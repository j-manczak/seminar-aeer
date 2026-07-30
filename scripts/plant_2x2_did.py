"""Per-site 2x2 difference-in-differences on upstream vs downstream river data.

Design
------
For one nuclear site and one shutdown year the 2x2 is

                     before shutdown        after shutdown
    upstream  (C)    mean y_up,before       mean y_up,after
    downstream(T)    mean y_down,before     mean y_down,after

and the estimate is the difference of the two differences. Because the two
gauges sit on the same river and are read in the same period, the sharper way to
write the same thing is the **paired difference**

    dy_t = y_downstream,t - y_upstream,t
    dy_t = a + b * post_t + month fixed effects + e_t

where ``b`` is numerically the DiD estimate but removes all common weather,
season and river-wide trend variation before estimation.

Two outcomes
------------
``water_temperature``  GKD Bayern daily means, ~1995-2024. Paired on the day.
``dissolved_oxygen``   GKD Bayern chemistry, roughly fortnightly samples back to
                       1990. Paired on the *month*, because the up- and
                       downstream sampling points are not always visited on the
                       same day. The oxygen panel is one to two orders of
                       magnitude thinner than the temperature one, and it uses
                       its own gauge pair — chemistry sampling points are not the
                       continuous temperature gauges.

Standard errors are Newey-West (HAC); the bandwidth is set per outcome to about
a month of observations. The pooled two-gauge regression, clustered on the
gauge, is reported alongside as a cross-check.

Robustness shipped with every estimate: donut, placebo, season split and a full
distance sweep over every available downstream gauge.

Run:
    python scripts/plant_2x2_did.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
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

OUT_DIR = ANALYSIS_DIR / "plant_2x2"
FIG_DIR = PROJECT_ROOT / "figures" / "plant_2x2"

WINDOW_YEARS = 3
SUMMER_MONTHS = (6, 7, 8, 9)
PLACEBO_OFFSET_YEARS = 3
MAX_PAIR_KM = 120.0


@dataclass(frozen=True)
class Outcome:
    """One measured quantity, with the settings its sampling frequency needs."""

    name: str
    label: str
    unit: str
    source_file: Path
    value_column: str
    pair_on: str        # "date" for daily data, "month" for campaign sampling
    hac_lags: int       # ~one month of observations
    min_per_cell: int   # a cell needs this many paired periods to be reported


OUTCOMES = [
    Outcome(
        name="water_temperature", label="water temperature", unit="°C",
        source_file=PROCESSED_DIR / "gkd_water_temperature_daily.csv",
        value_column="temp_mean_c", pair_on="date", hac_lags=30, min_per_cell=60,
    ),
    Outcome(
        name="dissolved_oxygen", label="dissolved oxygen", unit="mg/l",
        source_file=PROCESSED_DIR / "gkd_dissolved_oxygen.csv",
        value_column="oxygen_mg_l", pair_on="month", hac_lags=2, min_per_cell=12,
    ),
]


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
def load_panel(outcome: Outcome) -> pd.DataFrame:
    """Tidy panel for one outcome, with every gauge placed on its river."""
    if not outcome.source_file.exists():
        print(f"plant_2x2_did: {outcome.source_file.name} missing, skipping {outcome.name}.")
        return pd.DataFrame()

    panel = pd.read_csv(outcome.source_file, comment="#", parse_dates=["date"])
    panel = panel.rename(columns={outcome.value_column: "value"})
    panel = panel.dropna(subset=["value", "latitude", "longitude"])

    stations = panel[["station_id", "station_name", "latitude", "longitude"]].drop_duplicates()
    located = river_network.locate_frame(stations, max_offset_m=2500.0)
    located = located[located["river"].notna()]
    panel = panel.drop(columns=[c for c in ("river", "river_km", "offset_m") if c in panel.columns])
    panel = panel.merge(located[["station_id", "river", "river_km", "offset_m"]],
                        on="station_id", how="inner")

    panel["year"] = panel["date"].dt.year
    panel["month"] = panel["date"].dt.month
    panel["period"] = (
        panel["date"] if outcome.pair_on == "date"
        else panel["date"].dt.to_period("M").dt.to_timestamp()
    )
    return panel


def station_table(panel: pd.DataFrame) -> pd.DataFrame:
    return (
        panel.groupby(["station_id", "station_name", "river", "river_km"], as_index=False)
        .agg(n_obs=("value", "size"), year_min=("year", "min"), year_max=("year", "max"))
    )


# --------------------------------------------------------------------------
# estimation
# --------------------------------------------------------------------------
def paired_frame(panel: pd.DataFrame, upstream_id, downstream_id, event_year: int,
                 window: int = WINDOW_YEARS, max_year: Optional[int] = None,
                 donut: int = 0) -> pd.DataFrame:
    """Downstream-minus-upstream difference per shared period around one event.

    ``max_year`` truncates the sample, which the placebo needs: a fake shutdown
    three years early would otherwise carry the *real* shutdown year inside its
    own post period and inherit part of the true effect.

    ``donut`` drops whole years either side of the shutdown. Plants do not switch
    off cleanly — Isar 1 lost a fuel element in February 2010 and ran at reduced
    availability into 2011 — so the years touching the event are neither properly
    treated nor properly untreated.
    """
    lo, hi = event_year - window, event_year + window
    if max_year is not None:
        hi = min(hi, max_year)
    subset = panel[(panel["year"] >= lo) & (panel["year"] <= hi) & (panel["year"] != event_year)]
    if donut:
        subset = subset[(subset["year"] < event_year - donut) | (subset["year"] > event_year + donut)]

    wide = (
        subset[subset["station_id"].isin([upstream_id, downstream_id])]
        .pivot_table(index="period", columns="station_id", values="value", aggfunc="mean")
    )
    if upstream_id not in wide.columns or downstream_id not in wide.columns:
        return pd.DataFrame()
    wide = wide.dropna(subset=[upstream_id, downstream_id])
    if wide.empty:
        return pd.DataFrame()

    frame = pd.DataFrame({
        "period": wide.index,
        "upstream": wide[upstream_id].to_numpy(),
        "downstream": wide[downstream_id].to_numpy(),
    })
    frame["delta"] = frame["downstream"] - frame["upstream"]
    frame["year"] = frame["period"].dt.year
    frame["month"] = frame["period"].dt.month
    frame["post"] = (frame["year"] > event_year).astype(int)
    return frame


def fit_paired(frame: pd.DataFrame, outcome: Outcome) -> Optional[dict]:
    """Regress the paired gap on `post` with month fixed effects (HAC errors)."""
    if frame.empty:
        return None
    pre_n = int((frame["post"] == 0).sum())
    post_n = int((frame["post"] == 1).sum())
    if pre_n < outcome.min_per_cell or post_n < outcome.min_per_cell:
        return None
    if frame["month"].nunique() < 2:
        return None

    fitted = smf.ols("delta ~ post + C(month)", data=frame).fit(
        cov_type="HAC", cov_kwds={"maxlags": outcome.hac_lags}
    )
    ci_low, ci_high = fitted.conf_int().loc["post"]
    standard_error = float(fitted.bse["post"])
    return {
        "did": float(fitted.params["post"]),
        "std_error": standard_error,
        # Smallest true effect this test would detect 80 % of the time at the 5 %
        # level. Without it a null is unreadable: "no effect" and "no power to
        # see one" look identical, and the oxygen panel is thin enough that the
        # distinction decides the interpretation.
        "min_detectable_effect": round(2.802 * standard_error, 4),
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "p_value": float(fitted.pvalues["post"]),
        "n_pre": pre_n,
        "n_post": post_n,
        "gap_pre": float(frame.loc[frame["post"] == 0, "delta"].mean()),
        "gap_post": float(frame.loc[frame["post"] == 1, "delta"].mean()),
        "up_pre": float(frame.loc[frame["post"] == 0, "upstream"].mean()),
        "up_post": float(frame.loc[frame["post"] == 1, "upstream"].mean()),
        "down_pre": float(frame.loc[frame["post"] == 0, "downstream"].mean()),
        "down_post": float(frame.loc[frame["post"] == 1, "downstream"].mean()),
    }


def fit_pooled(frame: pd.DataFrame) -> Optional[dict]:
    """Textbook pooled 2x2 on the two gauges, clustered on the gauge."""
    if frame.empty:
        return None
    long = pd.concat([
        frame.assign(value=frame["upstream"], treated=0, gauge="upstream"),
        frame.assign(value=frame["downstream"], treated=1, gauge="downstream"),
    ], ignore_index=True)
    try:
        fitted = smf.ols("value ~ treated * post + C(month)", data=long).fit(
            cov_type="cluster", cov_kwds={"groups": long["gauge"]}
        )
    except Exception:
        return None
    if "treated:post" not in fitted.params:
        return None
    return {"pooled_did": float(fitted.params["treated:post"]),
            "pooled_p_value": float(fitted.pvalues["treated:post"])}


def estimate_one(panel: pd.DataFrame, outcome: Outcome, site: str, river: str, event_year: int,
                 upstream: pd.Series, downstream: pd.Series, sample: str = "all_year",
                 months: Optional[tuple] = None, event_override: Optional[int] = None,
                 max_year: Optional[int] = None, donut: int = 0,
                 window: int = WINDOW_YEARS) -> Optional[dict]:
    """One 2x2 estimate for a site-event, an outcome and a chosen gauge pair."""
    effective_event = event_override if event_override is not None else event_year
    frame = paired_frame(panel, upstream["station_id"], downstream["station_id"],
                         effective_event, window=window, max_year=max_year, donut=donut)
    if months is not None and not frame.empty:
        frame = frame[frame["month"].isin(months)]
    result = fit_paired(frame, outcome)
    if result is None:
        return None
    result.update(fit_pooled(frame) or {})
    result.update({
        "outcome": outcome.name,
        "unit": outcome.unit,
        "site": site,
        "river": river,
        "event_year": event_year,
        "sample": sample,
        "upstream_station": upstream["station_name"],
        "upstream_km": round(float(upstream["distance_km"]), 1),
        "downstream_station": downstream["station_name"],
        "downstream_km": round(float(downstream["distance_km"]), 1),
    })
    return result


def run_outcome(panel: pd.DataFrame, outcome: Outcome) -> tuple:
    """Every estimate for one outcome, plus the gauge inventory behind it."""
    if panel.empty:
        return pd.DataFrame(), pd.DataFrame()

    stations = station_table(panel)
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

        # The headline is the *closest pair that actually estimates*, not simply
        # the closest pair: the nearest gauge sometimes starts recording after
        # the shutdown, which would silently drop the site instead of falling
        # back to the next one downstream.
        headline_done = False
        headline_pair = None
        for _, downstream in downs.iterrows():
            base = estimate_one(panel, outcome, site, river, event_year, upstream, downstream)
            if base is None:
                continue
            base["spec"] = "distance_sensitivity" if headline_done else "nearest_downstream"
            results.append(base)

            if headline_done:
                continue
            headline_done = True
            results.extend(robustness_battery(panel, outcome, site, river, event_year,
                                              upstream, downstream))
            headline_pair = (upstream["station_id"], downstream["station_id"])

        # Proximity and statistical power pull in different directions: the
        # nearest gauge may have only started recording recently, while a gauge
        # further away has thirty years behind it. Report the best-powered clean
        # pair as well, so a thin headline cannot hide a usable estimate — and
        # give it the same robustness battery, otherwise it is an unchecked
        # second estimate that invites cherry-picking.
        best = None
        for _, up_candidate in ups.iterrows():
            for _, down_candidate in downs.iterrows():
                estimate = estimate_one(panel, outcome, site, river, event_year,
                                        up_candidate, down_candidate)
                if estimate is None:
                    continue
                power = min(estimate["n_pre"], estimate["n_post"])
                if best is None or power > best[0]:
                    best = (power, estimate, up_candidate, down_candidate)
        if best is not None:
            _, estimate, up_best, down_best = best
            estimate["spec"] = "best_coverage"
            results.append(estimate)
            if not headline_done or (up_best["station_id"], down_best["station_id"]) != headline_pair:
                results.extend(robustness_battery(panel, outcome, site, river, event_year,
                                                  up_best, down_best, prefix="best_coverage_"))

    return pd.DataFrame(results), pairs


def robustness_battery(panel: pd.DataFrame, outcome: Outcome, site: str, river: str,
                       event_year: int, upstream: pd.Series, downstream: pd.Series,
                       prefix: str = "") -> List[dict]:
    """Donut, season split and placebo for one gauge pair."""
    out: List[dict] = []

    donut = estimate_one(panel, outcome, site, river, event_year, upstream, downstream,
                         sample="donut_drop_1y_each_side", donut=1, window=WINDOW_YEARS + 1)
    if donut:
        donut["spec"] = f"{prefix}donut"
        out.append(donut)

    for label, months in (("summer_jun_sep", SUMMER_MONTHS),
                          ("winter_oct_may", (10, 11, 12, 1, 2, 3, 4, 5))):
        seasonal = estimate_one(panel, outcome, site, river, event_year, upstream,
                                downstream, sample=label, months=months)
        if seasonal:
            seasonal["spec"] = f"{prefix}season_split"
            out.append(seasonal)

    placebo = estimate_one(panel, outcome, site, river, event_year, upstream, downstream,
                           sample=f"placebo_{event_year - PLACEBO_OFFSET_YEARS}",
                           event_override=event_year - PLACEBO_OFFSET_YEARS,
                           max_year=event_year - 1)
    if placebo:
        placebo["spec"] = f"{prefix}placebo"
        out.append(placebo)
    return out


# --------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------
def plot_site(panel: pd.DataFrame, outcome: Outcome, row: pd.Series, pairs: pd.DataFrame) -> None:
    """Monthly upstream/downstream series and their gap around the shutdown."""
    site, event_year = row["site"], int(row["event_year"])
    group = pairs[(pairs["site"] == site) & (pairs["event_year"] == event_year) & pairs["clean"]]
    up = group[(group["role"] == "upstream") & (group["station_name"] == row["upstream_station"])]
    down = group[(group["role"] == "downstream") & (group["station_name"] == row["downstream_station"])]
    if up.empty or down.empty:
        return
    up, down = up.iloc[0], down.iloc[0]

    frame = paired_frame(panel, up["station_id"], down["station_id"], event_year,
                         window=WINDOW_YEARS + 2)
    if frame.empty:
        return
    monthly = frame.set_index("period").resample("MS").mean(numeric_only=True).reset_index()

    figure, axes = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True,
                                gridspec_kw={"height_ratios": [2, 1.4]})
    axes[0].plot(monthly["period"], monthly["upstream"], color="#2b6cb0", lw=1.6,
                 label=f"upstream · {row['upstream_station']} ({row['upstream_km']:.0f} km)")
    axes[0].plot(monthly["period"], monthly["downstream"], color="#c53030", lw=1.6,
                 label=f"downstream · {row['downstream_station']} ({row['downstream_km']:.0f} km)")
    axes[0].set_ylabel(f"monthly mean {outcome.label} ({outcome.unit})")
    axes[0].legend(loc="upper left", fontsize=9, frameon=False)
    axes[0].set_title(f"{site} ({row['river']}) — shutdown {event_year}", fontsize=13, loc="left")

    axes[1].axhline(0, color="#a0aec0", lw=0.8)
    axes[1].plot(monthly["period"], monthly["delta"], color="#2d3748", lw=1.4)
    pre = monthly[monthly["period"].dt.year < event_year]["delta"].mean()
    post = monthly[monthly["period"].dt.year > event_year]["delta"].mean()
    axes[1].axhline(pre, xmax=0.5, color="#c53030", ls="--", lw=1.2,
                    label=f"mean gap before: {pre:+.2f} {outcome.unit}")
    axes[1].axhline(post, xmin=0.5, color="#2b6cb0", ls="--", lw=1.2,
                    label=f"mean gap after: {post:+.2f} {outcome.unit}")
    axes[1].set_ylabel(f"downstream − upstream ({outcome.unit})")
    axes[1].legend(loc="lower left", fontsize=9, frameon=True, framealpha=0.85, edgecolor="none")

    for axis in axes:
        axis.axvline(pd.Timestamp(f"{event_year}-03-15"), color="#744210", lw=1.4, alpha=0.8)
        axis.spines[["top", "right"]].set_visible(False)

    p_value = float(row["p_value"])
    p_text = "p < 1e-16" if p_value < 1e-16 else f"p = {p_value:.3g}"
    figure.suptitle(f"DiD on the paired gap: {row['did']:+.3f} {outcome.unit}  ({p_text})",
                    y=0.02, fontsize=10, color="#4a5568")
    figure.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    name = site.lower().replace(" ", "_")
    figure.savefig(FIG_DIR / f"{name}_{event_year}_{outcome.name}.png", dpi=150, bbox_inches="tight")
    plt.close(figure)


def plot_long_run(panel: pd.DataFrame, outcome: Outcome, pairs: pd.DataFrame,
                  results: pd.DataFrame) -> None:
    """Annual downstream-minus-upstream gap over the whole record, per pair."""
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
            panel[panel["station_id"].isin([up["station_id"], down["station_id"]])]
            .pivot_table(index="period", columns="station_id", values="value", aggfunc="mean")
            .dropna()
        )
        if wide.empty:
            continue
        gap = (wide[down["station_id"]] - wide[up["station_id"]]).rename("gap")
        annual = gap.groupby(gap.index.year).agg(["mean", "count", "std"])
        annual = annual[annual["count"] >= (180 if outcome.pair_on == "date" else 6)]
        if annual.empty:
            continue
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
        axis.set_ylabel(f"gap ({outcome.unit})")
        axis.set_title(
            f"{site} ({river}) · {down['station_name']} minus {up['station_name']} "
            f"({down['distance_km']:.0f} km downstream vs {up['distance_km']:.0f} km upstream)",
            loc="left", fontsize=10.5,
        )
        axis.spines[["top", "right"]].set_visible(False)

    axes[-1].set_xlabel("year")
    figure.suptitle(f"Annual mean downstream − upstream {outcome.label} gap",
                    fontsize=13, y=1.0, x=0.01, ha="left")
    figure.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIG_DIR / f"long_run_gap_{outcome.name}.png", dpi=150, bbox_inches="tight")
    plt.close(figure)


# --------------------------------------------------------------------------
def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_results: List[pd.DataFrame] = []
    all_pairs: List[pd.DataFrame] = []

    for outcome in OUTCOMES:
        panel = load_panel(outcome)
        if panel.empty:
            continue
        print(f"plant_2x2_did: {outcome.name}: {len(panel):,} readings, "
              f"{panel['station_id'].nunique()} gauges", flush=True)

        results, pairs = run_outcome(panel, outcome)
        if results.empty:
            print(f"plant_2x2_did: {outcome.name}: no site-event had a clean gauge pair.")
            continue
        pairs = pairs.assign(outcome=outcome.name)
        all_pairs.append(pairs)
        all_results.append(results)

        for _, row in results[results["spec"] == "nearest_downstream"].iterrows():
            plot_site(panel, outcome, row, pairs)
        plot_long_run(panel, outcome, pairs, results)

    if not all_results:
        print("plant_2x2_did: nothing estimable.")
        return 1

    results = pd.concat(all_results, ignore_index=True)
    columns = [
        "outcome", "site", "river", "event_year", "spec", "sample", "unit",
        "upstream_station", "upstream_km", "downstream_station", "downstream_km",
        "up_pre", "up_post", "down_pre", "down_post", "gap_pre", "gap_post",
        "did", "std_error", "min_detectable_effect", "ci_low", "ci_high", "p_value",
        "pooled_did", "pooled_p_value", "n_pre", "n_post",
    ]
    results = results[[c for c in columns if c in results.columns]].round(4)
    results.to_csv(OUT_DIR / "plant_2x2_results.csv", index=False)
    pd.concat(all_pairs, ignore_index=True).to_csv(OUT_DIR / "station_pairs.csv", index=False)

    pd.set_option("display.width", 260)
    for outcome in OUTCOMES:
        headline = results[(results["outcome"] == outcome.name) & (results["spec"] == "nearest_downstream")]
        if headline.empty:
            continue
        print(f"\nHeadline 2x2 — {outcome.label} ({outcome.unit}), nearest clean gauge pair\n")
        print(headline[["site", "river", "event_year", "upstream_station", "downstream_station",
                        "downstream_km", "gap_pre", "gap_post", "did", "p_value",
                        "n_pre", "n_post"]].to_string(index=False))

    print(f"\nWrote {OUT_DIR / 'plant_2x2_results.csv'} and figures to {FIG_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
