"""Real river geometry and true along-river chainage for the study rivers.

Replaces the fixed per-river direction vector in ``river_position.py``. That
heuristic projected a straight line onto one unit vector per river, which is
wrong wherever a river meanders (Main, Neckar, Isar) and can even flip the
upstream/downstream sign near a bend.

Here the geometry is real:

* **HydroRIVERS v1.0 (Europe)** supplies the river network *with flow topology*
  (``NEXT_DOWN`` links every reach to the one below it), so "downstream" is read
  off the network rather than guessed.
* Each study river's main stem is grown from a seed point: walk down via
  ``NEXT_DOWN`` to the mouth, and up by repeatedly taking the tributary with the
  largest upstream catchment (``UPLAND_SKM``), which is the main stem by
  definition.
* HydroRIVERS ends at the tidal limit, so the lower Elbe (Brokdorf) and lower
  Weser (Unterweser) are missing. Those two reaches are appended from
  **OpenStreetMap** waterway geometry, fetched via Overpass.

A point is then placed on a river by projecting it onto that stem in a metric
CRS (EPSG:25832, UTM 32N), which yields

    river_km   distance from the river mouth along the channel; larger = further
               upstream, so ``river_km(plant) - river_km(site)`` is the true
               along-flow distance and its sign gives up/downstream.

Downloaded inputs are cached under ``data/raw/rivers/`` so the network is
fetched once.

    python scripts/pipeline/river_network.py     # build + print a summary
"""

from __future__ import annotations

import json
import sys
import urllib.request
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Point
from shapely.ops import linemerge

from pipeline.config import RAW_DIR

RIVER_DIR = RAW_DIR / "rivers"
HYDRORIVERS_ZIP_URL = "https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_eu_shp.zip"
HYDRORIVERS_SHP = RIVER_DIR / "HydroRIVERS_v10_eu_shp" / "HydroRIVERS_v10_eu.shp"
OSM_CACHE = RIVER_DIR / "osm_tidal_reaches.geojson"
STEM_CACHE = RIVER_DIR / "study_river_stems.geojson"

# Metric CRS for Germany; all distances below are metres in this projection.
METRIC_CRS = 25832
GEO_CRS = 4326

BBOX = (5.3, 46.8, 15.7, 55.5)  # lon_min, lat_min, lon_max, lat_max

# Seed points sit unambiguously on the main stem, away from confluences, so the
# "largest catchment nearby" rule cannot latch onto a tributary.
SEEDS: Dict[str, Tuple[float, float]] = {
    "Rhine": (49.4875, 8.4650),      # Rhine at Mannheim
    "Neckar": (49.1427, 9.2109),     # Neckar at Heilbronn
    "Main": (49.7925, 9.9300),       # Main at Würzburg
    "Danube": (49.0170, 12.0980),    # Danube at Regensburg
    "Isar": (48.5370, 12.1510),      # Isar at Landshut
    "Weser": (52.2870, 8.9130),      # Weser at Minden
    "Elbe": (53.1400, 10.4000),      # Elbe at Bleckede (above the tidal limit)
    "Ems": (52.5200, 7.3200),        # Ems at Lingen
}

# A tributary stem must stop where it joins a bigger river, otherwise the Neckar
# "continues" down the Rhine and every Rhine site would sit on both stems. The
# three tributary study rivers get their confluence stated explicitly rather than
# inferred, because catchment-ratio rules misfire where a tributary rivals its
# receiving river (the Aller is nearly as large as the Weser it joins).
# Rivers absent here run on to the sea (or, for the Danube, to the study bbox).
MOUTHS: Dict[str, Tuple[float, float]] = {
    "Neckar": (49.4260, 8.4740),   # into the Rhine at Mannheim
    "Main": (50.0047, 8.2947),     # into the Rhine at Mainz-Kostheim
    "Isar": (48.8180, 12.9760),    # into the Danube near Deggendorf
}

# Published main-stem lengths (km) used as a build-time sanity check.
EXPECTED_LENGTH_KM: Dict[str, float] = {
    "Neckar": 362.0, "Main": 527.0, "Isar": 295.0, "Ems": 371.0,
}

# Rivers whose lower course is tidal and therefore absent from HydroRIVERS.
# The Overpass query pulls the OSM waterway relation for the named river inside
# the bounding box and keeps the part seaward of the HydroRIVERS terminus.
TIDAL_RIVERS = {
    "Elbe": {"osm_name": "Elbe", "bbox": (53.30, 8.55, 53.95, 10.10)},
    "Weser": {"osm_name": "Weser", "bbox": (53.10, 8.20, 53.90, 8.70)},
}

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]


