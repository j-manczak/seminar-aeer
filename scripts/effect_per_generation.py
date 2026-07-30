"""Warming per unit of electricity — and per unit of heat that reached the river.

The raw 2x2 estimates are not comparable across sites, because the shutdowns
were not the same size and, more importantly, because the plants did not send
comparable amounts of heat to their rivers. Two normalisations answer two
different questions:

``per TWh``   °C per TWh of annual net generation removed. The economically
              natural denominator, and what the supervisor's question asks for:
              what did a unit of nuclear electricity cost the river?
``per GW``    °C per GW of waste heat that actually reached the water. The
              physically correct denominator. This is where the cooling
              technology enters, and it is what makes the cross-site pattern
              interpretable rather than contradictory.

Reporting only the first makes tower sites look like failed treatments. They
were not treatments of comparable size: Isar 1 put roughly 1.6 GW into the Isar,
Grafenrheinfeld about 0.075 GW into the Main — a factor of twenty — while their
electrical outputs differ by less than a third.

    python scripts/effect_per_generation.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pipeline import station_pairs, thermal_load
from pipeline.config import ANALYSIS_DIR, PROJECT_ROOT

RESULTS = ANALYSIS_DIR / "plant_2x2" / "plant_2x2_results.csv"
DISTANCE = ANALYSIS_DIR / "plant_2x2" / "distance_sensitivity.csv"
OUT_DIR = ANALYSIS_DIR / "plant_2x2"
FIG_DIR = PROJECT_ROOT / "figures" / "plant_2x2"

HEADLINE_SPECS = ["nearest_downstream", "donut"]


def load_headline() -> pd.DataFrame:
    if not RESULTS.exists():
        raise FileNotFoundError(f"{RESULTS} not found — run scripts/plant_2x2_did.py first.")
    results = pd.read_csv(RESULTS)
    keep = results["spec"].isin(HEADLINE_SPECS) & results["sample"].isin(
        ["all_year", "donut_drop_1y_each_side"])
    return results[keep].copy()


def attach_load(estimates: pd.DataFrame) -> pd.DataFrame:
    """Add the electricity and river-bound heat each event removed."""
    sites = {s.site: s for s in station_pairs.plant_sites()}
    rows = []
    for _, row in estimates.iterrows():
        site = sites.get(row["site"])
        if site is None:
            continue
        load = thermal_load.site_event_load(site.blocks, int(row["event_year"]))
        if not load:
            continue
        rows.append({**row.to_dict(), **load})
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame

    frame["heat_to_river_gw"] = frame["heat_to_river_mw"] / 1000.0
    frame["waste_heat_gw"] = frame["waste_heat_mw"] / 1000.0

    # Effects are negative for temperature (cooling) — flip the sign so the
    # normalised numbers read as "warming caused per unit", which is what the
    # shutdown removed.
    sign = np.where(frame["outcome"].eq("water_temperature"), -1.0, 1.0)
    frame["effect_removed"] = frame["did"] * sign

    frame["per_twh"] = frame["effect_removed"] / frame["annual_net_twh"]
    frame["per_twh_ci_low"] = (frame["ci_low"] * sign) / frame["annual_net_twh"]
    frame["per_twh_ci_high"] = (frame["ci_high"] * sign) / frame["annual_net_twh"]

    frame["per_gw_river_heat"] = frame["effect_removed"] / frame["heat_to_river_gw"]
    frame["per_gw_ci_low"] = (frame["ci_low"] * sign) / frame["heat_to_river_gw"]
    frame["per_gw_ci_high"] = (frame["ci_high"] * sign) / frame["heat_to_river_gw"]

    # Dividing an estimate that is really drift by a tiny denominator produces a
    # large, confident-looking, meaningless number: the tower sites put only
    # ~0.076 GW into their rivers, so any noise is multiplied by thirteen. Only
    # estimates the distance analysis certified as real effects are interpretable
    # here; the rest are carried so the table is complete, and flagged.
    frame["interpretable"] = False
    if DISTANCE.exists():
        verdicts = pd.read_csv(DISTANCE)[
            ["outcome", "site", "event_year", "downstream_station", "verdict"]
        ].drop_duplicates()
        frame = frame.merge(verdicts, on=["outcome", "site", "event_year", "downstream_station"],
                            how="left", suffixes=("", "_v"))
        frame["interpretable"] = frame["verdict"].eq("effect")
    return frame


def plot(frame: pd.DataFrame) -> None:
    subset = frame[frame["outcome"].eq("water_temperature") & frame["spec"].eq("nearest_downstream")]
    if subset.empty:
        return
    subset = subset.sort_values("heat_to_river_gw")
    labels = [f"{r.site} {r.event_year}" for r in subset.itertuples()]

    figure, axes = plt.subplots(1, 2, figsize=(13.5, 5.6))

    for axis, (value, low, high, title, unit) in zip(axes, [
        ("per_twh", "per_twh_ci_low", "per_twh_ci_high",
         "per TWh of annual generation removed", "°C per TWh/a"),
        ("per_gw_river_heat", "per_gw_ci_low", "per_gw_ci_high",
         "per GW of waste heat reaching the river", "°C per GW"),
    ]):
        positions = np.arange(len(subset))
        lower = (subset[value] - subset[[low, high]].min(axis=1)).to_numpy()
        upper = (subset[[low, high]].max(axis=1) - subset[value]).to_numpy()
        colours = ["#c53030" if ok else "#cbd5e0" for ok in subset["interpretable"]]
        axis.barh(positions, subset[value], color=colours, height=0.55)
        axis.errorbar(subset[value], positions, xerr=[lower, upper], fmt="none",
                      ecolor="#2d3748", elinewidth=1.1, capsize=3)
        axis.axvline(0, color="#4a5568", lw=1)
        axis.set_yticks(positions)
        axis.set_yticklabels(labels, fontsize=9.5)
        axis.set_xlabel(unit)
        axis.set_title(title, loc="left", fontsize=11.5)
        axis.spines[["top", "right"]].set_visible(False)

    figure.suptitle(
        "Warming removed per unit — red = confirmed effect; grey = drift, shown only for completeness",
        fontsize=13, x=0.01, ha="left", y=1.0,
    )
    figure.tight_layout()
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIG_DIR / "effect_per_generation.png", dpi=150, bbox_inches="tight")
    plt.close(figure)


def main() -> int:
    frame = attach_load(load_headline())
    if frame.empty:
        print("effect_per_generation: nothing to normalise.")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    columns = [
        "outcome", "site", "river", "event_year", "spec", "blocks_shut",
        "electric_net_mw", "annual_net_twh", "waste_heat_gw", "heat_to_river_gw",
        "downstream_station", "downstream_km", "did", "ci_low", "ci_high", "p_value",
        "effect_removed", "per_twh", "per_twh_ci_low", "per_twh_ci_high",
        "per_gw_river_heat", "per_gw_ci_low", "per_gw_ci_high", "verdict", "interpretable",
        "figures_approximate",
    ]
    table = frame[[c for c in columns if c in frame.columns]].round(4)
    table.to_csv(OUT_DIR / "effect_per_generation.csv", index=False)

    thermal_load.block_table().round(3).to_csv(OUT_DIR / "reactor_thermal_load.csv", index=False)
    plot(frame)

    pd.set_option("display.width", 260)
    print("Warming removed per unit of electricity and per unit of river-bound heat\n")
    show = table[table["outcome"].eq("water_temperature") & table["spec"].eq("nearest_downstream")]
    print(show[["site", "event_year", "blocks_shut", "annual_net_twh", "heat_to_river_gw",
                "effect_removed", "per_twh", "per_gw_river_heat", "p_value",
                "interpretable"]].to_string(index=False))
    print("\n  interpretable = the distance analysis certified this as a real effect rather"
          "\n  than drift. A normalised value on a row that is not interpretable divides noise"
          "\n  by a very small denominator and should not be quoted.")

    oxygen = table[table["outcome"].eq("dissolved_oxygen") & table["spec"].eq("nearest_downstream")]
    if not oxygen.empty:
        print("\nDissolved oxygen (mg/l removed per unit)\n")
        print(oxygen[["site", "event_year", "annual_net_twh", "heat_to_river_gw",
                      "effect_removed", "per_twh", "per_gw_river_heat", "p_value",
                      "interpretable"]].to_string(index=False))

    print(f"\nWrote {OUT_DIR / 'effect_per_generation.csv'} "
          f"and {OUT_DIR / 'reactor_thermal_load.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
