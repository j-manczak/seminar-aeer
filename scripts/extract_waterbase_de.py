"""One-pass extraction of every German temperature / oxygen sample from Waterbase.

The disaggregated Waterbase SQLite is ~30 GB and has no indices, so every query
is a full scan. This module makes exactly one scan and writes two compact local
files that the rest of the pipeline can read cheaply:

    data/raw/waterbase/de_samples_raw.csv   one row per measurement (DE only)
    data/raw/waterbase/de_sites_raw.csv     every German monitoring site

Deliberately *unfiltered* in space: earlier steps dropped sites with a 50 km
radius and a river-name match before we knew what the source actually contains,
which is how the 2x2 cells ended up empty. Filter later, on the extract.

    python scripts/extract_waterbase_de.py
"""

from __future__ import annotations

import csv
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw" / "waterbase"
OUT_SAMPLES = OUT_DIR / "de_samples_raw.csv"
OUT_SITES = OUT_DIR / "de_sites_raw.csv"

CANDIDATE_DBS = [
    OUT_DIR / "Waterbase_v2025_1_WISE6_DisaggregatedData.sqlite",
    Path.home() / "Downloads" / "AEER_Datasets" / "WISE6_DisaggregatedData_sqlite"
    / "Waterbase_v2025_1_WISE6_DisaggregatedData.sqlite",
]

SAMPLE_SQL = """
SELECT monitoringSiteIdentifier,
       observedPropertyDeterminandLabel,
       parameterWaterBodyCategory,
       phenomenonTimeSamplingDate,
       resultObservedValue,
       resultUom,
       parameterSampleDepth
FROM T_WISE6_DisaggregatedData
WHERE countryCode = 'DE'
  AND resultObservedValue IS NOT NULL
  AND (observedPropertyDeterminandLabel LIKE '%emperature%'
       OR observedPropertyDeterminandLabel LIKE '%xygen%')
"""

SITE_SQL = """
SELECT monitoringSiteIdentifier, monitoringSiteName, waterBodyName,
       waterBodyIdentifier, parameterWaterBodyCategory_placeholder, lat, lon
FROM S_WISE6_SpatialObject_DerivedData
WHERE countryCode = 'DE'
"""
# The spatial table has no water-body category column; keep the select explicit.
SITE_SQL = """
SELECT monitoringSiteIdentifier, monitoringSiteName, waterBodyName,
       waterBodyIdentifier, surfaceWaterBodyTypeCode, subUnitName, rbdName, lat, lon
FROM S_WISE6_SpatialObject_DerivedData
WHERE countryCode = 'DE'
"""


def find_db() -> Path:
    for path in CANDIDATE_DBS:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Waterbase disaggregated SQLite not found in:\n  "
        + "\n  ".join(str(p) for p in CANDIDATE_DBS)
    )


def connect(db: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    con.execute("PRAGMA cache_size = -524288")  # 512 MB page cache
    con.execute("PRAGMA mmap_size = 8589934592")
    return con


def dump_sites(con: sqlite3.Connection) -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    header = [
        "site_id", "site_name", "water_body_name", "water_body_id",
        "surface_water_body_type", "sub_unit", "rbd_name", "latitude", "longitude",
    ]
    seen: set[str] = set()
    written = 0
    with OUT_SITES.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in con.execute(SITE_SQL):
            site_id = row[0]
            if not site_id or site_id in seen:
                continue
            seen.add(site_id)
            writer.writerow(row)
            written += 1
    return written


def dump_samples(con: sqlite3.Connection) -> int:
    header = [
        "site_id", "determinand_label", "water_body_category",
        "sampling_date", "value", "uom", "sample_depth",
    ]
    written = 0
    started = time.time()
    with OUT_SAMPLES.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        cursor = con.execute(SAMPLE_SQL)
        while True:
            chunk = cursor.fetchmany(200_000)
            if not chunk:
                break
            writer.writerows(chunk)
            written += len(chunk)
            elapsed = time.time() - started
            print(f"  {written:,} rows ({elapsed:,.0f}s)", flush=True)
    return written


def main() -> int:
    db = find_db()
    print(f"extract_waterbase_de: reading {db}", flush=True)
    con = connect(db)

    print("extract_waterbase_de: dumping German monitoring sites ...", flush=True)
    n_sites = dump_sites(con)
    print(f"extract_waterbase_de: wrote {n_sites:,} sites -> {OUT_SITES}", flush=True)

    print("extract_waterbase_de: scanning measurements (one full pass) ...", flush=True)
    n_samples = dump_samples(con)
    print(f"extract_waterbase_de: wrote {n_samples:,} samples -> {OUT_SAMPLES}", flush=True)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
