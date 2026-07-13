"""Shared geometry and data for the study maps (static PNG and interactive HTML).

Pulls the Germany outline and the eight study-river centre-lines from Natural
Earth, and assembles the reactor sites and the *used* monitoring sites (those on
a study river) from the project data, so both maps show exactly the same thing.
"""

import csv
import json
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from pipeline.reactors import REACTORS
from pipeline.river_position import FLOW, river_of

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "processed" / "analysis"

# Clip everything to a generous box around Germany.
BBOX = (5.3, 46.8, 15.7, 55.5)  # lon_min, lat_min, lon_max, lat_max

_OUTLINE_URLS = [
    "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/1_deutschland/4_niedrig.geo.json",
    "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/master/1_deutschland/4_niedrig.geo.json",
]
_RIVER_URLS = [
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_rivers_lake_centerlines.geojson",
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_rivers_europe.geojson",
]

# Study river -> lowercase name variants used in Natural Earth.
RIVER_NAMES = {
    "Rhine": {"rhine", "rhein"},
    "Danube": {"danube", "donau"},
    "Elbe": {"elbe"},
    "Weser": {"weser"},
    "Ems": {"ems"},
    "Main": {"main"},
    "Neckar": {"neckar"},
    "Isar": {"isar"},
}

# Group order for picking a site's headline group (most-treated first).
GROUP_PRIORITY = ["treatment", "partial", "staggered_treatment", "control", "excluded"]
USED_POSITIONS = {"downstream", "upstream"}  # "used" = on a study river


def _get(url: str, timeout: int = 60) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "seminar-aeer/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _in_bbox(lon: float, lat: float) -> bool:
    return BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]


def germany_outline() -> List[List[List[float]]]:
    """List of rings, each a list of [lon, lat]."""
    for url in _OUTLINE_URLS:
        try:
            data = json.loads(_get(url).decode("utf-8"))
        except Exception as error:
            print(f"  outline failed ({url}): {error}")
            continue
        rings: List[List[List[float]]] = []
        for feature in data.get("features", [data]):
            geometry = feature.get("geometry", feature)
            if geometry["type"] == "Polygon":
                rings.append(geometry["coordinates"][0])
            elif geometry["type"] == "MultiPolygon":
                rings.extend(part[0] for part in geometry["coordinates"])
        if rings:
            return rings
    return []


def _match_river(properties: dict):
    names = {(properties.get(k) or "").strip().lower() for k in ("name", "name_en", "name_de", "rivername")}
    for river, variants in RIVER_NAMES.items():
        if names & variants:
            return river
    return None


def _clip_and_simplify(line: List[List[float]]) -> List[List[List[float]]]:
    """Split a polyline at the bounding box and round coordinates to ~100 m."""
    segments: List[List[List[float]]] = []
    current: List[List[float]] = []
    for lon, lat in line:
        if _in_bbox(lon, lat):
            point = [round(lon, 3), round(lat, 3)]
            if not current or current[-1] != point:
                current.append(point)
        elif current:
            segments.append(current)
            current = []
    if current:
        segments.append(current)
    return [s for s in segments if len(s) >= 2]


def study_rivers() -> Dict[str, List[List[List[float]]]]:
    """Study river -> list of polylines (each a list of [lon, lat])."""
    rivers: Dict[str, List[List[List[float]]]] = {name: [] for name in RIVER_NAMES}
    for url in _RIVER_URLS:
        try:
            data = json.loads(_get(url).decode("utf-8"))
        except Exception as error:
            print(f"  rivers failed ({url}): {error}")
            continue
        for feature in data["features"]:
            river = _match_river(feature.get("properties", {}))
            if not river:
                continue
            geometry = feature["geometry"]
            lines = (
                geometry["coordinates"]
                if geometry["type"] == "MultiLineString"
                else [geometry["coordinates"]]
            )
            for line in lines:
                rivers[river].extend(_clip_and_simplify(line))
    return rivers


def river_matcher(threshold_km: float = 2.5):
    """Return a function mapping (lat, lon) -> study river within threshold_km of
    its centre-line, or None. Coordinate-based, so it is robust to missing or
    placeholder water-body names in the source data."""
    from pipeline.geo import haversine_km
    rivers = study_rivers()
    points = {r: [(lat, lon) for line in lines for lon, lat in line] for r, lines in rivers.items()}

    def match(lat: float, lon: float):
        best, best_d = None, threshold_km
        for river, pts in points.items():
            for plat, plon in pts:
                d = haversine_km(lat, lon, plat, plon)
                if d < best_d:
                    best_d, best = d, river
        return best

    return match


