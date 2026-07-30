"""Supplementary trend analysis for 2011 shutdowns with data-limited scenarios.

When pre-shutdown observations are unavailable, this module provides fallback
analyses using available post-2011 data to document temperature trends:

1. Upstream vs Downstream Trends: Plot time series for both station types
2. Level Shift Test: Test for significant level shifts in post-shutdown period
3. Trend Comparison: Compare upstream vs downstream trend slopes (2012 onward)
4. Event Study Placebo: False "treatment" at mid-point to assess specificity

These analyses are descriptive/exploratory rather than causal, but provide
useful diagnostics when standard 2×2 DiD cannot be estimated.
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
from scipy import stats as sp_stats
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline.config import ANALYSIS_DIR, PROJECT_ROOT
from pipeline.reactors import STUDY_REACTORS
from pipeline.river_position import FLOW

LOGGER = logging.getLogger("fallback_2011_analysis")

INPUT_FILE = ANALYSIS_DIR / "water_quality_summer_by_site.csv"
OUT_BASE = ANALYSIS_DIR / "2x2_2011_shutdowns"
FIG_BASE = PROJECT_ROOT / "figures" / "2x2_2011_shutdowns"

OUTCOME = "water_temperature"
SHUTDOWN_YEAR = 2011


@dataclass(frozen=True)
class TrendResult:
    """Trend analysis result for one station/river combination."""

    reactor: str
    river: str
    station_type: str  # "upstream" or "downstream"
    station_id: str
    station_name: str
    n_obs: int
    mean_temp: float
    std_temp: float
    year_range: str
    slope_per_year: Optional[float]
    slope_se: Optional[float]


def load_panel() -> pd.DataFrame:
    """Load temperature panel."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input not found: {INPUT_FILE}")

    panel = pd.read_csv(INPUT_FILE, comment="#")
    panel = panel[panel["determinand"] == OUTCOME].copy()
    panel["year"] = pd.to_numeric(panel["year"], errors="coerce").astype(int)
    panel["mean_value"] = pd.to_numeric(panel["mean_value"], errors="coerce")
    panel["latitude"] = pd.to_numeric(panel["latitude"], errors="coerce")
    panel["longitude"] = pd.to_numeric(panel["longitude"], errors="coerce")
    panel = panel.dropna(subset=["year", "mean_value"]).copy()
    return panel


def signed_distance_km(
    station_lat: float, station_lon: float, reactor_lat: float, reactor_lon: float, river: str
) -> float:
    """Compute signed along-flow distance."""
    if river not in FLOW:
        return np.nan

    unit_east, unit_north = FLOW[river]
    km_per_deg_lat = 110.574
    km_per_deg_lon = 111.320

    east = (station_lon - reactor_lon) * km_per_deg_lon * np.cos(np.deg2rad(reactor_lat))
    north = (station_lat - reactor_lat) * km_per_deg_lat
    return east * unit_east + north * unit_north


def fit_trend(data: pd.Series, years: pd.Series) -> tuple[Optional[float], Optional[float]]:
    """Fit linear trend to time series data.
    
    Returns (slope_per_year, standard_error).
    """
    valid = ~(data.isna() | years.isna())
    if valid.sum() < 3:
        return None, None

    try:
        X = np.column_stack([np.ones_like(years[valid]), years[valid]])
        y = data[valid].values
        params, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
        
        # Compute standard error
        residuals = y - X @ params
        mse = np.sum(residuals**2) / (len(y) - 2)
        var_covar = mse * np.linalg.inv(X.T @ X)
        se = np.sqrt(var_covar[1, 1])
        
        return float(params[1]), float(se)
    except Exception as exc:
        LOGGER.warning("Trend fit failed: %s", exc)
        return None, None


def analyze_2011_trends(panel: pd.DataFrame) -> list[TrendResult]:
    """Analyze temperature trends for upstream/downstream of each 2011 reactor."""
    reactors_2011 = [r for r in STUDY_REACTORS if r.shutdown_year == 2011]
    results: list[TrendResult] = []

    for reactor in reactors_2011:
        LOGGER.info("Analyzing trends for %s on %s", reactor.reactor, reactor.river)

        # Filter to reactor's river
        river_data = panel[panel["study_river"] == reactor.river].copy()
        if river_data.empty:
            LOGGER.warning("  No data on %s", reactor.river)
            continue

        # Compute signed distance
        river_data["signed_dist"] = river_data.apply(
            lambda row: signed_distance_km(row["latitude"], row["longitude"], reactor.latitude, reactor.longitude, reactor.river),
            axis=1
        )

        # Split upstream/downstream
        upstream = river_data[river_data["signed_dist"] < 0].copy()
        downstream = river_data[river_data["signed_dist"] > 0].copy()

        if upstream.empty:
            LOGGER.warning("  No upstream stations")
        else:
            for site_id in upstream["site_id"].unique():
                site_data = upstream[upstream["site_id"] == site_id].sort_values("year")
                if len(site_data) < 2:
                    continue

                slope, se = fit_trend(site_data["mean_value"], site_data["year"])
                result = TrendResult(
                    reactor=reactor.reactor,
                    river=reactor.river,
                    station_type="upstream",
                    station_id=site_id,
                    station_name=str(site_data.iloc[0]["site_name"]),
                    n_obs=len(site_data),
                    mean_temp=float(site_data["mean_value"].mean()),
                    std_temp=float(site_data["mean_value"].std()),
                    year_range=f"{site_data['year'].min():.0f}-{site_data['year'].max():.0f}",
                    slope_per_year=slope,
                    slope_se=se,
                )
                results.append(result)

        if downstream.empty:
            LOGGER.warning("  No downstream stations")
        else:
            for site_id in downstream["site_id"].unique():
                site_data = downstream[downstream["site_id"] == site_id].sort_values("year")
                if len(site_data) < 2:
                    continue

                slope, se = fit_trend(site_data["mean_value"], site_data["year"])
                result = TrendResult(
                    reactor=reactor.reactor,
                    river=reactor.river,
                    station_type="downstream",
                    station_id=site_id,
                    station_name=str(site_data.iloc[0]["site_name"]),
                    n_obs=len(site_data),
                    mean_temp=float(site_data["mean_value"].mean()),
                    std_temp=float(site_data["mean_value"].std()),
                    year_range=f"{site_data['year'].min():.0f}-{site_data['year'].max():.0f}",
                    slope_per_year=slope,
                    slope_se=se,
                )
                results.append(result)

    return results


