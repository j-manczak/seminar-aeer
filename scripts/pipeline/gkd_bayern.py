"""Daily river water temperature from the Bavarian Gewässerkundlicher Dienst (GKD).

Why this exists
---------------
The EEA Waterbase extract contains **no German river water temperature before
2020** — every pre-2020 German temperature record in it is groundwater (see
``data/processed/analysis/data_source_audit.md``). A 2×2 DiD around the March
2011 moratorium therefore cannot be built from Waterbase at all.

GKD publishes *daily mean* water temperature for ~150 Bavarian river gauges,
many going back to the 1980s. That covers three study sites with a genuine
upstream **and** downstream gauge on the same river:

    Isar (Isar 1, shut down 2011), Main (Grafenrheinfeld, 2015),
    Danube (Gundremmingen B, 2017)

Endpoints used (plain public pages, no login):

  index      /de/fluesse/wassertemperatur/tabellen
             one row per station: name, river, district, station URL
  station    /de/fluesse/wassertemperatur/<basin>/<slug>-<id>
             embeds ``LfUMap.init({"pointer":[...]})`` with lat/lon per station
  values     /de/fluesse/wassertemperatur/<basin>/<slug>-<id>/messwerte/tabelle
             ?zr=individuell&wertart=tmw&beginn=DD.MM.YYYY&ende=DD.MM.YYYY
             daily mean / max / min, fetched in five-year chunks

Outputs:

    data/raw/gkd/gkd_stations.csv                station master table
    data/raw/gkd/daily/<id>.csv                  one file per station
    data/processed/gkd_water_temperature_daily.csv   combined tidy panel

    python scripts/pipeline/gkd_bayern.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

from pipeline.config import PROCESSED_DIR, RAW_DIR

BASE = "https://www.gkd.bayern.de"
INDEX_URL = f"{BASE}/de/fluesse/wassertemperatur/tabellen"
STATION_RE = re.compile(rf"{re.escape(BASE)}/de/fluesse/wassertemperatur/[^/\"]+/[^/\"]+-(\d+)")

GKD_DIR = RAW_DIR / "gkd"
DAILY_DIR = GKD_DIR / "daily"
STATIONS_CSV = GKD_DIR / "gkd_stations.csv"
OUT_PANEL = PROCESSED_DIR / "gkd_water_temperature_daily.csv"

# Rivers we need; GKD spells them in German.
STUDY_RIVER_BY_GERMAN = {"Isar": "Isar", "Donau": "Danube", "Main": "Main"}

YEAR_MIN, YEAR_MAX = 1995, 2025
CHUNK_YEARS = 5
REQUEST_PAUSE_S = 0.7  # be polite to a public state server

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "seminar-aeer academic research (contact via repo)"})


@dataclass(frozen=True)
class GkdStation:
    station_id: str
    name: str
    river_de: str
    river: str
    district: str
    url: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


def _get(url: str, params: Optional[dict] = None, retries: int = 3) -> str:
    last: Optional[Exception] = None
    for attempt in range(retries):
        try:
            response = SESSION.get(url, params=params, timeout=180)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            time.sleep(REQUEST_PAUSE_S)
            return response.text
        except Exception as error:
            last = error
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"GET failed after {retries} attempts: {url} ({last})")


def _cells(row_html: str) -> List[str]:
    return [
        re.sub(r"\s+", " ", re.sub("<[^>]+>", "", cell)).strip()
        for cell in re.findall(r"<td.*?</td>", row_html, re.S)
    ]


def fetch_station_index() -> List[GkdStation]:
    """Every GKD water-temperature station on a study river."""
    html = _get(INDEX_URL)
    stations: List[GkdStation] = []
    for row in re.findall(r"<tr.*?</tr>", html, re.S):
        link = re.search(rf'href="({re.escape(BASE)}/de/fluesse/wassertemperatur/[^"]+)"', row)
        if not link:
            continue
        cells = _cells(row)
        if len(cells) < 3:
            continue
        river_de = cells[1]
        if river_de not in STUDY_RIVER_BY_GERMAN:
            continue
        url = link.group(1).split("/messwerte")[0]
        identifier = STATION_RE.search(url)
        if not identifier:
            continue
        stations.append(
            GkdStation(
                station_id=identifier.group(1),
                name=cells[0],
                river_de=river_de,
                river=STUDY_RIVER_BY_GERMAN[river_de],
                district=cells[2],
                url=url,
            )
        )
    return stations


def add_coordinates(station: GkdStation) -> GkdStation:
    """Read a station's lat/lon out of the Leaflet payload on its own page."""
    html = _get(station.url)
    match = re.search(r"LfUMap\.init\((\{.*?\})\);", html, re.S)
    if not match:
        return station
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return station
    for point in payload.get("pointer", []):
        if str(point.get("p")) == station.station_id:
            return GkdStation(
                **{
                    **station.__dict__,
                    "latitude": float(point["lat"]),
                    "longitude": float(point["lon"]),
                }
            )
    return station


