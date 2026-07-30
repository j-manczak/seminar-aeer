"""Plant-level 2x2 Difference-in-Differences diagnostics.

This exploratory module estimates a local DiD for each reactor separately using
upstream stations as controls and downstream stations as treated units around the
reactor shutdown year. It is intentionally lightweight and independent from the
main staggered DiD workflow.

Outputs are written to:
- data/processed/analysis/plant_level_did/
- figures/plant_level_did/

Run:
    python scripts/plant_level_did.py
"""

from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

# Make the `pipeline` package importable when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline.config import ANALYSIS_DIR, PROJECT_ROOT
from pipeline.reactors import STUDY_REACTORS
from pipeline.river_position import FLOW

LOGGER = logging.getLogger("plant_level_did")

INPUT_FILE = ANALYSIS_DIR / "water_quality_summer_by_site.csv"
OUT_DIR = ANALYSIS_DIR / "plant_level_did"
FIG_DIR = PROJECT_ROOT / "figures" / "plant_level_did"

OUT_RESULTS = OUT_DIR / "plant_level_did_results.csv"
OUT_DISTANCE = OUT_DIR / "plant_level_did_distance_sensitivity.csv"
OUT_SUMMARY = OUT_DIR / "plant_level_did_summary.csv"
OUT_REPORT = OUT_DIR / "plant_level_did_report.md"

# Sensitivity thresholds for downstream exposure.
DISTANCE_THRESHOLDS_KM = [10.0, 25.0, 50.0, 75.0]
OUTCOMES = ["water_temperature", "dissolved_oxygen"]


@dataclass(frozen=True)
class ReactorSpec:
    """Reactor metadata needed for local panel construction."""

    reactor: str
    shutdown_year: int
    river: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class DidEstimate:
    """Container for one DiD estimate output row."""

    plant: str
    shutdown_year: int
    outcome: str
    model: str
    distance_threshold_km: str
    estimable: bool
    message: str
    upstream_pre_n: int
    upstream_post_n: int
    downstream_pre_n: int
    downstream_post_n: int
    coefficient: float | None
    standard_error: float | None
    ci_low: float | None
    ci_high: float | None
    p_value: float | None
    n_obs: int


def sanitize_name(text: str) -> str:
    """Return a filesystem-safe, lowercase name."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip())
    cleaned = cleaned.strip("_").lower()
    return cleaned or "plant"


def load_panel() -> pd.DataFrame:
    """Load the summer site-year panel and coerce required fields."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Required input not found: {INPUT_FILE}")

    panel = pd.read_csv(INPUT_FILE, comment="#")
    required = [
        "site_id",
        "study_river",
        "position",
        "nearest_upstream_plant",
        "determinand",
        "year",
        "mean_value",
        "latitude",
        "longitude",
        "along_river_km",
    ]
    missing = [col for col in required if col not in panel.columns]
    if missing:
        raise ValueError(f"Input panel is missing required columns: {missing}")

    panel["year"] = pd.to_numeric(panel["year"], errors="coerce")
    panel["mean_value"] = pd.to_numeric(panel["mean_value"], errors="coerce")
    panel["latitude"] = pd.to_numeric(panel["latitude"], errors="coerce")
    panel["longitude"] = pd.to_numeric(panel["longitude"], errors="coerce")
    panel["along_river_km"] = pd.to_numeric(panel["along_river_km"], errors="coerce")
    panel = panel.dropna(subset=["year", "mean_value", "latitude", "longitude"]).copy()
    panel["year"] = panel["year"].astype(int)

    return panel


def load_reactors() -> list[ReactorSpec]:
    """Map study reactors to a compact spec list."""
    reactors: list[ReactorSpec] = []
    for reactor in STUDY_REACTORS:
        reactors.append(
            ReactorSpec(
                reactor=reactor.reactor,
                shutdown_year=reactor.shutdown_year,
                river=reactor.river,
                latitude=reactor.latitude,
                longitude=reactor.longitude,
            )
        )
    return reactors


