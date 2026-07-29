"""Per-site 2x2 difference-in-differences on upstream vs downstream river temperature.

Design
------
For one nuclear site and one shutdown year the 2x2 is

                     before shutdown        after shutdown
    upstream  (C)    mean T_up,before       mean T_up,after
    downstream(T)    mean T_down,before     mean T_down,after

and the estimate is the difference of the two differences. Because the two
gauges sit on the same river and are read on the same days, the sharper way to
write the same thing is the **paired daily difference**

    dT_t = T_downstream,t - T_upstream,t
    dT_t = a + b * post_t + month fixed effects + e_t

where ``b`` is numerically the DiD estimate but removes all common weather,
season and river-wide trend variation. That is the headline specification here;
the pooled two-station regression is reported next to it as a cross-check.

Daily river temperature is heavily autocorrelated, so standard errors are
Newey-West (HAC) with a 30-day bandwidth. The pooled specification clusters on
the gauge instead.

Robustness shipped with every estimate:
  * **distance sensitivity** - the effect is re-estimated against each available
    downstream gauge, so it can be plotted against along-river distance
  * **season split** - summer (Jun-Sep, low flow, warm water) vs the rest of the
    year, where a thermal plume should matter most
  * **placebo** - the same regression on a fake shutdown three years earlier

Run:
    python scripts/plant_2x2_did.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from pipeline import river_network, station_pairs
from pipeline.config import ANALYSIS_DIR, PROCESSED_DIR, PROJECT_ROOT

GKD_PANEL = PROCESSED_DIR / "gkd_water_temperature_daily.csv"
OUT_DIR = ANALYSIS_DIR / "plant_2x2"
FIG_DIR = PROJECT_ROOT / "figures" / "plant_2x2"

WINDOW_YEARS = 3          # years kept either side of the shutdown
HAC_LAGS = 30             # days; river temperature is strongly persistent
SUMMER_MONTHS = (6, 7, 8, 9)
PLACEBO_OFFSET_YEARS = 3
MAX_PAIR_KM = 120.0
MIN_DAYS_PER_CELL = 60    # a cell needs this many paired days to be reported


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def load_daily() -> pd.DataFrame:
    """Daily station temperature with each gauge placed on its river."""
    if not GKD_PANEL.exists():
        raise FileNotFoundError(
            f"{GKD_PANEL} not found - run scripts/pipeline/gkd_bayern.py first."
        )
    daily = pd.read_csv(GKD_PANEL, comment="#", parse_dates=["date"])
    daily = daily.dropna(subset=["temp_mean_c", "latitude", "longitude"])

    stations = daily[["station_id", "station_name", "latitude", "longitude"]].drop_duplicates()
    located = river_network.locate_frame(stations, max_offset_m=2500.0)
    located = located.rename(columns={"river": "river_matched"})
    daily = daily.merge(
        located[["station_id", "river_matched", "river_km", "offset_m"]], on="station_id", how="left"
    )
    daily = daily.dropna(subset=["river_km"])
    daily["river"] = daily["river_matched"]
    daily["year"] = daily["date"].dt.year
    daily["month"] = daily["date"].dt.month
    return daily


def station_table(daily: pd.DataFrame) -> pd.DataFrame:
    return (
        daily.groupby(["station_id", "station_name", "river", "river_km"], as_index=False)
        .agg(n_days=("temp_mean_c", "size"), year_min=("year", "min"), year_max=("year", "max"))
    )


# --------------------------------------------------------------------------
# estimation
# --------------------------------------------------------------------------
def paired_frame(daily: pd.DataFrame, upstream_id: str, downstream_id: str,
                 event_year: int, window: int = WINDOW_YEARS,
                 max_year: Optional[int] = None, donut: int = 0) -> pd.DataFrame:
    """Daily downstream-minus-upstream difference around one event.

    ``max_year`` truncates the sample, which the placebo needs: a fake shutdown
    three years early would otherwise carry the *real* shutdown year inside its
    own post period and inherit part of the true effect.

    ``donut`` additionally drops whole years either side of the shutdown. Plants
    do not switch off cleanly — Isar 1 lost a fuel element in February 2010 and
    ran at reduced availability into 2011 — so the years touching the event are
    neither properly treated nor properly untreated.
    """
    lo, hi = event_year - window, event_year + window
    if max_year is not None:
        hi = min(hi, max_year)
    subset = daily[(daily["year"] >= lo) & (daily["year"] <= hi) & (daily["year"] != event_year)]
    if donut:
        subset = subset[(subset["year"] < event_year - donut) | (subset["year"] > event_year + donut)]
    wide = (
        subset[subset["station_id"].isin([upstream_id, downstream_id])]
        .pivot_table(index="date", columns="station_id", values="temp_mean_c", aggfunc="mean")
    )
    if upstream_id not in wide.columns or downstream_id not in wide.columns:
        return pd.DataFrame()
    wide = wide.dropna(subset=[upstream_id, downstream_id])
    if wide.empty:
        return pd.DataFrame()

    frame = pd.DataFrame({
        "date": wide.index,
        "upstream_c": wide[upstream_id].to_numpy(),
        "downstream_c": wide[downstream_id].to_numpy(),
    })
    frame["delta_c"] = frame["downstream_c"] - frame["upstream_c"]
    frame["year"] = frame["date"].dt.year
    frame["month"] = frame["date"].dt.month
    frame["post"] = (frame["year"] > event_year).astype(int)
    frame["summer"] = frame["month"].isin(SUMMER_MONTHS).astype(int)
    return frame


def fit_paired(frame: pd.DataFrame) -> Optional[dict]:
    """Regress the daily gap on `post` with month fixed effects (HAC errors)."""
    if frame.empty:
        return None
    pre_n = int((frame["post"] == 0).sum())
    post_n = int((frame["post"] == 1).sum())
    if pre_n < MIN_DAYS_PER_CELL or post_n < MIN_DAYS_PER_CELL:
        return None

    fitted = smf.ols("delta_c ~ post + C(month)", data=frame).fit(
        cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS}
    )
    ci_low, ci_high = fitted.conf_int().loc["post"]
    return {
        "did_c": float(fitted.params["post"]),
        "std_error": float(fitted.bse["post"]),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "p_value": float(fitted.pvalues["post"]),
        "n_days_pre": pre_n,
        "n_days_post": post_n,
        "gap_pre_c": float(frame.loc[frame["post"] == 0, "delta_c"].mean()),
        "gap_post_c": float(frame.loc[frame["post"] == 1, "delta_c"].mean()),
        "up_pre_c": float(frame.loc[frame["post"] == 0, "upstream_c"].mean()),
        "up_post_c": float(frame.loc[frame["post"] == 1, "upstream_c"].mean()),
        "down_pre_c": float(frame.loc[frame["post"] == 0, "downstream_c"].mean()),
        "down_post_c": float(frame.loc[frame["post"] == 1, "downstream_c"].mean()),
    }


def fit_pooled(frame: pd.DataFrame) -> Optional[dict]:
    """Textbook pooled 2x2 on the two gauges, clustered on the gauge."""
    if frame.empty:
        return None
    long = pd.concat([
        frame.assign(temp_c=frame["upstream_c"], treated=0, gauge="upstream"),
        frame.assign(temp_c=frame["downstream_c"], treated=1, gauge="downstream"),
    ], ignore_index=True)
    try:
        fitted = smf.ols("temp_c ~ treated * post + C(month)", data=long).fit(
            cov_type="cluster", cov_kwds={"groups": long["gauge"]}
        )
    except Exception:
        return None
    name = "treated:post"
    if name not in fitted.params:
        return None
    return {"pooled_did_c": float(fitted.params[name]), "pooled_p_value": float(fitted.pvalues[name])}


def estimate_one(daily: pd.DataFrame, site: str, river: str, event_year: int,
                 upstream: pd.Series, downstream: pd.Series, label: str = "all_year",
                 months: Optional[tuple] = None, event_override: Optional[int] = None,
                 max_year: Optional[int] = None, donut: int = 0,
                 window: int = WINDOW_YEARS) -> Optional[dict]:
    """One 2x2 estimate for a site-event and a chosen gauge pair."""
    effective_event = event_override if event_override is not None else event_year
    frame = paired_frame(daily, upstream["station_id"], downstream["station_id"],
                         effective_event, window=window, max_year=max_year, donut=donut)
    if months is not None and not frame.empty:
        frame = frame[frame["month"].isin(months)]
    result = fit_paired(frame)
    if result is None:
        return None
    result.update(fit_pooled(frame) or {})
    result.update({
        "site": site,
        "river": river,
        "event_year": event_year,
        "sample": label,
        "upstream_station": upstream["station_name"],
        "upstream_km": round(float(upstream["distance_km"]), 1),
        "downstream_station": downstream["station_name"],
        "downstream_km": round(float(downstream["distance_km"]), 1),
    })
    return result


def run(daily: pd.DataFrame) -> tuple:
    """All estimates and the underlying gauge inventory."""
    stations = station_table(daily)
    stations = stations.rename(columns={"river_km": "river_km"})
    pairs = station_pairs.candidate_pairs(stations, max_km=MAX_PAIR_KM)
    if pairs.empty:
        return pd.DataFrame(), pairs

    results: List[dict] = []
    for (site, event_year), group in pairs.groupby(["site", "event_year"]):
        clean = group[group["clean"]]
        ups = clean[clean["role"] == "upstream"].sort_values("distance_km")
        downs = clean[clean["role"] == "downstream"].sort_values("distance_km")
        if ups.empty or downs.empty:
            continue
        river = group["river"].iloc[0]
        upstream = ups.iloc[0]

        for rank, (_, downstream) in enumerate(downs.iterrows()):
            # Headline estimate uses the nearest downstream gauge; the rest form
            # the distance-sensitivity curve.
            base = estimate_one(daily, site, river, event_year, upstream, downstream)
            if base is None:
                continue
            base["spec"] = "nearest_downstream" if rank == 0 else "distance_sensitivity"
            results.append(base)

            if rank > 0:
                continue
            for label, months in (("summer_jun_sep", SUMMER_MONTHS), ("winter_oct_may", (10, 11, 12, 1, 2, 3, 4, 5))):
                seasonal = estimate_one(daily, site, river, event_year, upstream, downstream,
                                        label=label, months=months)
                if seasonal:
                    seasonal["spec"] = "season_split"
                    results.append(seasonal)

            # Drop the years touching the shutdown: ramp-down and commissioning
            # of the shutdown itself make them neither clean pre nor clean post.
            donut = estimate_one(daily, site, river, event_year, upstream, downstream,
                                 label="donut_drop_1y_each_side", donut=1, window=WINDOW_YEARS + 1)
            if donut:
                donut["spec"] = "donut"
                results.append(donut)

            placebo = estimate_one(daily, site, river, event_year, upstream, downstream,
                                   label=f"placebo_{event_year - PLACEBO_OFFSET_YEARS}",
                                   event_override=event_year - PLACEBO_OFFSET_YEARS,
                                   max_year=event_year - 1)
            if placebo:
                placebo["spec"] = "placebo"
                results.append(placebo)

    return pd.DataFrame(results), pairs


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------
def plot_site(daily: pd.DataFrame, row: pd.Series, pairs: pd.DataFrame) -> None:
    """Monthly upstream/downstream series and their gap around the shutdown."""
    site, event_year = row["site"], int(row["event_year"])
    group = pairs[(pairs["site"] == site) & (pairs["event_year"] == event_year) & pairs["clean"]]
    up = group[(group["role"] == "upstream") & (group["station_name"] == row["upstream_station"])].iloc[0]
    down = group[(group["role"] == "downstream") & (group["station_name"] == row["downstream_station"])].iloc[0]

    frame = paired_frame(daily, up["station_id"], down["station_id"], event_year, window=WINDOW_YEARS + 2)
    if frame.empty:
        return
    monthly = frame.set_index("date").resample("MS").mean(numeric_only=True).reset_index()

    figure, axes = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True,
                                gridspec_kw={"height_ratios": [2, 1.4]})
    axes[0].plot(monthly["date"], monthly["upstream_c"], color="#2b6cb0", lw=1.6,
                 label=f"upstream · {row['upstream_station']} ({row['upstream_km']:.0f} km)")
    axes[0].plot(monthly["date"], monthly["downstream_c"], color="#c53030", lw=1.6,
                 label=f"downstream · {row['downstream_station']} ({row['downstream_km']:.0f} km)")
    axes[0].set_ylabel("monthly mean water temperature (°C)")
    axes[0].legend(loc="upper left", fontsize=9, frameon=False)
    axes[0].set_title(f"{site} ({row['river']}) — shutdown {event_year}", fontsize=13, loc="left")

    axes[1].axhline(0, color="#a0aec0", lw=0.8)
    axes[1].plot(monthly["date"], monthly["delta_c"], color="#2d3748", lw=1.4)
    pre = monthly[monthly["date"].dt.year < event_year]["delta_c"].mean()
    post = monthly[monthly["date"].dt.year > event_year]["delta_c"].mean()
    axes[1].axhline(pre, xmax=0.5, color="#c53030", ls="--", lw=1.2, label=f"mean gap before: {pre:+.2f} °C")
    axes[1].axhline(post, xmin=0.5, color="#2b6cb0", ls="--", lw=1.2, label=f"mean gap after: {post:+.2f} °C")
    axes[1].set_ylabel("downstream − upstream (°C)")
    axes[1].legend(loc="lower left", fontsize=9, frameon=True, framealpha=0.85,
                   edgecolor="none")

    for axis in axes:
        axis.axvline(pd.Timestamp(f"{event_year}-03-15"), color="#744210", lw=1.4, alpha=0.8)
        axis.spines[["top", "right"]].set_visible(False)

    p_value = float(row["p_value"])
    p_text = "p < 1e-16" if p_value < 1e-16 else f"p = {p_value:.3g}"
    figure.suptitle(
        f"DiD on the daily gap: {row['did_c']:+.3f} °C  ({p_text})",
        y=0.02, fontsize=10, color="#4a5568",
    )
    figure.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    name = site.lower().replace(" ", "_")
    figure.savefig(FIG_DIR / f"{name}_{event_year}_2x2.png", dpi=150, bbox_inches="tight")
    plt.close(figure)


def plot_long_run(daily: pd.DataFrame, pairs: pd.DataFrame, results: pd.DataFrame) -> None:
    """Annual downstream-minus-upstream gap over the whole record, per pair.

    The ±3-year window can only show that the gap moved; this shows *when*. A
    thermal discharge switching off should appear as a step at the shutdown, not
    as a drift that was under way for years.
    """
    headline = results[results["spec"] == "nearest_downstream"]
    if headline.empty:
        return
    seen: set = set()
    panels: List[tuple] = []
    for _, row in headline.iterrows():
        key = (row["upstream_station"], row["downstream_station"])
        if key in seen:
            continue
        seen.add(key)
        group = pairs[(pairs["site"] == row["site"]) & pairs["clean"]]
        up = group[group["station_name"] == row["upstream_station"]]
        down = group[group["station_name"] == row["downstream_station"]]
        if up.empty or down.empty:
            continue
        events = sorted(headline[headline["site"] == row["site"]]["event_year"].unique())
        panels.append((row["site"], row["river"], up.iloc[0], down.iloc[0], events))

    if not panels:
        return
    figure, axes = plt.subplots(len(panels), 1, figsize=(11, 3.1 * len(panels)), sharex=True)
    axes = np.atleast_1d(axes)

    for axis, (site, river, up, down, events) in zip(axes, panels):
        wide = (
            daily[daily["station_id"].isin([up["station_id"], down["station_id"]])]
            .pivot_table(index="date", columns="station_id", values="temp_mean_c", aggfunc="mean")
            .dropna()
        )
        if wide.empty:
            continue
        gap = (wide[down["station_id"]] - wide[up["station_id"]]).rename("gap")
        annual = gap.groupby(gap.index.year).agg(["mean", "count", "std"])
        annual = annual[annual["count"] >= 180]
        error = 1.96 * annual["std"] / np.sqrt(annual["count"])

        axis.axhline(0, color="#a0aec0", lw=0.9)
        axis.fill_between(annual.index, annual["mean"] - error, annual["mean"] + error,
                          color="#3182ce", alpha=0.18)
        axis.plot(annual.index, annual["mean"], color="#2c5282", lw=1.8, marker="o", ms=3.5)
        for event in events:
            axis.axvline(event, color="#c53030", lw=1.6, alpha=0.85)
            axis.annotate(f"shutdown {event}", (event, axis.get_ylim()[1]),
                          textcoords="offset points", xytext=(4, -12),
                          fontsize=8.5, color="#c53030")
        axis.set_ylabel("gap (°C)")
        axis.set_title(
            f"{site} ({river}) · {down['station_name']} minus {up['station_name']} "
            f"({down['distance_km']:.0f} km downstream vs {up['distance_km']:.0f} km upstream)",
            loc="left", fontsize=10.5,
        )
        axis.spines[["top", "right"]].set_visible(False)

    axes[-1].set_xlabel("year")
    figure.suptitle("Annual mean downstream − upstream water temperature gap",
                    fontsize=13, y=1.0, x=0.01, ha="left")
    figure.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIG_DIR / "long_run_gap.png", dpi=150, bbox_inches="tight")
    plt.close(figure)


def plot_distance(results: pd.DataFrame) -> None:
    """Estimated effect against along-river distance of the downstream gauge."""
    subset = results[results["spec"].isin(["nearest_downstream", "distance_sensitivity"])]
    if subset.empty:
        return
    figure, axis = plt.subplots(figsize=(9, 5.5))
    for (site, event_year), group in subset.groupby(["site", "event_year"]):
        group = group.sort_values("downstream_km")
        axis.errorbar(group["downstream_km"], group["did_c"],
                      yerr=[group["did_c"] - group["ci_low"], group["ci_high"] - group["did_c"]],
                      marker="o", capsize=3, lw=1.4, label=f"{site} {event_year}")
    axis.axhline(0, color="#a0aec0", lw=1)
    axis.set_xlabel("along-river distance of the downstream gauge (km)")
    axis.set_ylabel("DiD estimate (°C)")
    axis.set_title("Distance sensitivity: effect decays away from the plant", loc="left")
    axis.legend(fontsize=9, frameon=False)
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIG_DIR / "distance_sensitivity.png", dpi=150, bbox_inches="tight")
    plt.close(figure)


# --------------------------------------------------------------------------
def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    daily = load_daily()
    print(f"plant_2x2_did: {len(daily):,} station-days, {daily['station_id'].nunique()} gauges")

    results, pairs = run(daily)
    pairs.to_csv(OUT_DIR / "station_pairs.csv", index=False)
    if results.empty:
        print("plant_2x2_did: no site-event had both a clean upstream and downstream gauge.")
        return 1

    columns = [
        "site", "river", "event_year", "spec", "sample",
        "upstream_station", "upstream_km", "downstream_station", "downstream_km",
        "up_pre_c", "up_post_c", "down_pre_c", "down_post_c",
        "gap_pre_c", "gap_post_c", "did_c", "std_error", "ci_low", "ci_high",
        "p_value", "pooled_did_c", "pooled_p_value", "n_days_pre", "n_days_post",
    ]
    results = results[[c for c in columns if c in results.columns]].round(4)
    results.to_csv(OUT_DIR / "plant_2x2_results.csv", index=False)

    headline = results[results["spec"] == "nearest_downstream"]
    for _, row in headline.iterrows():
        plot_site(daily, row, pairs)
    plot_distance(results)
    plot_long_run(daily, pairs, results)

    print("\nHeadline 2x2 estimates (nearest clean gauge pair, daily gap, HAC errors)\n")
    show = headline[["site", "river", "event_year", "upstream_station", "downstream_station",
                     "downstream_km", "gap_pre_c", "gap_post_c", "did_c", "p_value",
                     "n_days_pre", "n_days_post"]]
    print(show.to_string(index=False))
    print(f"\nWrote {OUT_DIR / 'plant_2x2_results.csv'} and figures to {FIG_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
