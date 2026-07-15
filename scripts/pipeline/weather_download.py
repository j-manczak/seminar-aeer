"""Download DWD daily climate (KL) data for stations near the study reactors.

Builds data/processed/dwd_kl_daily_near_nuclear.csv, the input for weather.py.
Unlike the older scripts/build_dwd_nuclear_dataset.py this targets our 15 study
reactors (from reactors.py), uses the wider weather radius so Unterweser is
covered, downloads the DWD "historical" archive (which reaches into recent years,
so the full 2006-2018 window is available) and writes the clean column names
weather.py expects. Standard library only.

Requires internet access; run it once locally:

    python -m pipeline.weather_download        # or: python scripts/pipeline/weather_download.py
"""

import csv
import io
import re
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

if __package__ in (None, ""):  # allow running as a plain script
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.config import (
    DWD_DAILY_CSV,
    DWD_KL_HISTORICAL_INDEX,
    DWD_STATIONS_CSV,
    WEATHER_RADIUS_KM,
    WINDOW_END,
    WINDOW_START,
)
from pipeline.geo import nearest
from pipeline.io_tables import to_float
from pipeline.reactors import STUDY_REACTORS

_MISSING = -999.0
_ZIP_RE = re.compile(r'href="(tageswerte_KL_(\d{5})_\d{8}_\d{8}_hist\.zip)"', re.IGNORECASE)

# DWD produkt column -> our clean output column.
_KL_COLUMNS = {
    "TMK": "temperature_celsius",
    "TNK": "min_temperature_celsius",
    "TXK": "max_temperature_celsius",
    "RSK": "precipitation_mm",
    "FM": "wind_speed_m_s",
}

OUTPUT_FIELDS = [
    "date",
    "station_id",
    "station_name",
    "latitude",
    "longitude",
    "temperature_celsius",
    "min_temperature_celsius",
    "max_temperature_celsius",
    "precipitation_mm",
    "wind_speed_m_s",
    "nearest_nuclear_plant",
    "nearest_nuclear_plant_id",
    "distance_to_nearest_nuclear_km",
]


def _get(url: str, timeout: int = 60) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "seminar-aeer/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _select_stations() -> List[dict]:
    """Stations within the weather radius of any study reactor."""
    selected: List[dict] = []
    with DWD_STATIONS_CSV.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            lat = to_float(row.get("geoBreite"))
            lon = to_float(row.get("geoLaenge"))
            if lat is None or lon is None:
                continue
            reactor, distance = nearest(lat, lon, STUDY_REACTORS)
            if reactor is None or distance > WEATHER_RADIUS_KM:
                continue
            selected.append(
                {
                    "station_id": str(row.get("Stations_id", "")).strip().zfill(5),
                    "station_name": (row.get("Stationsname") or "").strip(),
                    "latitude": lat,
                    "longitude": lon,
                    "nearest_reactor": reactor.reactor,
                    "nearest_block": reactor.block,
                    "distance_km": round(distance, 3),
                }
            )
    return selected


def _historical_zip_urls() -> Dict[str, str]:
    """Map station_id -> historical ZIP url from the DWD index page."""
    html = _get(DWD_KL_HISTORICAL_INDEX).decode("latin-1", errors="replace")
    return {sid: DWD_KL_HISTORICAL_INDEX + name for name, sid in _ZIP_RE.findall(html)}


def _read_daily_rows(zip_bytes: bytes, station: dict) -> List[dict]:
    """Parse one station ZIP into clean daily rows inside the window."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        members = [n for n in archive.namelist() if n.lower().startswith("produkt_klima_tag_")]
        if not members:
            return []
        text = archive.read(members[0]).decode("latin-1")

    rows: List[dict] = []
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    for record in reader:
        record = {(k or "").strip(): (v or "").strip() for k, v in record.items()}
        stamp = record.get("MESS_DATUM", "")
        if len(stamp) != 8 or not stamp.isdigit():
            continue
        year = int(stamp[:4])
        if not (WINDOW_START <= year <= WINDOW_END):
            continue
        row = {
            "date": f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}",
            "station_id": station["station_id"],
            "station_name": station["station_name"],
            "latitude": station["latitude"],
            "longitude": station["longitude"],
            "nearest_nuclear_plant": station["nearest_reactor"],
            "nearest_nuclear_plant_id": station["nearest_block"],
            "distance_to_nearest_nuclear_km": station["distance_km"],
        }
        for source, target in _KL_COLUMNS.items():
            value = to_float(record.get(source))
            row[target] = "" if value is None or value <= _MISSING else value
        rows.append(row)
    return rows


def build() -> None:
    if not DWD_STATIONS_CSV.exists():
        print(f"weather_download: station list not found at {DWD_STATIONS_CSV}, skipping.")
        return

    stations = _select_stations()
    print(f"weather_download: {len(stations)} stations within {WEATHER_RADIUS_KM:.0f} km of a study reactor")
    zip_urls = _historical_zip_urls()

    all_rows: List[dict] = []
    used, missing = 0, 0
    for station in stations:
        url = zip_urls.get(station["station_id"])
        if not url:
            missing += 1
            continue
        try:
            all_rows.extend(_read_daily_rows(_get(url), station))
            used += 1
        except Exception as error:  # keep going if a single station fails
            print(f"  station {station['station_id']} failed: {error}")
            missing += 1

    DWD_DAILY_CSV.parent.mkdir(parents=True, exist_ok=True)
    with DWD_DAILY_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    years = sorted({r["date"][:4] for r in all_rows})
    span = f"{years[0]}-{years[-1]}" if years else "no data"
    print(f"weather_download: {len(all_rows)} daily rows from {used} stations "
          f"({missing} without historical ZIP); years {span}")
    print(f"  wrote {DWD_DAILY_CSV}")


if __name__ == "__main__":
    build()
