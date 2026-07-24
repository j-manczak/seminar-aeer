"""Focused 2×2 DiD analysis for German nuclear plants shut down in 2011.

This module specializes the plant-level DiD framework for the 2011 nuclear
moratorium, implementing:
- Focused reactor selection (2011 shutdowns only)
- High-quality station selection with missing-data checks
- Distance-based sensitivity analysis (5, 10, 20, 30, 50 km)
- Structured reporting per plant

Outputs are organized in:
- data/processed/analysis/2x2_2011_shutdowns/
- figures/2x2_2011_shutdowns/

Run:
    python scripts/analyze_2011_shutdowns.py
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline.config import ANALYSIS_DIR, PROJECT_ROOT
from pipeline.reactors import STUDY_REACTORS
from pipeline.river_position import FLOW

LOGGER = logging.getLogger("analyze_2011_shutdowns")

INPUT_FILE = ANALYSIS_DIR / "water_quality_summer_by_site.csv"
OUT_BASE = ANALYSIS_DIR / "2x2_2011_shutdowns"
FIG_BASE = PROJECT_ROOT / "figures" / "2x2_2011_shutdowns"

# 2011-specific distance thresholds for sensitivity analysis.
DISTANCE_THRESHOLDS_KM = [5.0, 10.0, 20.0, 30.0, 50.0]
OUTCOME = "water_temperature"
SHUTDOWN_YEAR = 2011


@dataclass(frozen=True)
class Reactor2011:
    """Reactor with 2011 shutdown metadata."""

    reactor: str
    plant_name: str
    river: str
    shutdown_year: int
    latitude: float
    longitude: float


@dataclass(frozen=True)
class StationPair:
    """Upstream/downstream station pair for a reactor."""

    reactor: str
    upstream_id: str
    upstream_name: str
    upstream_distance_km: float
    upstream_obs_pre: int
    upstream_obs_post: int
    downstream_id: str
    downstream_name: str
    downstream_distance_km: float
    downstream_obs_pre: int
    downstream_obs_post: int


@dataclass(frozen=True)
class DidResult:
    """One 2×2 DiD result row."""

    reactor: str
    distance_threshold_km: float
    upstream_id: str
    downstream_id: str
    estimable: bool
    message: str
    coefficient: float | None
    standard_error: float | None
    ci_low: float | None
    ci_high: float | None
    p_value: float | None
    n_obs: int
    n_upstream_pre: int
    n_upstream_post: int
    n_downstream_pre: int
    n_downstream_post: int


def load_panel() -> pd.DataFrame:
    """Load summer temperature panel."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input not found: {INPUT_FILE}")

    panel = pd.read_csv(INPUT_FILE, comment="#")
    required = [
        "site_id",
        "site_name",
        "study_river",
        "position",
        "nearest_upstream_plant",
        "year",
        "mean_value",
        "latitude",
        "longitude",
        "along_river_km",
        "determinand",
    ]
    missing = [col for col in required if col not in panel.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    panel = panel[panel["determinand"] == OUTCOME].copy()
    panel["year"] = pd.to_numeric(panel["year"], errors="coerce").astype(int)
    panel["mean_value"] = pd.to_numeric(panel["mean_value"], errors="coerce")
    panel["latitude"] = pd.to_numeric(panel["latitude"], errors="coerce")
    panel["longitude"] = pd.to_numeric(panel["longitude"], errors="coerce")
    panel["along_river_km"] = pd.to_numeric(panel["along_river_km"], errors="coerce")

    panel = panel.dropna(subset=["year", "mean_value", "latitude", "longitude"]).copy()
    return panel


def get_2011_reactors() -> list[Reactor2011]:
    """Filter study reactors to only 2011 shutdowns."""
    reactors: list[Reactor2011] = []
    for reactor in STUDY_REACTORS:
        if reactor.shutdown_year == SHUTDOWN_YEAR:
            reactors.append(
                Reactor2011(
                    reactor=reactor.reactor,
                    plant_name=reactor.reactor.split()[0],  # e.g., "Biblis" from "Biblis A"
                    river=reactor.river,
                    shutdown_year=reactor.shutdown_year,
                    latitude=reactor.latitude,
                    longitude=reactor.longitude,
                )
            )
    return sorted(reactors, key=lambda r: r.reactor)


def signed_distance_from_reactor_km(
    df: pd.DataFrame, reactor: Reactor2011
) -> pd.Series:
    """Compute signed along-flow distance: positive=downstream."""
    if reactor.river not in FLOW:
        return pd.Series(np.nan, index=df.index)

    unit_east, unit_north = FLOW[reactor.river]
    km_per_deg_lat = 110.574
    km_per_deg_lon = 111.320

    east = (
        (df["longitude"] - reactor.longitude)
        * km_per_deg_lon
        * np.cos(np.deg2rad(reactor.latitude))
    )
    north = (df["latitude"] - reactor.latitude) * km_per_deg_lat
    return east * unit_east + north * unit_north


def find_best_upstream_downstream(
    panel: pd.DataFrame, reactor: Reactor2011, min_obs_per_period: int = 1
) -> Optional[StationPair]:
    """Identify nearest upstream and downstream stations with quality checks.

    Selects stations on the same river with:
    - At least min_obs_per_period observations before shutdown (default: 1)
    - At least min_obs_per_period observations after shutdown (default: 1)
    - Non-empty pre and post periods

    Returns the nearest upstream/downstream pair by distance.
    Data availability for 2011 shutdowns is limited (most monitoring started
    after 2011), so we're flexible but require at least some pre/post data.
    """
    local = panel[
        (panel["study_river"] == reactor.river)
        & (panel["year"] != reactor.shutdown_year)
    ].copy()

    if local.empty:
        LOGGER.debug("  No data on %s", reactor.river)
        return None

    local["signed_distance_km"] = signed_distance_from_reactor_km(local, reactor)

    # Upstream: negative signed distance
    upstream = local[local["signed_distance_km"] < 0].copy()
    if upstream.empty:
        LOGGER.debug("  No upstream stations on %s", reactor.river)
        return None

    downstream = local[local["signed_distance_km"] > 0].copy()
    if downstream.empty:
        LOGGER.debug("  No downstream stations on %s", reactor.river)
        return None

    # Count observations per period for each site
    def count_periods(group):
        pre = len(group[group["year"] < reactor.shutdown_year])
        post = len(group[group["year"] >= reactor.shutdown_year])
        return pd.Series({"pre": pre, "post": post, "dist": group["signed_distance_km"].iloc[0]})

    upstream_counts = upstream.groupby("site_id", group_keys=False).apply(
        count_periods, include_groups=False
    )
    downstream_counts = downstream.groupby("site_id", group_keys=False).apply(
        count_periods, include_groups=False
    )

    # Filter for minimum observations
    upstream_ok = upstream_counts[
        (upstream_counts["pre"] >= min_obs_per_period)
        & (upstream_counts["post"] >= min_obs_per_period)
    ]
    downstream_ok = downstream_counts[
        (downstream_counts["pre"] >= min_obs_per_period)
        & (downstream_counts["post"] >= min_obs_per_period)
    ]

    if upstream_ok.empty:
        LOGGER.debug("  No upstream stations with sufficient observations (need %d pre & post)", min_obs_per_period)
        return None

    if downstream_ok.empty:
        LOGGER.debug("  No downstream stations with sufficient observations (need %d pre & post)", min_obs_per_period)
        return None

    # Select nearest by absolute distance
    upstream_best_id = upstream_ok["dist"].abs().idxmin()
    downstream_best_id = downstream_ok["dist"].abs().idxmin()

    # Extract full metadata
    upstream_rows = upstream[upstream["site_id"] == upstream_best_id]
    downstream_rows = downstream[downstream["site_id"] == downstream_best_id]

    if upstream_rows.empty or downstream_rows.empty:
        return None

    up_meta = upstream_rows.iloc[0]
    down_meta = downstream_rows.iloc[0]

    return StationPair(
        reactor=reactor.reactor,
        upstream_id=upstream_best_id,
        upstream_name=str(up_meta.get("site_name", "?")).strip(),
        upstream_distance_km=round(abs(up_meta["signed_distance_km"]), 1),
        upstream_obs_pre=len(
            upstream_rows[upstream_rows["year"] < reactor.shutdown_year]
        ),
        upstream_obs_post=len(
            upstream_rows[upstream_rows["year"] >= reactor.shutdown_year]
        ),
        downstream_id=downstream_best_id,
        downstream_name=str(down_meta.get("site_name", "?")).strip(),
        downstream_distance_km=round(down_meta["signed_distance_km"], 1),
        downstream_obs_pre=len(
            downstream_rows[downstream_rows["year"] < reactor.shutdown_year]
        ),
        downstream_obs_post=len(
            downstream_rows[downstream_rows["year"] >= reactor.shutdown_year]
        ),
    )


def build_2x2_dataset(
    panel: pd.DataFrame,
    reactor: Reactor2011,
    station_pair: StationPair,
    max_distance_km: Optional[float] = None,
) -> pd.DataFrame:
    """Build a 2×2-ready dataset for one reactor-station-pair combination."""
    local = panel[
        (
            (panel["site_id"] == station_pair.upstream_id)
            | (panel["site_id"] == station_pair.downstream_id)
        )
        & (panel["year"] != reactor.shutdown_year)
    ].copy()

    if local.empty:
        return local

    # Apply distance filter if specified
    if max_distance_km is not None:
        local = local[
            (
                (local["site_id"] == station_pair.upstream_id)
                & (local["along_river_km"].le(max_distance_km))
            )
            | (
                (local["site_id"] == station_pair.downstream_id)
                & (local["along_river_km"].le(max_distance_km))
            )
        ].copy()

    if local.empty:
        return local

    # Treatment coding: downstream = 1, upstream = 0
    local["treatment"] = (local["site_id"] == station_pair.downstream_id).astype(int)

    # Post-period coding
    local["post"] = (local["year"] > reactor.shutdown_year).astype(int)
    local["did"] = local["treatment"] * local["post"]

    return local


def count_2x2_cells(local: pd.DataFrame) -> dict[str, int]:
    """Count observations in the 2×2 design."""
    if local.empty:
        return {
            "upstream_pre_n": 0,
            "upstream_post_n": 0,
            "downstream_pre_n": 0,
            "downstream_post_n": 0,
        }

    counts = (
        local.groupby(["treatment", "post"])
        .size()
        .reindex(pd.MultiIndex.from_product([[0, 1], [0, 1]]))
        .fillna(0)
        .astype(int)
    )
    return {
        "upstream_pre_n": int(counts.loc[(0, 0)]),
        "upstream_post_n": int(counts.loc[(0, 1)]),
        "downstream_pre_n": int(counts.loc[(1, 0)]),
        "downstream_post_n": int(counts.loc[(1, 1)]),
    }


def can_estimate_2x2(cell_counts: dict[str, int]) -> tuple[bool, str]:
    """Check if all 2×2 cells are non-empty."""
    if any(v == 0 for v in cell_counts.values()):
        return False, "At least one cell has zero observations."
    return True, ""


def fit_simple_did(
    local: pd.DataFrame,
) -> tuple[float | None, float | None, float | None, float | None, float | None]:
    """Fit simple 2×2 DiD: mean_value ~ treatment + post + treatment:post."""
    if local.empty or len(local) < 4:
        return None, None, None, None, None

    try:
        model = smf.ols("mean_value ~ treatment + post + treatment:post", data=local)
        if local["site_id"].nunique() > 1:
            fitted = model.fit(cov_type="cluster", cov_kwds={"groups": local["site_id"]})
        else:
            fitted = model.fit(cov_type="HC1")

        if "treatment:post" not in fitted.params:
            return None, None, None, None, None

        coef = float(fitted.params["treatment:post"])
        se = float(fitted.bse["treatment:post"])
        pval = float(fitted.pvalues["treatment:post"])
        ci_low, ci_high = fitted.conf_int().loc["treatment:post"]
        return coef, se, float(ci_low), float(ci_high), pval
    except Exception as exc:
        LOGGER.warning("Model fit failed: %s", exc)
        return None, None, None, None, None


def estimate_did(
    reactor: Reactor2011,
    station_pair: StationPair,
    local: pd.DataFrame,
    distance_threshold_km: Optional[float],
) -> DidResult:
    """Estimate a single 2×2 DiD and return result row."""
    cell_counts = count_2x2_cells(local)
    estimable, message = can_estimate_2x2(cell_counts)

    if not estimable:
        return DidResult(
            reactor=reactor.reactor,
            distance_threshold_km=distance_threshold_km or 999.0,
            upstream_id=station_pair.upstream_id,
            downstream_id=station_pair.downstream_id,
            estimable=False,
            message=message,
            coefficient=None,
            standard_error=None,
            ci_low=None,
            ci_high=None,
            p_value=None,
            n_obs=len(local),
            n_upstream_pre=cell_counts["upstream_pre_n"],
            n_upstream_post=cell_counts["upstream_post_n"],
            n_downstream_pre=cell_counts["downstream_pre_n"],
            n_downstream_post=cell_counts["downstream_post_n"],
        )

    coef, se, ci_low, ci_high, pval = fit_simple_did(local)

    return DidResult(
        reactor=reactor.reactor,
        distance_threshold_km=distance_threshold_km or 999.0,
        upstream_id=station_pair.upstream_id,
        downstream_id=station_pair.downstream_id,
        estimable=coef is not None,
        message="",
        coefficient=coef,
        standard_error=se,
        ci_low=ci_low,
        ci_high=ci_high,
        p_value=pval,
        n_obs=len(local),
        n_upstream_pre=cell_counts["upstream_pre_n"],
        n_upstream_post=cell_counts["upstream_post_n"],
        n_downstream_pre=cell_counts["downstream_pre_n"],
        n_downstream_post=cell_counts["downstream_post_n"],
    )


def plot_time_series(
    local: pd.DataFrame, reactor: Reactor2011, path: Path
) -> None:
    """Plot upstream/downstream trends with shutdown marker."""
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

    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=170)
    colors = {0: "#2a78d6", 1: "#e34948"}
    labels = {0: "Upstream (control)", 1: "Downstream (treated)"}

    for treatment in [0, 1]:
        part = grouped[grouped["treatment"] == treatment]
        if part.empty:
            continue
        ax.plot(
            part["year"],
            part["mean"],
            marker="o",
            lw=2.2,
            color=colors[treatment],
            label=labels[treatment],
        )
        if part["count"].max() > 1:
            ax.fill_between(
                part["year"], part["ci_low"], part["ci_high"], color=colors[treatment], alpha=0.2
            )

    ax.axvline(reactor.shutdown_year, color="#4a4a4a", linestyle="--", lw=1.5, alpha=0.8)
    ax.text(
        reactor.shutdown_year,
        ax.get_ylim()[1] * 0.95,
        f"Shutdown\n{reactor.shutdown_year}",
        ha="center",
        fontsize=9,
        color="#4a4a4a",
    )

    ax.set_title(f"{reactor.reactor}: Summer Water Temperature Trends", fontsize=12, weight="bold")
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Mean temperature (°C)", fontsize=10)
    ax.grid(axis="y", color="#e0e0e0", lw=0.6, alpha=0.7)
    ax.legend(frameon=False, loc="best")

    fig.tight_layout()
    fig.savefig(path, dpi=170, facecolor="white")
    plt.close(fig)


