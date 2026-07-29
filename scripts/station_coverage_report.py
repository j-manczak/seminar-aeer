"""Per-site answer to: do we actually have an upstream *and* a downstream gauge?

Writes one row per nuclear site and shutdown event, listing the nearest usable
gauge on each side, whether the 2x2 is estimable, and if not, why.

    python scripts/station_coverage_report.py
    -> data/processed/analysis/station_coverage.csv  (+ a printed summary)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from pipeline import monitoring_stations, station_pairs
from pipeline.config import ANALYSIS_DIR
from pipeline.reactors import REACTORS

MAX_PAIR_KM = 120.0
OUT = ANALYSIS_DIR / "station_coverage.csv"

# A 2x2 needs readings on both sides of the shutdown, so the gauge has to have
# been running before it. Waterbase only starts in 2020.
PRE_EVENT_MARGIN_YEARS = 1


def heat_load(site: station_pairs.PlantSite, event_year: int) -> str:
    loads = {b.river_heat_load for b in site.blocks_at(event_year)}
    order = ["high", "moderate", "low", "unknown"]
    return min(loads, key=order.index) if loads else "unknown"


def cooling(site: station_pairs.PlantSite, event_year: int) -> str:
    return "/".join(sorted({b.cooling_type for b in site.blocks_at(event_year)}))


def main() -> int:
    stations = monitoring_stations.all_stations()
    pairs = station_pairs.candidate_pairs(stations, max_km=MAX_PAIR_KM)
    coverage = stations.set_index("station_id")

    rows = []
    for site in station_pairs.plant_sites():
        for event in site.events:
            record = {
                "site": site.site,
                "river": site.river,
                "event_year": event,
                "blocks_shut": ", ".join(b.reactor for b in site.blocks_at(event)),
                "cooling": cooling(site, event),
                "heat_to_river": heat_load(site, event),
                "capacity_lost_mw": site.capacity_lost_mw(event),
            }
            group = pairs[(pairs["site"] == site.site) & (pairs["event_year"] == event) & pairs["clean"]]

            for role in ("upstream", "downstream"):
                side = group[group["role"] == role].sort_values("distance_km")
                # Usable = has readings starting before the shutdown.
                usable = side[side["station_id"].map(
                    lambda sid: coverage.loc[sid, "year_min"] <= event - PRE_EVENT_MARGIN_YEARS
                    if sid in coverage.index else False
                )]
                record[f"{role}_n"] = len(side)
                record[f"{role}_usable_n"] = len(usable)
                if usable.empty:
                    record[f"{role}_station"] = ""
                    record[f"{role}_km"] = None
                    record[f"{role}_source"] = ""
                    record[f"{role}_from"] = None
                else:
                    best = usable.iloc[0]
                    meta = coverage.loc[best["station_id"]]
                    record[f"{role}_station"] = best["station_name"]
                    record[f"{role}_km"] = best["distance_km"]
                    record[f"{role}_source"] = meta["source"]
                    record[f"{role}_from"] = meta["year_min"]

            has_up = bool(record["upstream_station"])
            has_down = bool(record["downstream_station"])
            record["estimable_2x2"] = has_up and has_down
            if has_up and has_down:
                record["blocker"] = ""
            elif not has_up and not has_down:
                record["blocker"] = "no gauge on either side with data before the shutdown"
            elif not has_down:
                record["blocker"] = "no downstream gauge with data before the shutdown"
            else:
                record["blocker"] = "no upstream gauge with data before the shutdown"
            rows.append(record)

    frame = pd.DataFrame(rows).sort_values(["event_year", "site"]).reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT, index=False)

    pd.set_option("display.width", 300)
    pd.set_option("display.max_colwidth", 30)
    print("Do we have an upstream AND a downstream gauge per site and shutdown?\n")
    print(frame[["site", "river", "event_year", "cooling", "heat_to_river",
                 "upstream_station", "upstream_km", "downstream_station", "downstream_km",
                 "estimable_2x2", "blocker"]].to_string(index=False))
    print(f"\nEstimable: {int(frame['estimable_2x2'].sum())} of {len(frame)} site-events")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
