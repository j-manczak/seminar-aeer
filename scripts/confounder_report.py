"""What else was heating these rivers, and did any of it change with the reactor?

A nuclear site is not the only heat source on its reach. This report lists, for
every site-event that the 2x2 can estimate, the other condensing thermal plants
on the same river inside the analysis radius, split into

* **between the gauges** — their heat lands in the *treated* reach, so a change
  there moves the same gap the nuclear shutdown moves;
* **above the control gauge** — they warm both gauges, which differences out
  unless they changed at the same time.

The verdict column is what matters: a plant is only a confounder if it started
up or shut down within a few years of the nuclear event. Stable neighbours are
harmless by construction, because the paired difference removes anything that
did not change.

The radius comes from scripts/distance_sensitivity.py, so the confounder search
and the effect estimate use the same along-river geometry.

    python scripts/confounder_report.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from pipeline import monitoring_stations, station_pairs, thermal_confounders
from pipeline.config import ANALYSIS_DIR

RADIUS_FILE = ANALYSIS_DIR / "plant_2x2" / "analysis_radius.json"
RESULTS = ANALYSIS_DIR / "plant_2x2" / "plant_2x2_results.csv"
OUT_PLANTS = ANALYSIS_DIR / "plant_2x2" / "thermal_plants_on_study_rivers.csv"
OUT_CONFOUNDERS = ANALYSIS_DIR / "plant_2x2" / "confounders_by_site_event.csv"

DEFAULT_RADIUS_KM = 50.0

# Plant and gauge coordinates are good to a few hundred metres, so a plant this
# close to a gauge is worth flagging even when the geometry places it just
# outside the measured reach.
NEAR_GAUGE_KM = 3.0


def analysis_radius() -> float:
    if RADIUS_FILE.exists():
        return float(json.loads(RADIUS_FILE.read_text(encoding="utf-8"))["radius_km"])
    print(f"confounder_report: {RADIUS_FILE.name} not found, using {DEFAULT_RADIUS_KM:.0f} km.")
    return DEFAULT_RADIUS_KM


def used_pairs() -> pd.DataFrame:
    """The gauge pairs the 2x2 actually used, with their river kilometres."""
    if not RESULTS.exists():
        raise FileNotFoundError(f"{RESULTS} not found — run scripts/plant_2x2_did.py first.")
    results = pd.read_csv(RESULTS)
    # Both reported pairs have to be screened, not just the headline one: the
    # best-covered pair often reaches much further downstream, and that is
    # exactly where another plant is most likely to sit.
    headline = results[
        results["spec"].isin(["nearest_downstream", "best_coverage"])
        & results["sample"].eq("all_year")
    ]

    stations = monitoring_stations.all_stations()
    gkd_names = stations.set_index("station_name")["river_km"].to_dict()

    rows = []
    for _, row in headline.drop_duplicates(
        ["site", "event_year", "outcome", "upstream_station", "downstream_station"]
    ).iterrows():
        up_km = gkd_names.get(row["upstream_station"])
        down_km = gkd_names.get(row["downstream_station"])
        site = next((s for s in station_pairs.plant_sites() if s.site == row["site"]), None)
        if site is None:
            continue
        # Fall back to the plant position plus the reported along-river distance
        # when a chemistry point is not in the shared station table.
        if up_km is None:
            up_km = site.river_km + float(row["upstream_km"])
        if down_km is None:
            down_km = site.river_km - float(row["downstream_km"])
        rows.append({
            "outcome": row["outcome"], "site": row["site"], "river": row["river"],
            "spec": row["spec"], "event_year": int(row["event_year"]),
            "site_river_km": site.river_km,
            "upstream_station": row["upstream_station"], "upstream_river_km": up_km,
            "downstream_station": row["downstream_station"], "downstream_river_km": down_km,
        })
    return pd.DataFrame(rows)


def main() -> int:
    radius = analysis_radius()
    plants = thermal_confounders.load_thermal_plants()
    OUT_PLANTS.parent.mkdir(parents=True, exist_ok=True)
    plants.round(3).to_csv(OUT_PLANTS, index=False)

    pairs = used_pairs()
    records = []
    for _, pair in pairs.iterrows():
        found = thermal_confounders.confounders_for_pair(
            plants, pair["river"], pair["upstream_river_km"], pair["downstream_river_km"],
            pair["event_year"], control_reach_km=radius, margin_km=NEAR_GAUGE_KM,
        )
        if found.empty:
            records.append({
                **{k: pair[k] for k in ("outcome", "spec", "site", "river", "event_year")},
                "upstream_station": pair["upstream_station"],
                "downstream_station": pair["downstream_station"],
                "plant": "", "energy_source": "", "capacity_net_bnetza": None,
                "reach": "none within the radius", "changed_near_event": "",
                "is_confounder": False, "active_at_event": None, "river_km": None,
                "near_a_gauge": False,
            })
            continue
        for _, plant in found.iterrows():
            records.append({
                **{k: pair[k] for k in ("outcome", "spec", "site", "river", "event_year")},
                "upstream_station": pair["upstream_station"],
                "downstream_station": pair["downstream_station"],
                "plant": plant["plant"], "city": plant.get("city"),
                "energy_source": plant["energy_source"],
                "capacity_net_bnetza": plant["capacity_net_bnetza"],
                "chp": plant.get("chp"),
                "river_km": plant["river_km"],
                "reach": plant["reach"],
                "commissioned_year": plant.get("commissioned_year"),
                "shutdown_year": plant.get("shutdown_year"),
                "changed_near_event": plant["changed_near_event"],
                "is_confounder": plant["is_confounder"],
                "active_at_event": plant["active_at_event"],
                "near_a_gauge": plant["near_a_gauge"],
            })

    table = pd.DataFrame(records)
    table.to_csv(OUT_CONFOUNDERS, index=False)

    pd.set_option("display.width", 260)
    pd.set_option("display.max_rows", 200)
    print(f"Other condensing thermal plants on the study rivers (radius {radius:.0f} km "
          f"along the channel)\n")
    show = table[table["plant"].ne("")][
        ["outcome", "site", "event_year", "downstream_station", "plant", "energy_source",
         "capacity_net_bnetza", "river_km", "reach", "changed_near_event", "is_confounder"]
    ]
    print(show.to_string(index=False) if not show.empty else "  none found")

    empty = table[table["plant"].eq("")]
    if not empty.empty:
        print("\nNo other thermal plant within the radius for:")
        for _, row in empty.drop_duplicates(["site", "event_year", "downstream_station"]).iterrows():
            print(f"  {row['site']} {row['event_year']} ({row['river']}) "
                  f"-> {row['downstream_station']}")

    near = table[table["near_a_gauge"].fillna(False)]
    if not near.empty:
        print(f"\nPlants sitting within {NEAR_GAUGE_KM:.0f} km of one of the gauges — worth a look "
              f"even when the geometry puts them outside the reach, because plant and gauge "
              f"coordinates are only accurate to a few hundred metres:")
        for _, row in near.drop_duplicates(["site", "event_year", "plant"]).iterrows():
            print(f"  {row['site']} {row['event_year']}: {row['plant']} at river-km "
                  f"{row['river_km']:.1f} ({row['reach'] or 'outside the reach'})")

    flagged = table[table["is_confounder"].fillna(False)]
    print(f"\nActual confounders (changed within "
          f"{thermal_confounders.CHANGE_WINDOW_YEARS} years of the nuclear event): "
          f"{flagged['plant'].nunique()}")
    for _, row in flagged.drop_duplicates(["site", "event_year", "plant"]).iterrows():
        print(f"  {row['site']} {row['event_year']}: {row['plant']} "
              f"({row['energy_source']}, {row['capacity_net_bnetza']:.0f} MW) "
              f"— {row['changed_near_event']}, {row['reach']}")

    print(f"\nWrote {OUT_CONFOUNDERS} and {OUT_PLANTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
