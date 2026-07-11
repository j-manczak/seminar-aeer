"""Locate each observation relative to the study reactors along its river.

A thermal plume only reaches monitoring points that are (a) on the *same* river
as the plant and (b) *downstream* of it, and it decays with distance. A plain
straight-line radius ignores both facts, so most sites it captures sit on other
rivers or upstream and cannot show an effect.

This module adds, for the outcome files (water temperature, dissolved oxygen)
and for discharge:

    study_river            the study river the site is on, or "" (off-river)
    position               downstream / upstream / off_river
    nearest_upstream_plant the study reactor just upstream of the site (or "")
    nearest_upstream_group that reactor's group
    along_river_km         approx. along-flow distance below that reactor (km)
    distance_band          0-10 / 10-25 / 25-50 / >50 (km downstream)
    downstream_of_shock    1 if downstream of a treatment/partial/staggered plant

Flow direction is approximated by a single downstream unit vector per river near
our reactors (see FLOW). This is a first-pass heuristic; for a final version it
should be replaced by true river kilometres from a river network (e.g.
HydroRIVERS). The along-flow sign (up- vs downstream) is robust; the exact
distance is approximate on curved reaches.
"""

import math
import re
from typing import Dict, List, Optional, Tuple

from pipeline.config import ANALYSIS_DIR
from pipeline.io_tables import read_rows, to_float, write_table
from pipeline.reactors import STUDY_REACTORS

# River tokens as they appear in Waterbase (German) and GRDC (English) names.
RIVER_KEYWORDS: Dict[str, set] = {
    "Rhine": {"RHEIN", "RHINE"},
    "Neckar": {"NECKAR"},
    "Main": {"MAIN"},
    "Danube": {"DONAU", "DANUBE"},
    "Isar": {"ISAR"},
    "Weser": {"WESER"},
    "Elbe": {"ELBE"},
    "Ems": {"EMS"},
}

# Prefixes German water-body names glue onto a river name (Tideelbe, Unterweser).
_PREFIXES = ("", "TIDE", "UNTER", "MITTEL", "OBER", "NIEDER", "AUSSEN")

# Approximate downstream unit vector (east, north) per river near our reactors.
FLOW: Dict[str, Tuple[float, float]] = {
    "Rhine": (0.0, 1.0),      # flows north (Philippsburg -> Biblis -> north)
    "Neckar": (-0.73, 0.68),  # flows NW toward Mannheim
    "Main": (-0.98, 0.17),    # flows west toward the Rhine
    "Danube": (0.92, 0.40),   # flows ENE
    "Isar": (0.89, 0.46),     # flows NE into the Danube
    "Weser": (-0.34, 0.94),   # flows north to the sea
    "Elbe": (-0.98, 0.17),    # flows NW to the sea (tidal near Brokdorf)
    "Ems": (-0.10, 0.99),     # flows north to the sea
}

_KM_PER_DEG_LAT = 110.574
_KM_PER_DEG_LON = 111.320


def river_of(name: str) -> Optional[str]:
    """Return the study river a water-body / GRDC river name refers to, else None."""
    tokens = [t for t in re.split(r"[^A-Za-z]+", name.upper()) if t]
    if "KANAL" in tokens:  # canals (e.g. MAIN-DONAU-KANAL) are not the river itself
        return None
    for river, keywords in RIVER_KEYWORDS.items():
        for keyword in keywords:
            if any(prefix + keyword in tokens for prefix in _PREFIXES):
                return river
    return None


def _along_flow_km(plant, lat: float, lon: float) -> float:
    """Signed along-flow distance from the plant to (lat, lon); + is downstream."""
    east_km = (lon - plant.longitude) * _KM_PER_DEG_LON * math.cos(math.radians(plant.latitude))
    north_km = (lat - plant.latitude) * _KM_PER_DEG_LAT
    unit_east, unit_north = FLOW[plant.river]
    return east_km * unit_east + north_km * unit_north