def _site_short_name(reactor_name: str) -> str:
    import re
    return re.sub(r"\s+(A|B|C|1|2|I|II)$", "", reactor_name)


def study_sites() -> List[dict]:
    """Reactors aggregated to physical sites, with block detail for tooltips."""
    grouped = defaultdict(list)
    for reactor in REACTORS:
        grouped[_site_short_name(reactor.reactor)].append(reactor)
    sites = []
    for name, blocks in grouped.items():
        group = min((b.group for b in blocks), key=GROUP_PRIORITY.index)
        sites.append(
            {
                "name": name,
                "lat": sum(b.latitude for b in blocks) / len(blocks),
                "lon": sum(b.longitude for b in blocks) / len(blocks),
                "group": group,
                "river": blocks[0].river,
                "flow": FLOW.get(blocks[0].river),
                "blocks": [
                    {"block": b.reactor, "group": b.group, "shutdown": b.shutdown_year,
                     "cooling": b.cooling_type}
                    for b in blocks
                ],
            }
        )
    return sites


def _read(path: Path) -> List[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(line for line in handle if not line.startswith("#")))


def used_water_sites() -> List[dict]:
    """On-river water-quality sites with temperature/oxygen usage summarised."""
    def summarise(rows, sid):
        subset = [r for r in rows if r["site_id"] == sid and r.get("mean_value") not in (None, "")]
        years = sorted({int(r["year"]) for r in subset})
        values = [float(r["mean_value"]) for r in subset]
        if not subset:
            return None
        return {
            "years": len(years),
            "year_min": years[0],
            "year_max": years[-1],
            "mean_min": round(min(values), 2),
            "mean_max": round(max(values), 2),
        }

    temp_rows = _read(ANALYSIS / "water_temperature_2006_2018.csv")
    oxy_rows = _read(ANALYSIS / "dissolved_oxygen_2006_2018.csv")
    by_id = {}
    for row in temp_rows + oxy_rows:
        if row.get("position") in USED_POSITIONS:
            by_id.setdefault(row["site_id"], row)

    sites = []
    for sid, row in by_id.items():
        try:
            lat, lon = float(row["latitude"]), float(row["longitude"])
        except (TypeError, ValueError):
            continue
        sites.append(
            {
                "id": sid,
                "name": row.get("site_name", ""),
                "water_body": row.get("water_body_name", ""),
                "lat": lat,
                "lon": lon,
                "river": row.get("study_river", ""),
                "position": row.get("position", ""),
                "plant": row.get("nearest_upstream_plant", ""),
                "group": row.get("nearest_upstream_group", ""),
                "along_km": row.get("along_river_km", ""),
                "band": row.get("distance_band", ""),
                "shock": row.get("downstream_of_shock", "0") == "1",
                "temperature": summarise(temp_rows, sid),
                "oxygen": summarise(oxy_rows, sid),
            }
        )
    return sites


def used_discharge_sites() -> List[dict]:
    """On-river discharge gauges with a short usage summary."""
    rows = _read(ANALYSIS / "discharge_2006_2018.csv")
    by_id = defaultdict(list)
    for row in rows:
        if row.get("position") in USED_POSITIONS:
            by_id[row["grdc_no"]].append(row)
    gauges = []
    for gid, group in by_id.items():
        first = group[0]
        try:
            lat, lon = float(first["latitude"]), float(first["longitude"])
        except (TypeError, ValueError):
            continue
        years = sorted({int(r["year"]) for r in group})
        means = [float(r["discharge_mean_m3_s"]) for r in group if r.get("discharge_mean_m3_s")]
        gauges.append(
            {
                "id": gid,
                "name": first.get("station", ""),
                "lat": lat,
                "lon": lon,
                "river": first.get("study_river", ""),
                "position": first.get("position", ""),
                "plant": first.get("nearest_upstream_plant", ""),
                "band": first.get("distance_band", ""),
                "years": len(years),
                "year_min": years[0] if years else "",
                "year_max": years[-1] if years else "",
                "q_min": round(min(means), 1) if means else "",
                "q_max": round(max(means), 1) if means else "",
            }
        )
    return gauges
