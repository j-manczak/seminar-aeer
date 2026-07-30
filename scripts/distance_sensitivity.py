"""How far downstream can we still see anything, and how far should we look?

Two different questions get mixed up in "sensitivity analysis by distance":

1. **How does the effect decay along the river?** Answering that needs several
   downstream gauges per event. We have that for the cooling-tower sites, where
   there is no effect to decay, and *not* for the Isar, the one site with a real
   effect — it has a single downstream gauge with pre-2011 data. So the decay
   curve cannot be estimated where it would matter.

2. **Out to what distance is this design able to detect a plume at all?** That
   we can answer, because every estimate carries a minimum detectable effect
   (MDE): the smallest true effect the test would find 80 % of the time. Beyond
   the distance where the MDE exceeds any plausible plume, a null result says
   nothing.

This module reports both honestly and derives the along-river radius used by the
confounder analysis and the maps. Distances are always along the channel, from
:mod:`pipeline.river_network`, never straight-line.

    python scripts/distance_sensitivity.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pipeline.config import ANALYSIS_DIR, PROJECT_ROOT

RESULTS = ANALYSIS_DIR / "plant_2x2" / "plant_2x2_results.csv"
OUT_DIR = ANALYSIS_DIR / "plant_2x2"
FIG_DIR = PROJECT_ROOT / "figures" / "plant_2x2"
RADIUS_FILE = OUT_DIR / "analysis_radius.json"

DISTANCE_SPECS = ["nearest_downstream", "distance_sensitivity", "best_coverage"]

# A thermal plume from a once-through reactor is worth calling detectable at a
# few tenths of a degree; below that the signal is inside normal river noise.
PLUME_FLOOR_C = 0.25

# The radius handed to the confounder analysis and the maps is rounded up from
# the largest confirmed detection to the next round number, so it is stable
# against one gauge being added or removed.
RADIUS_ROUNDING_KM = 25.0
RADIUS_FLOOR_KM = 50.0


def load_results() -> pd.DataFrame:
    if not RESULTS.exists():
        raise FileNotFoundError(f"{RESULTS} not found — run scripts/plant_2x2_did.py first.")
    return pd.read_csv(RESULTS)


def distance_table(results: pd.DataFrame) -> pd.DataFrame:
    """One row per (outcome, site, event, downstream gauge)."""
    subset = results[results["spec"].isin(DISTANCE_SPECS)].copy()
    subset = subset[subset["sample"].eq("all_year")]
    subset = subset.drop_duplicates(
        subset=["outcome", "site", "event_year", "upstream_station", "downstream_station"]
    )
    subset["significant"] = subset["p_value"] < 0.05
    subset["detectable"] = subset["min_detectable_effect"] <= PLUME_FLOOR_C
    # A cooling shutdown should *lower* the downstream temperature gap and
    # *raise* the oxygen gap; anything else is not a plume signature.
    expected_sign = np.where(subset["outcome"].eq("water_temperature"), -1.0, 1.0)
    subset["expected_direction"] = np.sign(subset["did"]) == expected_sign
    subset["confirmed"] = subset["significant"] & subset["expected_direction"]
    return subset.sort_values(["outcome", "site", "event_year", "downstream_km"])


def placebo_by_pair(results: pd.DataFrame) -> pd.DataFrame:
    """Placebo estimate per gauge pair, to judge whether an estimate is drift."""
    placebo = results[results["spec"].str.endswith("placebo")].copy()
    return placebo[["outcome", "site", "event_year", "upstream_station", "downstream_station",
                    "did", "p_value"]].rename(columns={"did": "placebo_did",
                                                       "p_value": "placebo_p"})


def derive_radius(table: pd.DataFrame) -> dict:
    """The along-river radius the rest of the project should use."""
    temperature = table[table["outcome"].eq("water_temperature")]
    confirmed = temperature[temperature["confirmed"]]

    max_confirmed = float(confirmed["downstream_km"].max()) if not confirmed.empty else np.nan
    # Where does the design still have the power to see a plume at all?
    detectable = temperature[temperature["detectable"]]
    max_detectable = float(detectable["downstream_km"].max()) if not detectable.empty else np.nan

    if np.isnan(max_confirmed):
        radius = RADIUS_FLOOR_KM
        basis = "no confirmed detection; fell back to the floor"
    else:
        rounded = float(np.ceil(max_confirmed / RADIUS_ROUNDING_KM) * RADIUS_ROUNDING_KM)
        radius = max(rounded, RADIUS_FLOOR_KM)
        basis = (f"largest confirmed detection {max_confirmed:.1f} km, rounded up to the next "
                 f"{RADIUS_ROUNDING_KM:.0f} km and floored at {RADIUS_FLOOR_KM:.0f} km")

    return {
        "radius_km": radius,
        "basis": basis,
        "max_confirmed_detection_km": None if np.isnan(max_confirmed) else max_confirmed,
        "max_distance_with_power_km": None if np.isnan(max_detectable) else max_detectable,
        "plume_floor_c": PLUME_FLOOR_C,
        "note": (
            "Distances are along the river channel, not straight-line. The radius is a "
            "detection limit for this design, not an estimate of how far a thermal plume "
            "physically reaches: the one site with a real effect (Isar) has a single "
            "downstream gauge with pre-2011 data, so no decay curve can be fitted there."
        ),
    }


def plot(table: pd.DataFrame, radius: dict) -> None:
    outcomes = [o for o in ("water_temperature", "dissolved_oxygen") if o in set(table["outcome"])]
    if not outcomes:
        return
    figure, axes = plt.subplots(len(outcomes), 1, figsize=(10.5, 4.6 * len(outcomes)), squeeze=False)

    for axis, outcome in zip(axes[:, 0], outcomes):
        subset = table[table["outcome"].eq(outcome)]
        unit = subset["unit"].iloc[0] if "unit" in subset else ""
        for (site, event), group in subset.groupby(["site", "event_year"]):
            group = group.sort_values("downstream_km")
            axis.errorbar(
                group["downstream_km"], group["did"],
                yerr=[group["did"] - group["ci_low"], group["ci_high"] - group["did"]],
                marker="o", capsize=3, lw=1.4, ms=5, label=f"{site} {event}",
            )
        # The band the design simply cannot see into.
        mde = subset.groupby("downstream_km")["min_detectable_effect"].median()
        if not mde.empty:
            axis.fill_between(mde.index, -mde.values, mde.values, color="#a0aec0", alpha=0.16,
                              label="below the detection limit (median MDE)", zorder=0)
        axis.axhline(0, color="#718096", lw=1)
        axis.axvline(radius["radius_km"], color="#c53030", ls="--", lw=1.3)
        axis.annotate(f"radius used: {radius['radius_km']:.0f} km",
                      (radius["radius_km"], axis.get_ylim()[1]), textcoords="offset points",
                      xytext=(6, -14), fontsize=9, color="#c53030")
        axis.set_xlabel("along-river distance of the downstream gauge (km)")
        axis.set_ylabel(f"DiD estimate ({unit})")
        axis.set_title(f"Distance sensitivity — {outcome.replace('_', ' ')}", loc="left", fontsize=12)
        axis.legend(fontsize=8.5, frameon=False, ncol=2)
        axis.spines[["top", "right"]].set_visible(False)

    figure.suptitle("Effect against along-river distance, with the detection limit shaded",
                    fontsize=13, x=0.01, ha="left", y=1.0)
    figure.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIG_DIR / "distance_sensitivity.png", dpi=150, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    results = load_results()
    table = distance_table(results)
    table = table.merge(placebo_by_pair(results),
                        on=["outcome", "site", "event_year", "upstream_station", "downstream_station"],
                        how="left")
    # An estimate no larger than its own placebo is drift, not an effect.
    table["exceeds_placebo"] = table["did"].abs() > table["placebo_did"].abs().fillna(0)
    table["verdict"] = np.select(
        [table["confirmed"] & table["exceeds_placebo"],
         table["confirmed"] & ~table["exceeds_placebo"],
         ~table["significant"] & ~table["detectable"]],
        ["effect", "significant but no larger than its placebo (drift)",
         "null, but underpowered"],
        default="null",
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    columns = ["outcome", "site", "river", "event_year", "upstream_station", "upstream_km",
               "downstream_station", "downstream_km", "did", "ci_low", "ci_high", "p_value",
               "min_detectable_effect", "placebo_did", "placebo_p", "n_pre", "n_post", "verdict"]
    table[[c for c in columns if c in table.columns]].round(4).to_csv(
        OUT_DIR / "distance_sensitivity.csv", index=False)

    radius = derive_radius(table)
    RADIUS_FILE.write_text(json.dumps(radius, indent=2), encoding="utf-8")
    plot(table, radius)

    pd.set_option("display.width", 260)
    print("Effect against along-river distance\n")
    show = table[["outcome", "site", "event_year", "downstream_station", "downstream_km",
                  "did", "min_detectable_effect", "p_value", "verdict"]]
    print(show.to_string(index=False))
    print("\nDerived analysis radius")
    for key, value in radius.items():
        print(f"  {key}: {value}")
    print(f"\nWrote {OUT_DIR / 'distance_sensitivity.csv'} and {RADIUS_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