def _band(distance_km: float) -> str:
    if distance_km <= 10:
        return "0-10"
    if distance_km <= 25:
        return "10-25"
    if distance_km <= 50:
        return "25-50"
    return ">50"


def classify(lat: float, lon: float, river_name: str = "", river: Optional[str] = None) -> dict:
    """Position a monitoring point relative to the study reactors on its river.

    The river can be supplied directly (e.g. from a geometric match on the site
    coordinates); otherwise it is inferred from ``river_name``. A geometric match
    is more robust when the water-body name is missing or a placeholder.
    """
    empty = {
        "study_river": "",
        "position": "off_river",
        "nearest_upstream_plant": "",
        "nearest_upstream_group": "",
        "along_river_km": "",
        "distance_band": "",
        "downstream_of_shock": 0,
    }
    if river is None:
        river = river_of(river_name or "")
    if river is None:
        return empty

    # Plants on this river with the site downstream of them (positive along-flow).
    downstream = [
        (_along_flow_km(plant, lat, lon), plant)
        for plant in STUDY_REACTORS
        if plant.river == river
    ]
    downstream = [(distance, plant) for distance, plant in downstream if distance > 0]
    if not downstream:
        return {**empty, "study_river": river, "position": "upstream"}

    distance, plant = min(downstream, key=lambda item: item[0])
    is_shock = plant.group in {"treatment", "partial", "staggered_treatment"}
    return {
        "study_river": river,
        "position": "downstream",
        "nearest_upstream_plant": plant.reactor,
        "nearest_upstream_group": plant.group,
        "along_river_km": round(distance, 1),
        "distance_band": _band(distance),
        "downstream_of_shock": int(is_shock),
    }


_ADDED_FIELDS = [
    "study_river",
    "position",
    "nearest_upstream_plant",
    "nearest_upstream_group",
    "along_river_km",
    "distance_band",
    "downstream_of_shock",
]

# Files to enrich: (filename, column that holds the river/water-body name).
_TARGETS = [
    ("water_temperature_2006_2018.csv", "water_body_name"),
    ("dissolved_oxygen_2006_2018.csv", "water_body_name"),
    ("discharge_2006_2018.csv", "river"),
]


def _existing_header(path) -> List[str]:
    """Return the file's leading ``#`` comment lines (without the ``# ``)."""
    comments: List[str] = []
    with path.open(encoding="utf-8-sig") as handle:
        for line in handle:
            if not line.startswith("#"):
                break
            comments.append(line[1:].strip())
    return comments


_NOTE = [
    "River position added by river_position.py: each site is matched to its",
    "study river and classified upstream/downstream of the nearest reactor, with",
    "an approximate along-flow distance and distance band. Flow direction is a",
    "per-river heuristic (see the module); the up/down sign is robust, the distance",
    "is approximate. Filter on position=downstream for the plume-exposed sample;",
    "downstream_of_shock=1 marks sites below a 2011/staggered shutdown.",
]


def _enrich_file(filename: str, river_field: str) -> None:
    path = ANALYSIS_DIR / filename
    if not path.exists():
        print(f"river_position: {filename} not found, skipping.")
        return
    # Do not re-enrich a file that already carries the river-position columns.
    header = [line for line in _existing_header(path) if not line.startswith("River position added")]
    rows = read_rows(path)
    if not rows:
        return
    for row in rows:
        for field in _ADDED_FIELDS:
            row.pop(field, None)  # drop stale columns so a re-run stays clean
        lat = to_float(row.get("latitude"))
        lon = to_float(row.get("longitude"))
        if lat is None or lon is None:
            row.update({field: "" for field in _ADDED_FIELDS})
            row["downstream_of_shock"] = 0
            continue
        row.update(classify(lat, lon, row.get(river_field, "")))

    fieldnames = list(rows[0].keys())
    write_table(path, header + _NOTE, fieldnames, rows)
    print(f"river_position: enriched {filename} ({len(rows)} rows)")


def build() -> None:
    for filename, river_field in _TARGETS:
        _enrich_file(filename, river_field)


if __name__ == "__main__":
    build()