def signed_distance_from_reactor_km(df: pd.DataFrame, reactor: ReactorSpec) -> pd.Series:
    """Compute signed along-flow distance from a reactor to each row's site.

    Positive values indicate downstream, negative values indicate upstream.
    """
    if reactor.river not in FLOW:
        return pd.Series(np.nan, index=df.index)

    unit_east, unit_north = FLOW[reactor.river]
    km_per_deg_lat = 110.574
    km_per_deg_lon = 111.320

    east = (df["longitude"] - reactor.longitude) * km_per_deg_lon * np.cos(np.deg2rad(reactor.latitude))
    north = (df["latitude"] - reactor.latitude) * km_per_deg_lat
    return east * unit_east + north * unit_north


def build_local_dataset(
    panel: pd.DataFrame,
    reactor: ReactorSpec,
    outcome: str,
    downstream_max_km: float | None = None,
) -> pd.DataFrame:
    """Create a local 2x2-ready panel for one plant and one outcome.

    Treated rows are downstream stations whose nearest upstream plant is the
    focal reactor. Control rows are stations upstream of the focal reactor
    according to the signed along-flow distance on the same study river.
    """
    local = panel[(panel["determinand"] == outcome) & (panel["study_river"] == reactor.river)].copy()
    if local.empty:
        return local

    local["signed_distance_km"] = signed_distance_from_reactor_km(local, reactor)

    treated_mask = (local["position"] == "downstream") & (local["nearest_upstream_plant"] == reactor.reactor)
    if downstream_max_km is not None:
        treated_mask = treated_mask & local["along_river_km"].le(downstream_max_km)

    control_mask = local["signed_distance_km"].lt(0)

    local = local[treated_mask | control_mask].copy()
    if local.empty:
        return local

    local["treatment"] = np.where(treated_mask.loc[local.index], 1, 0)

    # Strict before/after coding for a 2x2 design around shutdown.
    local = local[local["year"] != reactor.shutdown_year].copy()
    local["post"] = np.where(local["year"] > reactor.shutdown_year, 1, 0)
    local["did"] = local["treatment"] * local["post"]

    return local


def count_design_cells(local: pd.DataFrame) -> dict[str, int]:
    """Count observations in the four 2x2 design cells."""
    if local.empty:
        return {
            "upstream_pre_n": 0,
            "upstream_post_n": 0,
            "downstream_pre_n": 0,
            "downstream_post_n": 0,
        }

    counts = (
        local.groupby(["treatment", "post"]).size().reindex(pd.MultiIndex.from_product([[0, 1], [0, 1]])).fillna(0).astype(int)
    )
    return {
        "upstream_pre_n": int(counts.loc[(0, 0)]),
        "upstream_post_n": int(counts.loc[(0, 1)]),
        "downstream_pre_n": int(counts.loc[(1, 0)]),
        "downstream_post_n": int(counts.loc[(1, 1)]),
    }


def can_estimate_2x2(cell_counts: dict[str, int]) -> tuple[bool, str]:
    """Validate whether all required 2x2 cells are non-empty."""
    required = [
        cell_counts["upstream_pre_n"],
        cell_counts["upstream_post_n"],
        cell_counts["downstream_pre_n"],
        cell_counts["downstream_post_n"],
    ]
    if any(value == 0 for value in required):
        return False, "2x2 DiD cannot be estimated because one required cell contains zero observations."
    return True, ""


def _extract_estimate(
    fitted,
    coefficient_name: str,
) -> tuple[float | None, float | None, float | None, float | None, float | None]:
    """Safely extract coefficient statistics from a fitted statsmodels result."""
    if coefficient_name not in fitted.params:
        return None, None, None, None, None

    coef = float(fitted.params[coefficient_name])
    se = float(fitted.bse[coefficient_name])
    pval = float(fitted.pvalues[coefficient_name])
    ci_low, ci_high = fitted.conf_int().loc[coefficient_name]
    return coef, se, float(ci_low), float(ci_high), pval


def fit_base_did(local: pd.DataFrame) -> tuple[float | None, float | None, float | None, float | None, float | None]:
    """Fit a simple 2x2 DiD model with treatment, post, and interaction."""
    if local.empty:
        return None, None, None, None, None

    model = smf.ols("mean_value ~ treatment + post + treatment:post", data=local)
    if local["site_id"].nunique() > 1:
        fitted = model.fit(cov_type="cluster", cov_kwds={"groups": local["site_id"]})
    else:
        fitted = model.fit(cov_type="HC1")
    return _extract_estimate(fitted, "treatment:post")