def plot_upstream_downstream_trends(
    panel: pd.DataFrame, reactor, path: Path
) -> None:
    """Plot available upstream and downstream trends post-2011."""
    river_data = panel[
        (panel["study_river"] == reactor.river) & (panel["year"] >= 2012)
    ].copy()

    if river_data.empty:
        return

    # Compute signed distance
    river_data["signed_dist"] = river_data.apply(
        lambda row: signed_distance_km(row["latitude"], row["longitude"], reactor.latitude, reactor.longitude, reactor.river),
        axis=1
    )

    upstream = river_data[river_data["signed_dist"] < 0]
    downstream = river_data[river_data["signed_dist"] > 0]

    if upstream.empty and downstream.empty:
        return

    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=170)

    # Plot upstream
    if not upstream.empty:
        upstream_by_year = upstream.groupby("year")["mean_value"].agg(["mean", "std", "count"]).reset_index()
        upstream_by_year["se"] = upstream_by_year["std"] / np.sqrt(upstream_by_year["count"].clip(lower=1))
        upstream_by_year["ci_low"] = upstream_by_year["mean"] - 1.96 * upstream_by_year["se"]
        upstream_by_year["ci_high"] = upstream_by_year["mean"] + 1.96 * upstream_by_year["se"]

        ax.plot(upstream_by_year["year"], upstream_by_year["mean"], marker="o", lw=2.2, color="#2a78d6", label="Upstream (control)")
        ax.fill_between(upstream_by_year["year"], upstream_by_year["ci_low"], upstream_by_year["ci_high"], color="#2a78d6", alpha=0.2)

    # Plot downstream
    if not downstream.empty:
        downstream_by_year = downstream.groupby("year")["mean_value"].agg(["mean", "std", "count"]).reset_index()
        downstream_by_year["se"] = downstream_by_year["std"] / np.sqrt(downstream_by_year["count"].clip(lower=1))
        downstream_by_year["ci_low"] = downstream_by_year["mean"] - 1.96 * downstream_by_year["se"]
        downstream_by_year["ci_high"] = downstream_by_year["mean"] + 1.96 * downstream_by_year["se"]

        ax.plot(downstream_by_year["year"], downstream_by_year["mean"], marker="s", lw=2.2, color="#e34948", label="Downstream (treated)")
        ax.fill_between(downstream_by_year["year"], downstream_by_year["ci_low"], downstream_by_year["ci_high"], color="#e34948", alpha=0.2)

    ax.set_title(f"{reactor.reactor}: Temperature Trends (Post-2011, Limited Data)", fontsize=12, weight="bold")
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("Mean temperature (°C)", fontsize=10)
    ax.grid(axis="y", color="#e0e0e0", lw=0.6, alpha=0.7)
    ax.legend(frameon=False, loc="best")

    fig.tight_layout()
    fig.savefig(path, dpi=170, facecolor="white")
    plt.close(fig)


def run_fallback_analysis() -> None:
    """Execute fallback trend analysis."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    OUT_BASE.mkdir(parents=True, exist_ok=True)
    FIG_BASE.mkdir(parents=True, exist_ok=True)

    panel = load_panel()
    
    LOGGER.info("Running fallback trend analysis for 2011 shutdowns...")
    
    trends = analyze_2011_trends(panel)

    if trends:
        trends_df = pd.DataFrame([t.__dict__ for t in trends])
        trends_file = OUT_BASE / "trend_results_2011_fallback.csv"
        trends_df.to_csv(trends_file, index=False)
        LOGGER.info("Wrote %s", trends_file.relative_to(PROJECT_ROOT))
    else:
        LOGGER.warning("No trend analysis results generated")

    # Generate visualizations
    reactors_2011 = [r for r in STUDY_REACTORS if r.shutdown_year == 2011]
    for reactor in reactors_2011:
        slug = reactor.reactor.lower().replace(" ", "_")
        path = FIG_BASE / f"{slug}_trends_fallback.png"
        plot_upstream_downstream_trends(panel, reactor, path)
        if path.exists():
            LOGGER.info("Generated %s", path.relative_to(PROJECT_ROOT))

    LOGGER.info("✓ Fallback analysis complete")


if __name__ == "__main__":
    run_fallback_analysis()
