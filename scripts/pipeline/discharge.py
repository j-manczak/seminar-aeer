"""Filter GRDC daily river-discharge files.

Reads the per-station text files the user downloads into data/raw/discharge/
(GRDC "Export Format, daily data only", one *.txt per gauge). Each file has a
``#`` metadata header (GRDC number, river, station, coordinates) followed by
lines ``YYYY-MM-DD;hh:mm; value`` where ``-999`` marks a missing value.

Daily values are aggregated to one row per station and year (mean/min/max plus
the number of observed days) inside the window, then restricted to gauges near a
study reactor. If the folder is missing or empty, the builder skips.
"""

from pathlib import Path
from typing import Dict, List, Optional

from pipeline.config import ANALYSIS_DIR, DISCHARGE_DIR, WINDOW_END, WINDOW_START
from pipeline.io_tables import to_float, write_table
from pipeline import sites

MISSING_VALUE = -999.0

OUTPUT_FIELDS = [
    "grdc_no",
    "river",
    "station",
    "latitude",
    "longitude",
    "year",
    "discharge_mean_m3_s",
    "discharge_min_m3_s",
    "discharge_max_m3_s",
    "days_observed",
    "nearest_reactor",
    "nearest_group",
    "distance_km",
]

# Which metadata keys we read out of the ``#`` header.
_META_KEYS = {
    "grdc-no.": "grdc_no",
    "river": "river",
    "station": "station",
    "latitude (dd)": "latitude",
    "longitude (dd)": "longitude",
}


def _parse_meta_line(line: str, meta: Dict[str, str]) -> None:
    body = line.lstrip("#").strip()
    if ":" not in body:
        return
    key, value = body.split(":", 1)
    field = _META_KEYS.get(key.strip().lower())
    if field:
        meta[field] = value.strip()


def _parse_station_file(path: Path) -> Optional[List[dict]]:
    """Read one GRDC file into annual summaries; None if it has no coordinates."""
    meta: Dict[str, str] = {}
    # year -> list of valid daily discharge values
    per_year: Dict[int, List[float]] = {}

    with path.open(encoding="latin-1") as handle:
        for line in handle:
            if line.startswith("#"):
                _parse_meta_line(line, meta)
                continue
            # Data lines look like 2008-07-01;--:--;   123.456
            if len(line) < 10 or not line[:4].isdigit() or line[4] != "-":
                continue
            parts = line.strip().split(";")
            year = to_float(line[:4])
            value = to_float(parts[-1]) if parts else None
            if year is None or value is None or value <= MISSING_VALUE:
                continue
            per_year.setdefault(int(year), []).append(value)

    latitude = to_float(meta.get("latitude"))
    longitude = to_float(meta.get("longitude"))
    if latitude is None or longitude is None:
        return None

    matched = sites.match(latitude, longitude)
    if matched is None:
        return []
    reactor, distance = matched

    rows: List[dict] = []
    for year, values in sorted(per_year.items()):
        if not (WINDOW_START <= year <= WINDOW_END):
            continue
        rows.append(
            {
                "grdc_no": meta.get("grdc_no", ""),
                "river": meta.get("river", ""),
                "station": meta.get("station", ""),
                "latitude": latitude,
                "longitude": longitude,
                "year": year,
                "discharge_mean_m3_s": round(sum(values) / len(values), 3),
                "discharge_min_m3_s": min(values),
                "discharge_max_m3_s": max(values),
                "days_observed": len(values),
                "nearest_reactor": reactor.reactor,
                "nearest_group": reactor.group,
                "distance_km": round(distance, 3),
            }
        )
    return rows


def build() -> None:
    if not DISCHARGE_DIR.exists():
        print("discharge: data/raw/discharge/ not found, skipping.")
        return
    files = sorted(p for p in DISCHARGE_DIR.rglob("*.txt"))
    if not files:
        print("discharge: no *.txt files in data/raw/discharge/, skipping.")
        return

    rows: List[dict] = []
    for path in files:
        parsed = _parse_station_file(path)
        if parsed:
            rows.extend(parsed)
    rows.sort(key=lambda r: (r["grdc_no"], r["year"]))

    header = [
        "Dataset: mean daily river discharge (GRDC), aggregated to annual values.",
        "Source: data/raw/discharge/ GRDC daily export files (*.txt).",
        "Site filter: gauges within the study radius of a study reactor.",
        f"Window filter: years {WINDOW_START}-{WINDOW_END} (inclusive).",
        "Aggregation: per station and year -- mean/min/max discharge and the",
        "         number of observed days (days_observed lets you drop sparse years).",
        "Added columns: nearest study reactor, its group and the distance in km.",
    ]
    count = write_table(ANALYSIS_DIR / "discharge_2006_2018.csv", header, OUTPUT_FIELDS, rows)
    stations = len({r["grdc_no"] for r in rows})
    print(f"discharge_2006_2018.csv: {count} rows from {stations} gauges near study sites")


if __name__ == "__main__":
    build()