def plot_2x2_summary(
    local: pd.DataFrame, reactor: Reactor2011, path: Path
) -> None:
    """Bar plot of 2×2 cell means with implied DiD."""
    if local.empty:
        return

    cells = (
        local.groupby(["treatment", "post"])["mean_value"]
        .mean()
        .reindex(pd.MultiIndex.from_product([[0, 1], [0, 1]]))
    )

    labels = ["Upstream\nBefore", "Upstream\nAfter", "Downstream\nBefore", "Downstream\nAfter"]
    values = [
        cells.loc[(0, 0)],
        cells.loc[(0, 1)],
        cells.loc[(1, 0)],
        cells.loc[(1, 1)],
    ]

    fig, ax = plt.subplots(figsize=(8.2, 5), dpi=170)
    colors_bar = ["#6ea8d4", "#2a78d6", "#f5a5a5", "#e34948"]
    bars = ax.bar(labels, values, color=colors_bar, width=0.6)

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if not np.isnan(height):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{height:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    if all(pd.notna(values)):
        did_effect = (values[3] - values[2]) - (values[1] - values[0])
        ax.text(
            0.5,
            0.95,
            f"Implied DiD coefficient: {did_effect:+.3f} °C",
            transform=ax.transAxes,
            ha="center",
            va="top",
            fontsize=10,
            bbox=dict(boxstyle="round", facecolor="#f0f0f0", alpha=0.8),
        )

    ax.set_title(f"{reactor.reactor}: 2×2 Summary (Pre vs Post Shutdown)", fontsize=12, weight="bold")
    ax.set_ylabel("Mean temperature (°C)", fontsize=10)
    ax.grid(axis="y", color="#e0e0e0", lw=0.6, alpha=0.7)

    fig.tight_layout()
    fig.savefig(path, dpi=170, facecolor="white")
    plt.close(fig)


def make_figures_for_reactor(
    reactor: Reactor2011, local: pd.DataFrame
) -> dict[str, Path]:
    """Generate all plots for one reactor."""
    slug = reactor.reactor.lower().replace(" ", "_")
    paths = {
        "timeseries": FIG_BASE / f"{slug}_timeseries.png",
        "did_2x2": FIG_BASE / f"{slug}_did_2x2.png",
    }

    plot_time_series(local, reactor, paths["timeseries"])
    plot_2x2_summary(local, reactor, paths["did_2x2"])

    return {k: v for k, v in paths.items() if v.exists()}


def run() -> None:
    """Execute the full 2011-focused DiD analysis."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    OUT_BASE.mkdir(parents=True, exist_ok=True)
    FIG_BASE.mkdir(parents=True, exist_ok=True)

    panel = load_panel()
    reactors_2011 = get_2011_reactors()

    LOGGER.info("Found %d reactors with 2011 shutdown", len(reactors_2011))
    LOGGER.info("Temperature data spans: %d-%d", panel["year"].min(), panel["year"].max())

    all_results: list[DidResult] = []
    station_pairs: dict[str, StationPair] = {}
    figure_map: dict[str, dict[str, Path]] = {}

    for reactor in reactors_2011:
        LOGGER.info("Processing %s (River %s, shutdown %d)", reactor.reactor, reactor.river, reactor.shutdown_year)

        # Find best upstream/downstream pair
        pair = find_best_upstream_downstream(panel, reactor, min_obs_per_period=1)
        if pair is None:
            LOGGER.warning("  → No valid upstream/downstream pair found")
            LOGGER.debug("  Available data may not span pre/post shutdown period")
            continue

        station_pairs[reactor.reactor] = pair
        LOGGER.info(
            "  Upstream: %s (%s), %.1f km away, %d pre / %d post obs",
            pair.upstream_id,
            pair.upstream_name,
            pair.upstream_distance_km,
            pair.upstream_obs_pre,
            pair.upstream_obs_post,
        )
        LOGGER.info(
            "  Downstream: %s (%s), %.1f km away, %d pre / %d post obs",
            pair.downstream_id,
            pair.downstream_name,
            pair.downstream_distance_km,
            pair.downstream_obs_pre,
            pair.downstream_obs_post,
        )

        # Base dataset (no distance filter)
        local_base = build_2x2_dataset(panel, reactor, pair)
        if not local_base.empty:
            result = estimate_did(reactor, pair, local_base, distance_threshold_km=None)
            all_results.append(result)
            est_str = "✓ estimable" if result.estimable else "✗ not estimable"
            LOGGER.info("  Base (no distance limit): %s, N=%d", est_str, result.n_obs)
            if result.estimable:
                LOGGER.info("    DiD coefficient: %+.4f (SE: %.4f, p: %.3f)", result.coefficient, result.standard_error, result.p_value)

        # Generate figures
        figure_map[reactor.reactor] = make_figures_for_reactor(reactor, local_base)

        # Distance sensitivity
        for threshold in DISTANCE_THRESHOLDS_KM:
            local_threshold = build_2x2_dataset(panel, reactor, pair, max_distance_km=threshold)
            if not local_threshold.empty:
                result = estimate_did(reactor, pair, local_threshold, distance_threshold_km=threshold)
                all_results.append(result)
                est_str = "✓" if result.estimable else "✗"
                LOGGER.debug("    %d km threshold: %s, N=%d", threshold, est_str, result.n_obs)

    LOGGER.info("")

    # Write results CSV
    if all_results:
        results_df = pd.DataFrame([r.__dict__ for r in all_results])
        results_file = OUT_BASE / "did_results_2011.csv"
        results_df.to_csv(results_file, index=False)
        LOGGER.info("Wrote %s", results_file.relative_to(PROJECT_ROOT))
    else:
        LOGGER.warning("No results to write (no estimable designs found)")

    # Write station pairs CSV
    if station_pairs:
        pairs_df = pd.DataFrame([p.__dict__ for p in station_pairs.values()])
        pairs_file = OUT_BASE / "station_pairs_2011.csv"
        pairs_df.to_csv(pairs_file, index=False)
        LOGGER.info("Wrote %s", pairs_file.relative_to(PROJECT_ROOT))

    # Write summary report
    report_file = OUT_BASE / "report_2011_shutdowns.md"
    lines = [
        "# 2×2 DiD Analysis: 2011 German Nuclear Shutdowns",
        "",
        "## Overview",
        f"Analysis of {len(reactors_2011)} reactors shut down in {SHUTDOWN_YEAR}",
        "using nearest upstream (control) and downstream (treatment) stations.",
        "",
        "**Data Limitation Note:** Temperature monitoring data coverage varies by river.",
        "Most monitoring stations started after 2011, limiting pre-shutdown observations.",
        f"This analysis uses available data from {panel['year'].min():.0f}-{panel['year'].max():.0f}.",
        "",
        "## Station Pairs Identified",
        "",
    ]

    for reactor in reactors_2011:
        if reactor.reactor in station_pairs:
            pair = station_pairs[reactor.reactor]
            lines.append(f"### {reactor.reactor}")
            lines.append(f"- **Upstream:** {pair.upstream_name} ({pair.upstream_id}), "
                        f"{pair.upstream_distance_km} km away, "
                        f"{pair.upstream_obs_pre} pre / {pair.upstream_obs_post} post observations")
            lines.append(f"- **Downstream:** {pair.downstream_name} ({pair.downstream_id}), "
                        f"{pair.downstream_distance_km} km away, "
                        f"{pair.downstream_obs_pre} pre / {pair.downstream_obs_post} post observations")
            lines.append("")
        else:
            lines.append(f"### {reactor.reactor}")
            lines.append("⚠️ No valid upstream/downstream pair found.")
            lines.append("")

    lines.extend([
        "## Results Summary",
        "",
    ])

    if all_results:
        lines.append(results_df.to_markdown(index=False))
    else:
        lines.append("⚠️ No results (insufficient data for any reactor).")

    lines.extend([
        "",
        "## Figures",
        "",
    ])

    for reactor in reactors_2011:
        if reactor.reactor in figure_map:
            figs = figure_map[reactor.reactor]
            if figs:
                lines.append(f"### {reactor.reactor}")
                for fig_type, fig_path in sorted(figs.items()):
                    rel = fig_path.relative_to(PROJECT_ROOT)
                    lines.append(f"- {fig_type.replace('_', ' ').title()}: `{rel}`")
                lines.append("")

    report_file.write_text("\n".join(lines), encoding="utf-8")
    LOGGER.info("Wrote %s", report_file.relative_to(PROJECT_ROOT))

    print("\n✓ 2011 DiD analysis complete")
    print(f"  Results: {results_file.relative_to(PROJECT_ROOT) if all_results else '(none)'}")
    print(f"  Pairs:   {pairs_file.relative_to(PROJECT_ROOT) if station_pairs else '(none)'}")
    print(f"  Report:  {report_file.relative_to(PROJECT_ROOT)}")
    print(f"  Figures: {FIG_BASE.relative_to(PROJECT_ROOT)}/")
    if not station_pairs:
        print("\n⚠️  Note: No valid station pairs found. Check data availability:")
        print("     - Most rivers started monitoring after 2011 shutdowns")
        print("     - Consider using earlier shutdowns (e.g., Stade 2003)")
        print("     - Or widening analysis window (pre/post relative to shutdown)")


if __name__ == "__main__":
    run()