def fit_twfe_did(local: pd.DataFrame) -> tuple[float | None, float | None, float | None, float | None, float | None, str]:
    """Fit a TWFE DiD model if the sample has enough variation."""
    if local.empty:
        return None, None, None, None, None, ""

    if local["site_id"].nunique() < 2 or local["year"].nunique() < 2:
        return None, None, None, None, None, "TWFE skipped: insufficient site/year variation."

    try:
        model = smf.ols("mean_value ~ did + C(site_id) + C(year)", data=local)
        if local["site_id"].nunique() > 1:
            fitted = model.fit(cov_type="cluster", cov_kwds={"groups": local["site_id"]})
        else:
            fitted = model.fit(cov_type="HC1")
        coef, se, ci_low, ci_high, pval = _extract_estimate(fitted, "did")
        return coef, se, ci_low, ci_high, pval, ""
    except Exception as exc:  # noqa: BLE001 - keep module robust across sparse designs.
        return None, None, None, None, None, f"TWFE skipped: {exc}"


def estimate_models(
    plant: ReactorSpec,
    outcome: str,
    local: pd.DataFrame,
    distance_threshold_km: float | None,
) -> list[DidEstimate]:
    """Run all requested model variants for a local plant-outcome panel."""
    cell_counts = count_design_cells(local)
    estimable, message = can_estimate_2x2(cell_counts)

    threshold_label = "all" if distance_threshold_km is None else f"<= {distance_threshold_km:.0f}"
    rows: list[DidEstimate] = []

    if not estimable:
        LOGGER.warning("%s | %s | %s", plant.reactor, outcome, message)
        rows.append(
            DidEstimate(
                plant=plant.reactor,
                shutdown_year=plant.shutdown_year,
                outcome=outcome,
                model="simple_did",
                distance_threshold_km=threshold_label,
                estimable=False,
                message=message,
                upstream_pre_n=cell_counts["upstream_pre_n"],
                upstream_post_n=cell_counts["upstream_post_n"],
                downstream_pre_n=cell_counts["downstream_pre_n"],
                downstream_post_n=cell_counts["downstream_post_n"],
                coefficient=None,
                standard_error=None,
                ci_low=None,
                ci_high=None,
                p_value=None,
                n_obs=int(len(local)),
            )
        )
        rows.append(
            DidEstimate(
                plant=plant.reactor,
                shutdown_year=plant.shutdown_year,
                outcome=outcome,
                model="twfe_did",
                distance_threshold_km=threshold_label,
                estimable=False,
                message=message,
                upstream_pre_n=cell_counts["upstream_pre_n"],
                upstream_post_n=cell_counts["upstream_post_n"],
                downstream_pre_n=cell_counts["downstream_pre_n"],
                downstream_post_n=cell_counts["downstream_post_n"],
                coefficient=None,
                standard_error=None,
                ci_low=None,
                ci_high=None,
                p_value=None,
                n_obs=int(len(local)),
            )
        )
        return rows

    coef, se, ci_low, ci_high, pval = fit_base_did(local)
    rows.append(
        DidEstimate(
            plant=plant.reactor,
            shutdown_year=plant.shutdown_year,
            outcome=outcome,
            model="simple_did",
            distance_threshold_km=threshold_label,
            estimable=True,
            message="",
            upstream_pre_n=cell_counts["upstream_pre_n"],
            upstream_post_n=cell_counts["upstream_post_n"],
            downstream_pre_n=cell_counts["downstream_pre_n"],
            downstream_post_n=cell_counts["downstream_post_n"],
            coefficient=coef,
            standard_error=se,
            ci_low=ci_low,
            ci_high=ci_high,
            p_value=pval,
            n_obs=int(len(local)),
        )
    )

    twfe_coef, twfe_se, twfe_ci_low, twfe_ci_high, twfe_p, twfe_msg = fit_twfe_did(local)
    rows.append(
        DidEstimate(
            plant=plant.reactor,
            shutdown_year=plant.shutdown_year,
            outcome=outcome,
            model="twfe_did",
            distance_threshold_km=threshold_label,
            estimable=twfe_coef is not None,
            message=twfe_msg,
            upstream_pre_n=cell_counts["upstream_pre_n"],
            upstream_post_n=cell_counts["upstream_post_n"],
            downstream_pre_n=cell_counts["downstream_pre_n"],
            downstream_post_n=cell_counts["downstream_post_n"],
            coefficient=twfe_coef,
            standard_error=twfe_se,
            ci_low=twfe_ci_low,
            ci_high=twfe_ci_high,
            p_value=twfe_p,
            n_obs=int(len(local)),
        )
    )

    return rows


