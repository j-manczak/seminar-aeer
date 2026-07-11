"""Build a dense water-quality panel from the Waterbase disaggregated SQLite.

The annual AggregatedData is too sparse for the DiD (see did_analysis.py). This
module reads the individual measurements (Waterbase v2025_1 WISE6
DisaggregatedData, ~97 M rows), keeps German water-temperature and dissolved-
oxygen samples on a study river within 50 km of a study reactor, and aggregates
them to two balanced panels:

  water_quality_monthly_by_site.csv  site x determinand x year x month
  water_quality_summer_by_site.csv   site x determinand x year, June-September

Each row carries the river position (downstream/upstream), the nearest upstream
reactor and its group, and the distance band -- everything the analysis needs.

The SQLite file is large and lives outside git; the module looks for it in
data/raw/waterbase/ and then in the download folder.

    python scripts/pipeline/waterbase_disaggregated.py
"""

import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.config import ANALYSIS_DIR, WATERBASE_DIR
from pipeline.io_tables import write_table
from pipeline import sites, river_position
import mapdata

DB_NAME = "Waterbase_v2025_1_WISE6_DisaggregatedData.sqlite"
CANDIDATE_DBS = [
    WATERBASE_DIR / DB_NAME,
    Path.home() / "Downloads" / "AEER_Datasets" / "WISE6_DisaggregatedData_sqlite" / DB_NAME,
]

DETERMINANDS = {"Water temperature": "water_temperature", "Dissolved oxygen": "dissolved_oxygen"}
SUMMER_MONTHS = {6, 7, 8, 9}
YEAR_MIN, YEAR_MAX = 2006, 2024  # keep broad; the analysis picks its own window


def _find_db() -> Optional[Path]:
    return next((p for p in CANDIDATE_DBS if p.exists()), None)


def _load_sites(con: sqlite3.Connection) -> Dict[str, dict]:
    rows = con.execute(
        "SELECT monitoringSiteIdentifier, monitoringSiteName, waterBodyName, lat, lon "
        "FROM S_WISE6_SpatialObject_DerivedData WHERE countryCode='DE'"
    )
    out = {}
    for site_id, name, water_body, lat, lon in rows:
        if site_id and lat is not None and lon is not None:
            out[site_id] = {"name": name or "", "water_body": water_body or "",
                            "lat": float(lat), "lon": float(lon)}
    return out


def _parse_ym(stamp: str):
    stamp = (stamp or "").strip()
    if len(stamp) < 7 or not stamp[:4].isdigit():
        return None, None
    year = int(stamp[:4])
    month = int(stamp[5:7]) if stamp[4] == "-" else int(stamp[4:6])
    return year, month


def build() -> None:
    db = _find_db()
    if db is None:
        print(f"waterbase_disaggregated: {DB_NAME} not found in data/raw/waterbase/ or Downloads, skipping.")
        return
    print(f"waterbase_disaggregated: reading {db}")
    con = sqlite3.connect(str(db))
    site_meta = _load_sites(con)

    # The v2025 water-body names are often the placeholder "NAME", so match the
    # river geometrically from the site coordinates instead of by name.
    to_river = mapdata.river_matcher()

    # Cache the river-position classification per site (independent of the sample).
    classify_cache: Dict[str, Optional[dict]] = {}

    def classify(site_id: str):
        if site_id not in classify_cache:
            meta = site_meta.get(site_id)
            if meta is None or sites.match(meta["lat"], meta["lon"]) is None:
                classify_cache[site_id] = None
            else:
                river = to_river(meta["lat"], meta["lon"])
                pos = river_position.classify(meta["lat"], meta["lon"], river=river)
                classify_cache[site_id] = pos if pos["position"] in {"downstream", "upstream"} else None
        return classify_cache[site_id]

    # monthly[(site, det, year, month)] = [values]; summer[(site, det, year)] = [values]
    monthly: Dict[tuple, List[float]] = defaultdict(list)
    summer: Dict[tuple, List[float]] = defaultdict(list)

    query = (
        "SELECT monitoringSiteIdentifier, observedPropertyDeterminandLabel, "
        "phenomenonTimeSamplingDate, resultObservedValue "
        "FROM T_WISE6_DisaggregatedData "
        "WHERE countryCode='DE' AND observedPropertyDeterminandLabel IN ('Water temperature','Dissolved oxygen') "
        "AND resultObservedValue IS NOT NULL"
    )
    kept = scanned = 0
    for site_id, label, stamp, value in con.execute(query):
        scanned += 1
        det = DETERMINANDS.get(label)
        if det is None:
            continue
        pos = classify(site_id)
        if pos is None:
            continue
        year, month = _parse_ym(stamp)
        if year is None or not (YEAR_MIN <= year <= YEAR_MAX):
            continue
        try:
            v = float(value)
        except (TypeError, ValueError):
            continue
        monthly[(site_id, det, year, month)].append(v)
        if month in SUMMER_MONTHS:
            summer[(site_id, det, year)].append(v)
        kept += 1
    con.close()
    print(f"  scanned {scanned:,} DE temp/oxygen samples; kept {kept:,} on study rivers")

    _write_summer(summer, site_meta, classify_cache)
    _write_monthly(monthly, site_meta, classify_cache)