# --------------------------------------------------------------------------
# inputs
# --------------------------------------------------------------------------
def ensure_hydrorivers() -> Path:
    """Download and unpack HydroRIVERS Europe on first use."""
    if HYDRORIVERS_SHP.exists():
        return HYDRORIVERS_SHP
    import zipfile

    RIVER_DIR.mkdir(parents=True, exist_ok=True)
    archive = RIVER_DIR / "HydroRIVERS_v10_eu_shp.zip"
    if not archive.exists():
        print(f"river_network: downloading {HYDRORIVERS_ZIP_URL} ...", flush=True)
        request = urllib.request.Request(
            HYDRORIVERS_ZIP_URL, headers={"User-Agent": "seminar-aeer/1.0"}
        )
        with urllib.request.urlopen(request, timeout=900) as response, archive.open("wb") as handle:
            handle.write(response.read())
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(RIVER_DIR)
    return HYDRORIVERS_SHP


def _overpass(query: str) -> dict:
    """POST an Overpass QL query, trying the public mirrors in turn."""
    import requests

    last_error: Optional[Exception] = None
    for url in OVERPASS_URLS:
        try:
            response = requests.post(
                url, data={"data": query}, timeout=300,
                headers={"User-Agent": "seminar-aeer/1.0"},
            )
            response.raise_for_status()
            return response.json()
        except Exception as error:  # mirror down, rate-limited, or TLS trouble
            print(f"river_network: Overpass mirror failed ({url}): {error}")
            last_error = error
    raise RuntimeError(f"All Overpass mirrors failed: {last_error}")


def fetch_tidal_reaches() -> Dict[str, LineString]:
    """Return river -> merged OSM centre-line for the tidal lower course."""
    if OSM_CACHE.exists():
        gdf = gpd.read_file(OSM_CACHE)
        return {row.river: row.geometry for row in gdf.itertuples()}

    RIVER_DIR.mkdir(parents=True, exist_ok=True)
    records = []
    for river, spec in TIDAL_RIVERS.items():
        south, west, north, east = spec["bbox"]
        query = f"""
        [out:json][timeout:240];
        way["waterway"="river"]["name"="{spec['osm_name']}"]({south},{west},{north},{east});
        out geom;
        """
        print(f"river_network: Overpass query for tidal {river} ...", flush=True)
        try:
            payload = _overpass(query)
        except RuntimeError as error:
            # Without the tidal extension the stem simply ends at the tidal
            # limit; Brokdorf and Unterweser then fall outside it, which the
            # caller reports rather than silently mislocating them.
            print(f"river_network: skipping tidal {river}: {error}")
            continue
        lines = [
            LineString([(p["lon"], p["lat"]) for p in element["geometry"]])
            for element in payload.get("elements", [])
            if len(element.get("geometry", [])) >= 2
        ]
        if not lines:
            print(f"river_network: no OSM geometry for tidal {river}")
            continue
        merged = linemerge(lines)
        records.append({"river": river, "geometry": merged})

    gdf = gpd.GeoDataFrame(records, crs=GEO_CRS)
    gdf.to_file(OSM_CACHE, driver="GeoJSON")
    return {row.river: row.geometry for row in gdf.itertuples()}


# --------------------------------------------------------------------------
# main-stem construction
# --------------------------------------------------------------------------
def _seed_reach(reaches: gpd.GeoDataFrame, lat: float, lon: float, radius_m: float = 8000.0):
    """Index of the largest-catchment reach within ``radius_m`` of a seed point."""
    point = gpd.GeoSeries([Point(lon, lat)], crs=GEO_CRS).to_crs(METRIC_CRS).iloc[0]
    distance = reaches.distance(point)
    nearby = reaches[distance < radius_m]
    if nearby.empty:
        raise ValueError(f"No river reach within {radius_m/1000:.0f} km of ({lat}, {lon}).")
    return nearby["UPLAND_SKM"].idxmax()