def _group_label(treatment: int) -> str:
    return "Downstream" if treatment == 1 else "Upstream"


def plot_time_series(local: pd.DataFrame, plant: ReactorSpec, path: Path) -> None:
    """Plot upstream/downstream annual means with approximate 95% CIs."""
    if local.empty:
        return

    grouped = (
        local.groupby(["year", "treatment"])["mean_value"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    grouped["se"] = grouped["std"] / np.sqrt(grouped["count"].clip(lower=1))
    grouped["ci_low"] = grouped["mean"] - 1.96 * grouped["se"]
    grouped["ci_high"] = grouped["mean"] + 1.96 * grouped["se"]

    fig, ax = plt.subplots(figsize=(8.5, 4.6), dpi=170)
    colors = {0: "#2a78d6", 1: "#e34948"}

    for treatment in [0, 1]:
        part = grouped[grouped["treatment"] == treatment]
        if part.empty:
            continue
        ax.plot(part["year"], part["mean"], marker="o", lw=2, color=colors[treatment], label=_group_label(treatment))
        if part["count"].max() > 1:
            ax.fill_between(part["year"], part["ci_low"], part["ci_high"], color=colors[treatment], alpha=0.2)

    ax.axvline(plant.shutdown_year, color="#4a4a4a", linestyle="--", lw=1.3, label=f"Shutdown ({plant.shutdown_year})")
    ax.set_title(f"{plant.reactor}: Summer Mean by Upstream vs Downstream")
    ax.set_xlabel("Year")
    ax.set_ylabel("Water temperature (deg C)")
    ax.grid(axis="y", color="#dddddd", lw=0.7)
    ax.legend(frameon=False)

    fig.tight_layout()
    fig.savefig(path, dpi=170, facecolor="white")
    plt.close(fig)


def plot_did_2x2(local: pd.DataFrame, plant: ReactorSpec, path: Path) -> None:
    """Plot the 2x2 cell means and show implied DiD contrast."""
    if local.empty:
        return

    cells = (
        local.groupby(["treatment", "post"])["mean_value"]
        .mean()
        .reindex(pd.MultiIndex.from_product([[0, 1], [0, 1]]))
    )

    labels = ["Upstream\nPre", "Upstream\nPost", "Downstream\nPre", "Downstream\nPost"]
    values = [cells.loc[(0, 0)], cells.loc[(0, 1)], cells.loc[(1, 0)], cells.loc[(1, 1)]]

    fig, ax = plt.subplots(figsize=(7.6, 4.4), dpi=170)
    ax.bar(labels, values, color=["#6ea8e0", "#2a78d6", "#f59a9a", "#e34948"])

    if all(pd.notna(values)):
        did_effect = (values[3] - values[2]) - (values[1] - values[0])
        ax.text(0.01, 0.98, f"Implied DiD = {did_effect:+.3f}", transform=ax.transAxes, ha="left", va="top")

    ax.set_title(f"{plant.reactor}: 2x2 Mean Summary")
    ax.set_ylabel("Water temperature (deg C)")
    ax.grid(axis="y", color="#dddddd", lw=0.7)

    fig.tight_layout()
    fig.savefig(path, dpi=170, facecolor="white")
    plt.close(fig)


def plot_coverage(local: pd.DataFrame, plant: ReactorSpec, path: Path) -> None:
    """Plot annual observation coverage for upstream vs downstream groups."""
    if local.empty:
        return

    counts = (
        local.groupby(["year", "treatment"]).size().unstack("treatment").fillna(0).astype(int)
    )

    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=170)
    for treatment, color in [(0, "#2a78d6"), (1, "#e34948")]:
        if treatment in counts:
            ax.plot(counts.index, counts[treatment], marker="o", lw=2, color=color, label=_group_label(treatment))

    ax.axvline(plant.shutdown_year, color="#4a4a4a", linestyle="--", lw=1.3)
    ax.set_title(f"{plant.reactor}: Observation Coverage by Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of observations")
    ax.grid(axis="y", color="#dddddd", lw=0.7)
    ax.legend(frameon=False)

    fig.tight_layout()
    fig.savefig(path, dpi=170, facecolor="white")
    plt.close(fig)


def make_temperature_figures(plant: ReactorSpec, local_temp: pd.DataFrame) -> dict[str, str]:
    """Generate all requested temperature visualizations for one plant."""
    slug = sanitize_name(plant.reactor)
    paths = {
        "timeseries": FIG_DIR / f"{slug}_timeseries.png",
        "did_2x2": FIG_DIR / f"{slug}_did_2x2.png",
        "coverage": FIG_DIR / f"{slug}_coverage.png",
    }

    plot_time_series(local_temp, plant, paths["timeseries"])
    plot_did_2x2(local_temp, plant, paths["did_2x2"])
    plot_coverage(local_temp, plant, paths["coverage"])

    return {name: str(path.relative_to(PROJECT_ROOT)) for name, path in paths.items() if path.exists()}


def rows_to_frame(rows: Iterable[DidEstimate]) -> pd.DataFrame:
    """Convert dataclass estimate rows to a flat DataFrame."""
    return pd.DataFrame([row.__dict__ for row in rows])


def build_summary_table(
    results: pd.DataFrame,
    station_counts: dict[str, dict[str, int]],
) -> pd.DataFrame:
    """Build one-row-per-plant summary as requested."""
    temp_simple = results[
        (results["outcome"] == "water_temperature")
        & (results["model"] == "simple_did")
        & (results["distance_threshold_km"] == "all")
    ].copy()

    summary = temp_simple[
        [
            "plant",
            "shutdown_year",
            "estimable",
            "coefficient",
            "n_obs",
            "upstream_pre_n",
            "upstream_post_n",
            "downstream_pre_n",
            "downstream_post_n",
        ]
    ].rename(
        columns={
            "plant": "Plant",
            "shutdown_year": "Shutdown",
            "estimable": "DiD estimable",
            "coefficient": "beta",
            "n_obs": "N",
        }
    )

    summary["Upstream stations"] = summary["Plant"].map(
        lambda plant: station_counts.get(str(plant), {}).get("upstream", 0)
    )
    summary["Downstream stations"] = summary["Plant"].map(
        lambda plant: station_counts.get(str(plant), {}).get("downstream", 0)
    )
    return summary[
        [
            "Plant",
            "Shutdown",
            "Upstream stations",
            "Downstream stations",
            "DiD estimable",
            "beta",
            "N",
            "upstream_pre_n",
            "upstream_post_n",
            "downstream_pre_n",
            "downstream_post_n",
        ]
    ]


def build_distance_summary(results: pd.DataFrame) -> pd.DataFrame:
    """Build distance sensitivity summary table for simple temperature DiD."""
    dist = results[
        (results["outcome"] == "water_temperature")
        & (results["model"] == "simple_did")
        & (results["distance_threshold_km"] != "all")
    ].copy()

    return dist[
        [
            "plant",
            "distance_threshold_km",
            "coefficient",
            "standard_error",
            "p_value",
            "n_obs",
            "estimable",
            "message",
        ]
    ].rename(
        columns={
            "plant": "Plant",
            "distance_threshold_km": "Distance",
            "coefficient": "beta",
            "standard_error": "SE",
            "p_value": "p-value",
            "n_obs": "N",
        }
    )


def write_report(
    reactors: list[ReactorSpec],
    results: pd.DataFrame,
    figure_map: dict[str, dict[str, str]],
    summary: pd.DataFrame,
    distance_summary: pd.DataFrame,
) -> None:
    """Write a Markdown narrative report with per-plant diagnostics."""
    lines: list[str] = [
        "# Plant-Level 2x2 Difference-in-Differences Review",
        "",
        "This report summarizes exploratory per-plant 2x2 DiD diagnostics using",
        "upstream stations as control and downstream stations as treated units.",
        "",
        "## Plant Summary",
        "",
        summary.to_markdown(index=False),
        "",
        "## Distance Sensitivity (Temperature, Simple DiD)",
        "",
        distance_summary.to_markdown(index=False) if not distance_summary.empty else "No distance-sensitivity rows available.",
        "",
        "## Per-Plant Notes",
        "",
    ]

    for plant in reactors:
        lines.append(f"### {plant.reactor} (shutdown {plant.shutdown_year})")
        lines.append("")

        plant_rows = results[
            (results["plant"] == plant.reactor)
            & (results["distance_threshold_km"] == "all")
            & (results["model"].isin(["simple_did", "twfe_did"]))
        ].copy()

        if plant_rows.empty:
            lines.append("No estimations were produced for this plant.")
            lines.append("")
            continue

        temp_row = plant_rows[(plant_rows["outcome"] == "water_temperature") & (plant_rows["model"] == "simple_did")]
        if not temp_row.empty:
            row = temp_row.iloc[0]
            lines.append(
                "2x2 cells (temperature): "
                f"upstream-pre={int(row['upstream_pre_n'])}, "
                f"upstream-post={int(row['upstream_post_n'])}, "
                f"downstream-pre={int(row['downstream_pre_n'])}, "
                f"downstream-post={int(row['downstream_post_n'])}."
            )
            if not bool(row["estimable"]):
                lines.append(str(row["message"]))

        lines.append("")
        lines.append(plant_rows[["outcome", "model", "estimable", "coefficient", "standard_error", "p_value", "n_obs", "message"]].to_markdown(index=False))
        lines.append("")

        figs = figure_map.get(plant.reactor, {})
        if figs:
            lines.append("Figures:")
            for _, rel in figs.items():
                lines.append(f"- {rel}")
            lines.append("")

    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def run() -> None:
    """Execute the full plant-level DiD workflow and export artifacts."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    panel = load_panel()
    reactors = load_reactors()

    all_rows: list[DidEstimate] = []
    figure_map: dict[str, dict[str, str]] = {}
    station_counts: dict[str, dict[str, int]] = {}

    for reactor in reactors:
        LOGGER.info("Processing %s", reactor.reactor)

        # Main estimates across all downstream distances.
        for outcome in OUTCOMES:
            local = build_local_dataset(panel, reactor, outcome, downstream_max_km=None)
            all_rows.extend(estimate_models(reactor, outcome, local, distance_threshold_km=None))

            if outcome == "water_temperature":
                station_counts[reactor.reactor] = {
                    "upstream": int(local.loc[local["treatment"] == 0, "site_id"].nunique()),
                    "downstream": int(local.loc[local["treatment"] == 1, "site_id"].nunique()),
                }

        # Per-plant visualization uses temperature local data.
        local_temp = build_local_dataset(panel, reactor, "water_temperature", downstream_max_km=None)
        figure_map[reactor.reactor] = make_temperature_figures(reactor, local_temp)

        # Distance-based sensitivity for temperature.
        for threshold in DISTANCE_THRESHOLDS_KM:
            local_threshold = build_local_dataset(panel, reactor, "water_temperature", downstream_max_km=threshold)
            all_rows.extend(
                estimate_models(
                    reactor,
                    "water_temperature",
                    local_threshold,
                    distance_threshold_km=threshold,
                )
            )

    results = rows_to_frame(all_rows)
    results.to_csv(OUT_RESULTS, index=False)

    summary = build_summary_table(results, station_counts)
    summary.to_csv(OUT_SUMMARY, index=False)

    distance_summary = build_distance_summary(results)
    distance_summary.to_csv(OUT_DISTANCE, index=False)

    write_report(reactors, results, figure_map, summary, distance_summary)

    print(f"Wrote {OUT_RESULTS.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {OUT_SUMMARY.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {OUT_DISTANCE.relative_to(PROJECT_ROOT)}")
    print(f"Wrote {OUT_REPORT.relative_to(PROJECT_ROOT)}")
    print(f"Figures in {FIG_DIR.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    run()