def _site_columns(site_id, meta, pos):
    return {
        "site_id": site_id,
        "site_name": meta["name"],
        "water_body_name": meta["water_body"],
        "latitude": meta["lat"],
        "longitude": meta["lon"],
        "study_river": pos["study_river"],
        "position": pos["position"],
        "nearest_upstream_plant": pos["nearest_upstream_plant"],
        "nearest_upstream_group": pos["nearest_upstream_group"],
        "along_river_km": pos["along_river_km"],
        "distance_band": pos["distance_band"],
    }


_BASE_FIELDS = ["site_id", "site_name", "water_body_name", "latitude", "longitude",
                "study_river", "position", "nearest_upstream_plant", "nearest_upstream_group",
                "along_river_km", "distance_band", "determinand"]


def _write_summer(summer, site_meta, cache):
    fields = _BASE_FIELDS + ["year", "mean_value", "n_samples"]
    rows = []
    for (site_id, det, year), values in summer.items():
        rows.append({**_site_columns(site_id, site_meta[site_id], cache[site_id]),
                     "determinand": det, "year": year,
                     "mean_value": round(sum(values) / len(values), 3), "n_samples": len(values)})
    rows.sort(key=lambda r: (r["determinand"], r["site_id"], r["year"]))
    header = [
        "Water quality, June-September (summer) mean per site and year, from the Waterbase",
        "v2025_1 disaggregated (individual-sample) data. German sites on a study river within",
        "50 km of a study reactor; determinand in {water_temperature (Cel), dissolved_oxygen (mg/L)}.",
        "n_samples is the number of underlying measurements. Built by waterbase_disaggregated.py.",
    ]
    n = write_table(ANALYSIS_DIR / "water_quality_summer_by_site.csv", header, fields, rows)
    print(f"  water_quality_summer_by_site.csv: {n} rows")


def _write_monthly(monthly, site_meta, cache):
    fields = _BASE_FIELDS + ["year", "month", "mean_value", "n_samples"]
    rows = []
    for (site_id, det, year, month), values in monthly.items():
        rows.append({**_site_columns(site_id, site_meta[site_id], cache[site_id]),
                     "determinand": det, "year": year, "month": month,
                     "mean_value": round(sum(values) / len(values), 3), "n_samples": len(values)})
    rows.sort(key=lambda r: (r["determinand"], r["site_id"], r["year"], r["month"]))
    header = [
        "Water quality, monthly mean per site, from the Waterbase v2025_1 disaggregated data.",
        "German sites on a study river within 50 km of a study reactor.",
        "Built by waterbase_disaggregated.py.",
    ]
    n = write_table(ANALYSIS_DIR / "water_quality_monthly_by_site.csv", header, fields, rows)
    print(f"  water_quality_monthly_by_site.csv: {n} rows")


if __name__ == "__main__":
    build()