def _trim_at_mouth(reaches: gpd.GeoDataFrame, order: List[int], mouth: Tuple[float, float]) -> List[int]:
    """Cut an ordered stem at the reach closest to a declared confluence point.

    Snapping the confluence to "the biggest reach nearby" would pick the
    *receiving* river (the Rhine is within a few hundred metres of the Neckar's
    mouth), so the cut is made on the chain itself instead.
    """
    lat, lon = mouth
    point = gpd.GeoSeries([Point(lon, lat)], crs=GEO_CRS).to_crs(METRIC_CRS).iloc[0]
    distances = [reaches.geometry.loc[index].distance(point) for index in order]
    cut = int(np.argmin(distances))
    return order[: cut + 1]


def _stem_reach_ids(reaches: gpd.GeoDataFrame, seed_index) -> List[int]:
    """Reach ids from the headwater down to the mouth, through the seed reach."""
    by_id = {int(r): i for i, r in reaches["HYRIV_ID"].items()}
    next_down = reaches["NEXT_DOWN"].astype(int)
    upland = reaches["UPLAND_SKM"]

    # Children: every reach that flows into a given reach.
    parents: Dict[int, List[int]] = {}
    for index, target in next_down.items():
        if target:
            parents.setdefault(int(target), []).append(index)

    # Downstream from the seed, following the single outflow link.
    downstream: List[int] = []
    cursor = seed_index
    seen = {seed_index}
    while True:
        target = int(next_down.loc[cursor])
        if not target or target not in by_id:
            break
        cursor = by_id[target]
        if cursor in seen:
            break
        seen.add(cursor)
        downstream.append(cursor)

    # Upstream from the seed, always taking the largest contributing branch.
    upstream: List[int] = []
    cursor = seed_index
    while True:
        candidates = [i for i in parents.get(int(reaches["HYRIV_ID"].loc[cursor]), []) if i not in seen]
        if not candidates:
            break
        cursor = max(candidates, key=lambda i: upland.loc[i])
        seen.add(cursor)
        upstream.append(cursor)

    return list(reversed(upstream)) + [seed_index] + downstream