def _parse_daily_table(html: str) -> List[tuple]:
    """(date, mean, max, min) rows from a GKD daily-values table."""
    out: List[tuple] = []
    for row in re.findall(r"<tr.*?</tr>", html, re.S):
        cells = _cells(row)
        if len(cells) < 2 or not re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", cells[0]):
            continue

        def number(text: str) -> Optional[float]:
            text = text.replace(",", ".").strip()
            try:
                return float(text)
            except ValueError:
                return None

        day, month, year = cells[0].split(".")
        values = [number(c) for c in cells[1:4]] + [None, None, None]
        out.append((f"{year}-{month}-{day}", values[0], values[1], values[2]))
    return out


def fetch_daily(station: GkdStation, year_min: int = YEAR_MIN, year_max: int = YEAR_MAX) -> List[tuple]:
    """Daily means for one station, requested in five-year chunks."""
    rows: List[tuple] = []
    for start in range(year_min, year_max + 1, CHUNK_YEARS):
        end = min(start + CHUNK_YEARS - 1, year_max)
        html = _get(
            f"{station.url}/messwerte/tabelle",
            params={
                "zr": "individuell",
                "wertart": "tmw",
                "beginn": f"01.01.{start}",
                "ende": f"31.12.{end}",
            },
        )
        chunk = _parse_daily_table(html)
        rows.extend(chunk)
        print(f"    {start}-{end}: {len(chunk):5d} days", flush=True)
    # De-duplicate on date, keeping the first reading seen.
    seen: set = set()
    unique = []
    for row in sorted(rows):
        if row[0] in seen:
            continue
        seen.add(row[0])
        unique.append(row)
    return unique


def build() -> None:
    GKD_DIR.mkdir(parents=True, exist_ok=True)
    DAILY_DIR.mkdir(parents=True, exist_ok=True)

    print("gkd_bayern: fetching station index ...", flush=True)
    stations = fetch_station_index()
    print(f"gkd_bayern: {len(stations)} stations on study rivers", flush=True)

    located: List[GkdStation] = []
    for station in stations:
        located.append(add_coordinates(station))
    with STATIONS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["station_id", "name", "river_de", "river", "district", "url", "latitude", "longitude"])
        for s in located:
            writer.writerow([s.station_id, s.name, s.river_de, s.river, s.district, s.url, s.latitude, s.longitude])
    print(f"gkd_bayern: wrote {STATIONS_CSV}", flush=True)

    combined: List[list] = []
    for station in located:
        target = DAILY_DIR / f"{station.station_id}.csv"
        if target.exists():
            print(f"  {station.name} ({station.river}) cached", flush=True)
            with target.open(encoding="utf-8") as handle:
                rows = [tuple(r) for r in csv.reader(handle)][1:]
        else:
            print(f"  {station.name} ({station.river}) downloading ...", flush=True)
            rows = fetch_daily(station)
            with target.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["date", "temp_mean_c", "temp_max_c", "temp_min_c"])
                writer.writerows(rows)
        for date, mean, maximum, minimum in rows:
            if mean in (None, "", "None"):
                continue
            combined.append(
                [station.station_id, station.name, station.river, station.latitude,
                 station.longitude, date, mean, maximum, minimum]
            )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_PANEL.open("w", newline="", encoding="utf-8") as handle:
        handle.write("# Daily mean river water temperature, Bavarian Gewässerkundlicher Dienst (GKD).\n")
        handle.write(f"# Source: {INDEX_URL} (public station pages, daily means 'Tagesmittelwerte').\n")
        handle.write("# Built by scripts/pipeline/gkd_bayern.py. Covers the Isar, Danube and Main study reaches.\n")
        writer = csv.writer(handle)
        writer.writerow(["station_id", "station_name", "river", "latitude", "longitude",
                         "date", "temp_mean_c", "temp_max_c", "temp_min_c"])
        writer.writerows(combined)
    print(f"gkd_bayern: wrote {len(combined):,} daily observations -> {OUT_PANEL}", flush=True)


if __name__ == "__main__":
    build()
