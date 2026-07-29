"""Germany's national border for the study maps.

The maps show rivers that run well past the border (the Rhine into the
Netherlands, the Danube into Austria), so without an outline it is hard to see
which reach is actually in the sample. This module fetches the national boundary
once and caches it, so the maps do not depend on network access after the first
run.

Source: `deutschlandGeoJSON <https://github.com/isellsoap/deutschlandGeoJSON>`_
(public-domain boundaries derived from official Bundesamt für Kartographie und
Geodäsie data). The medium resolution is plenty for a country-scale map and
keeps the cached file small enough to commit.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from functools import lru_cache
from pathlib import Path
from typing import List

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.config import RAW_DIR

BORDER_DIR = RAW_DIR / "borders"
CACHE = BORDER_DIR / "germany.geo.json"

# 3_mittel: ~116 kB, smooth at country scale. 2_hoch/1_sehr_hoch add detail we
# cannot see at this zoom and would bloat the repository.
SOURCE_URLS = [
    "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/1_deutschland/3_mittel.geo.json",
    "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/master/1_deutschland/3_mittel.geo.json",
]


def _download() -> dict:
    last: Exception | None = None
    for url in SOURCE_URLS:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "seminar-aeer/1.0"})
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as error:
            print(f"boundaries: download failed ({url}): {error}")
            last = error
    raise RuntimeError(f"Could not fetch the Germany outline: {last}")


@lru_cache(maxsize=1)
def germany_rings() -> List[List[List[float]]]:
    """Germany's outline as a list of rings, each a list of ``[lon, lat]``.

    Returns an empty list if the boundary is neither cached nor reachable, so a
    map still renders (without the outline) rather than failing.
    """
    if CACHE.exists():
        payload = json.loads(CACHE.read_text(encoding="utf-8"))
    else:
        try:
            payload = _download()
        except RuntimeError as error:
            print(f"boundaries: {error}; drawing the map without an outline.")
            return []
        BORDER_DIR.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(payload), encoding="utf-8")

    rings: List[List[List[float]]] = []
    for feature in payload.get("features", [payload]):
        geometry = feature.get("geometry", feature)
        if geometry["type"] == "Polygon":
            rings.append(geometry["coordinates"][0])
        elif geometry["type"] == "MultiPolygon":
            rings.extend(part[0] for part in geometry["coordinates"])
    # Drop the small offshore islands; they only add clutter at this scale.
    return [ring for ring in rings if len(ring) >= 40]


def main() -> int:
    rings = germany_rings()
    print(f"boundaries: {len(rings)} rings, {sum(len(r) for r in rings)} points -> {CACHE}")
    return 0 if rings else 1


if __name__ == "__main__":
    sys.exit(main())