def _oriented_coords(geometry: LineString, previous_end: Optional[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Coordinates of ``geometry``, flipped if that better continues the stem."""
    coords = list(geometry.coords)
    if previous_end is None:
        return coords
    start, end = coords[0], coords[-1]
    d_start = (start[0] - previous_end[0]) ** 2 + (start[1] - previous_end[1]) ** 2
    d_end = (end[0] - previous_end[0]) ** 2 + (end[1] - previous_end[1]) ** 2
    return coords if d_start <= d_end else coords[::-1]


def _stem_line(reaches: gpd.GeoDataFrame, order: List[int]) -> LineString:
    """Stitch ordered reaches into one source-to-mouth line (metric CRS)."""
    coords: List[Tuple[float, float]] = []
    for index in order:
        piece = _oriented_coords(reaches.geometry.loc[index], coords[-1] if coords else None)
        if coords and piece and coords[-1] == piece[0]:
            piece = piece[1:]
        coords.extend(piece)
    return LineString(coords)


def _append_tidal(stem: LineString, tidal: LineString) -> LineString:
    """Extend a source-to-mouth stem with its tidal continuation."""
    tidal_metric = gpd.GeoSeries([tidal], crs=GEO_CRS).to_crs(METRIC_CRS).iloc[0]
    if tidal_metric.geom_type == "MultiLineString":
        parts = sorted(tidal_metric.geoms, key=lambda p: p.length, reverse=True)
        tidal_metric = parts[0]
    stem_end = stem.coords[-1]
    coords = _oriented_coords(tidal_metric, stem_end)
    # Keep only the part seaward of where the stem currently ends.
    start_gap = Point(coords[0]).distance(Point(stem_end))
    if start_gap > 30_000:  # unrelated geometry; leave the stem untouched
        return stem
    return LineString(list(stem.coords) + list(coords))


@dataclass(frozen=True)
class RiverStem:
    """One study river's source-to-mouth centre-line in the metric CRS."""

    river: str
    line: LineString

    @property
    def length_km(self) -> float:
        return self.line.length / 1000.0

    def river_km(self, point: Point) -> float:
        """Distance from the mouth, in km (larger = further upstream)."""
        along_from_source = self.line.project(point)
        return (self.line.length - along_from_source) / 1000.0

    def offset_m(self, point: Point) -> float:
        """Perpendicular distance from the centre-line, in metres."""
        return self.line.distance(point)


@lru_cache(maxsize=1)
def study_river_stems() -> Dict[str, RiverStem]:
    """Build (and cache on disk) the main stem of every study river."""
    if STEM_CACHE.exists():
        gdf = gpd.read_file(STEM_CACHE).to_crs(METRIC_CRS)
        return {row.river: RiverStem(row.river, row.geometry) for row in gdf.itertuples()}

    shp = ensure_hydrorivers()
    print("river_network: loading HydroRIVERS ...", flush=True)
    reaches = gpd.read_file(shp, bbox=BBOX, engine="pyogrio").to_crs(METRIC_CRS)

    tidal = fetch_tidal_reaches()
    stems: Dict[str, RiverStem] = {}
    for river, (lat, lon) in SEEDS.items():
        seed = _seed_reach(reaches, lat, lon)
        order = _stem_reach_ids(reaches, seed)
        if river in MOUTHS:
            order = _trim_at_mouth(reaches, order, MOUTHS[river])
        line = _stem_line(reaches, order)
        if river in tidal:
            line = _append_tidal(line, tidal[river])
        stems[river] = RiverStem(river, line)

        length_km = line.length / 1000.0
        expected = EXPECTED_LENGTH_KM.get(river)
        check = f"  (published {expected:.0f} km)" if expected else ""
        print(f"river_network: {river:8s} {len(order):4d} reaches, {length_km:7.1f} km{check}", flush=True)

    RIVER_DIR.mkdir(parents=True, exist_ok=True)
    gpd.GeoDataFrame(
        [{"river": s.river, "geometry": s.line} for s in stems.values()], crs=METRIC_CRS
    ).to_crs(GEO_CRS).to_file(STEM_CACHE, driver="GeoJSON")
    return stems


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------
def locate(lat: float, lon: float, max_offset_m: float = 2500.0) -> Optional[dict]:
    """Place a point on the nearest study river.

    Returns ``{"river", "river_km", "offset_m"}`` for the closest stem within
    ``max_offset_m``, else ``None``. ``river_km`` counts from the river mouth,
    so it decreases downstream.
    """
    point = gpd.GeoSeries([Point(lon, lat)], crs=GEO_CRS).to_crs(METRIC_CRS).iloc[0]
    best = None
    for stem in study_river_stems().values():
        offset = stem.offset_m(point)
        if offset <= max_offset_m and (best is None or offset < best["offset_m"]):
            best = {"river": stem.river, "river_km": stem.river_km(point), "offset_m": offset}
    return best


def locate_frame(frame: pd.DataFrame, lat_col: str = "latitude", lon_col: str = "longitude",
                 max_offset_m: float = 2500.0) -> pd.DataFrame:
    """Vectorised :func:`locate` for a whole table; adds river/river_km/offset_m."""
    points = gpd.GeoSeries(
        gpd.points_from_xy(frame[lon_col], frame[lat_col]), index=frame.index, crs=GEO_CRS
    ).to_crs(METRIC_CRS)

    river = pd.Series(pd.NA, index=frame.index, dtype="object")
    river_km = pd.Series(np.nan, index=frame.index)
    offset_m = pd.Series(np.inf, index=frame.index)

    for stem in study_river_stems().values():
        distance = points.distance(stem.line)
        better = distance < offset_m
        if not better.any():
            continue
        along = points[better].apply(stem.line.project)
        river.loc[better] = stem.river
        river_km.loc[better] = (stem.line.length - along) / 1000.0
        offset_m.loc[better] = distance[better]

    too_far = offset_m > max_offset_m
    river.loc[too_far] = pd.NA
    river_km.loc[too_far] = np.nan

    out = frame.copy()
    out["river"] = river
    out["river_km"] = river_km
    out["offset_m"] = offset_m.replace(np.inf, np.nan)
    return out


def main() -> int:
    stems = study_river_stems()
    print("\nStudy river stems (HydroRIVERS + OSM tidal reaches)")
    for river, stem in stems.items():
        print(f"  {river:8s} {stem.length_km:8.1f} km")

    from pipeline.reactors import STUDY_REACTORS

    print("\nReactor positions on their river")
    for reactor in STUDY_REACTORS:
        found = locate(reactor.latitude, reactor.longitude, max_offset_m=5000.0)
        if found is None:
            print(f"  {reactor.reactor:18s} NOT ON ANY STEM")
            continue
        flag = "" if found["river"] == reactor.river else f"  <-- expected {reactor.river}"
        print(
            f"  {reactor.reactor:18s} {found['river']:8s} km {found['river_km']:7.1f} "
            f"(offset {found['offset_m']:5.0f} m){flag}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
