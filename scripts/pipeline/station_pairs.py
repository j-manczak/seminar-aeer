"""Match each nuclear *site* to upstream (control) and downstream (treated) gauges.

This replaces the pairing logic that produced the empty 2x2 cells. Three things
were wrong with it and are fixed here.

1. **Sister blocks cancelled each other out.** Downstream stations were attached
   to the "nearest upstream reactor", and blocks that share a site share exact
   coordinates, so a tie was broken arbitrarily: Biblis A took every downstream
   station and Biblis B got none, likewise Philippsburg 2, Neckarwestheim 2,
   Isar 2 and Gundremmingen C. The unit here is the **site**, which is also the
   right physical unit — the river responds to the site's total cooling load.

2. **Position came from a straight-line projection.** Up/downstream and distance
   were computed by projecting onto one fixed direction vector per river, which
   is unreliable on a meandering reach. Here both come from true along-channel
   river kilometres (see :mod:`pipeline.river_network`).

3. **Controls were not screened for contamination.** An upstream gauge is only a
   valid control if *its* water was not disturbed by a different plant changing
   load at the same time; a downstream gauge is only clean if no other plant
   changed in between. Both are checked explicitly.

The output is a tidy table of candidate (site, event, station, role) rows that
the estimation step consumes.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from pipeline import river_network
from pipeline.reactors import REACTORS, Reactor

# A neighbouring plant that changes load within this many years of the focal
# event contaminates any gauge that sits between the two.
CONTAMINATION_WINDOW_YEARS = 2


@dataclass(frozen=True)
class PlantSite:
    """A physical nuclear site: one or more blocks sharing a location."""

    site: str
    river: str
    latitude: float
    longitude: float
    river_km: float
    blocks: tuple

    @property
    def events(self) -> List[int]:
        """Years in which this site lost cooling load, earliest first."""
        return sorted({b.shutdown_year for b in self.blocks if b.shutdown_year})

    def blocks_at(self, year: int) -> List[Reactor]:
        return [b for b in self.blocks if b.shutdown_year == year]

    def capacity_lost_mw(self, year: int) -> float:
        return float(sum(CAPACITY_MW.get(b.reactor, 0.0) for b in self.blocks_at(year)))

    def capacity_total_mw(self) -> float:
        return float(sum(CAPACITY_MW.get(b.reactor, 0.0) for b in self.blocks))


# Net electrical capacity (MW) per block, from the reactor master data. Kept
# here so the share of a site's load removed by an event can be reported.
CAPACITY_MW: Dict[str, float] = {
    "Biblis A": 1167, "Biblis B": 1240, "Unterweser": 1345,
    "Isar 1": 878, "Isar 2": 1410, "Neckarwestheim 1": 785, "Neckarwestheim 2": 1310,
    "Philippsburg 1": 890, "Philippsburg 2": 1402, "Grohnde": 1360,
    "Emsland": 1336, "Brokdorf": 1410, "Grafenrheinfeld": 1275,
    "Gundremmingen B": 1284, "Gundremmingen C": 1288,
    "Krümmel": 1346, "Brunsbüttel": 771,
}

SITE_NAMES: Dict[str, str] = {
    "Biblis A": "Biblis", "Biblis B": "Biblis",
    "Isar 1": "Isar", "Isar 2": "Isar",
    "Neckarwestheim 1": "Neckarwestheim", "Neckarwestheim 2": "Neckarwestheim",
    "Philippsburg 1": "Philippsburg", "Philippsburg 2": "Philippsburg",
    "Gundremmingen B": "Gundremmingen", "Gundremmingen C": "Gundremmingen",
}


def plant_sites(include_excluded: bool = False) -> List[PlantSite]:
    """Group the reactor master table into physical sites, placed on their river."""
    grouped: Dict[str, List[Reactor]] = {}
    for reactor in REACTORS:
        if reactor.group == "excluded" and not include_excluded:
            continue
        grouped.setdefault(SITE_NAMES.get(reactor.reactor, reactor.reactor), []).append(reactor)

    sites: List[PlantSite] = []
    for name, blocks in grouped.items():
        latitude = sum(b.latitude for b in blocks) / len(blocks)
        longitude = sum(b.longitude for b in blocks) / len(blocks)
        found = river_network.locate(latitude, longitude, max_offset_m=5000.0)
        if found is None:
            print(f"station_pairs: {name} could not be placed on a study river; skipped.")
            continue
        sites.append(
            PlantSite(
                site=name, river=found["river"], latitude=latitude, longitude=longitude,
                river_km=found["river_km"], blocks=tuple(blocks),
            )
        )
    return sorted(sites, key=lambda s: (s.river, -s.river_km))


def _other_sites_between(focal: PlantSite, km_low: float, km_high: float,
                         event_year: int, sites: Iterable[PlantSite]) -> List[str]:
    """Sites on the same river inside a km interval that also changed load nearby in time."""
    offenders = []
    for other in sites:
        if other.site == focal.site or other.river != focal.river:
            continue
        if not (km_low < other.river_km < km_high):
            continue
        if any(abs(year - event_year) <= CONTAMINATION_WINDOW_YEARS for year in other.events):
            offenders.append(other.site)
    return offenders


def candidate_pairs(stations: pd.DataFrame, max_km: float = 120.0,
                    site_filter: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """Rank upstream/downstream gauges for every site and shutdown event.

    ``stations`` needs ``station_id``, ``station_name``, ``river`` and
    ``river_km`` (as produced by :func:`pipeline.river_network.locate_frame`).
    The result has one row per (site, event, station) candidate with its role,
    along-river distance and a contamination flag.
    """
    required = {"station_id", "station_name", "river", "river_km"}
    missing = required - set(stations.columns)
    if missing:
        raise ValueError(f"stations table is missing columns: {sorted(missing)}")

    sites = plant_sites()
    if site_filter is not None:
        wanted = set(site_filter)
        sites = [s for s in sites if s.site in wanted]

    rows: List[dict] = []
    for site in sites:
        on_river = stations[stations["river"] == site.river]
        for event in site.events:
            for _, station in on_river.iterrows():
                delta = station["river_km"] - site.river_km
                distance = abs(delta)
                if distance > max_km:
                    continue
                # river_km counts from the mouth, so a *smaller* value is downstream.
                role = "upstream" if delta > 0 else "downstream"
                if role == "upstream":
                    contaminants = _other_sites_between(
                        site, site.river_km, station["river_km"], event, plant_sites())
                else:
                    contaminants = _other_sites_between(
                        site, station["river_km"], site.river_km, event, plant_sites())

                rows.append({
                    "site": site.site,
                    "river": site.river,
                    "site_river_km": round(site.river_km, 2),
                    "event_year": event,
                    "blocks_shut": ", ".join(b.reactor for b in site.blocks_at(event)),
                    "capacity_lost_mw": site.capacity_lost_mw(event),
                    "capacity_share_lost": round(
                        site.capacity_lost_mw(event) / site.capacity_total_mw(), 3
                    ) if site.capacity_total_mw() else None,
                    "station_id": station["station_id"],
                    "station_name": station["station_name"],
                    "station_river_km": round(float(station["river_km"]), 2),
                    "role": role,
                    "distance_km": round(distance, 2),
                    "contaminated_by": ", ".join(contaminants),
                    "clean": not contaminants,
                })

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values(["river", "site", "event_year", "role", "distance_km"]).reset_index(drop=True)


def best_pair(pairs: pd.DataFrame, site: str, event_year: int,
              clean_only: bool = True) -> Optional[dict]:
    """The closest clean upstream and downstream gauge for one site-event."""
    subset = pairs[(pairs["site"] == site) & (pairs["event_year"] == event_year)]
    if clean_only:
        subset = subset[subset["clean"]]
    chosen = {}
    for role in ("upstream", "downstream"):
        side = subset[subset["role"] == role].sort_values("distance_km")
        if side.empty:
            return None
        chosen[role] = side.iloc[0].to_dict()
    return chosen


def main() -> int:
    print("Nuclear sites placed on the real river network\n")
    for site in plant_sites():
        events = ", ".join(str(y) for y in site.events) or "-"
        print(f"  {site.site:16s} {site.river:8s} river-km {site.river_km:7.1f}  "
              f"blocks: {len(site.blocks)}  shutdowns: {events}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
