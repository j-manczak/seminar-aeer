"""Dissolved oxygen (and co-located spot temperature) from GKD Bayern chemistry.

Why a second GKD downloader
---------------------------
Dissolved oxygen has the same problem as temperature: the EEA Waterbase reports
German *river* oxygen only from 2020 (see METHODS §2.1), so it cannot speak to
2011, 2015 or 2017. GKD's water-chemistry programme does — many stations run
back to the 1980s.

Two differences from :mod:`pipeline.gkd_bayern` that matter for interpretation:

* **Different stations.** Chemistry sampling points are not the continuous
  temperature gauges, so the oxygen 2x2 uses its own upstream/downstream pair.
* **Different frequency.** Sampling is roughly fortnightly (~26 readings a year
  at a good station) rather than daily, so the oxygen panel is one to two orders
  of magnitude thinner and its estimates are correspondingly less precise.

Each request returns both parameters at once, so we also pull the *spot*
water temperature measured with the sample (``Wassertemperatur (vor Ort)``).
That is not a substitute for the daily gauge series, but it lets us check that
the oxygen stations see the same thermal signal.

Endpoints (public pages, no login):

  index    /de/fluesse/chemie/tabellen
  station  /de/fluesse/chemie/<basin>/<slug>-<id>          (coordinates)
  values   /de/fluesse/chemie/<basin>/<slug>-<id>/gesamtzeitraum/tabelle
           ?zr=gesamt&msprg=0&mpnr1=1018&mpnr2=1680&art=Mittel&beginn=&ende=
           mpnr 1018 = "Sauerstoff, gelöst", 1680 = "Wassertemperatur (vor Ort)"

Outputs:

    data/raw/gkd/gkd_chemie_stations.csv
    data/raw/gkd/chemie/<id>.csv
    data/processed/gkd_dissolved_oxygen.csv

    python scripts/pipeline/gkd_chemie.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

from pipeline.config import PROCESSED_DIR, RAW_DIR

BASE = "https://www.gkd.bayern.de"
INDEX_URL = f"{BASE}/de/fluesse/chemie/tabellen"
STATION_RE = re.compile(rf"{re.escape(BASE)}/de/fluesse/chemie/[^/\"]+/[^/\"]+-(\d+)")

GKD_DIR = RAW_DIR / "gkd"
CHEM_DIR = GKD_DIR / "chemie"
STATIONS_CSV = GKD_DIR / "gkd_chemie_stations.csv"
OUT_PANEL = PROCESSED_DIR / "gkd_dissolved_oxygen.csv"

STUDY_RIVER_BY_GERMAN = {"Isar": "Isar", "Donau": "Danube", "Main": "Main"}

PARAM_OXYGEN = "1018"       # Sauerstoff, gelöst [mg/l]
PARAM_TEMPERATURE = "1680"  # Wassertemperatur (vor Ort) [°C]

YEAR_MIN, YEAR_MAX = 1990, 2025
REQUEST_PAUSE_S = 0.7
MIN_READINGS = 40  # skip stations with almost nothing; they only cost requests

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "seminar-aeer academic research (contact via repo)"})


@dataclass(frozen=True)
class ChemStation:
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


def fetch_station_index() -> List[ChemStation]:
    """Chemistry sampling points on the study rivers."""
    html = _get(INDEX_URL)
    stations: List[ChemStation] = []
    seen: set = set()
    for row in re.findall(r"<tr.*?</tr>", html, re.S):
        link = re.search(rf'href="({re.escape(BASE)}/de/fluesse/chemie/[^"]+)"', row)
        if not link:
            continue
        cells = _cells(row)
        if len(cells) < 2:
            continue
        river_de = cells[1]
        if river_de not in STUDY_RIVER_BY_GERMAN:
            continue
        url = link.group(1).split("/gesamtzeitraum")[0]
        identifier = STATION_RE.search(url)
        if not identifier or identifier.group(1) in seen:
            continue
        seen.add(identifier.group(1))
        stations.append(
            ChemStation(
                station_id=identifier.group(1),
                name=cells[0],
                river_de=river_de,
                river=STUDY_RIVER_BY_GERMAN[river_de],
                district=cells[2] if len(cells) > 2 else "",
                url=url,
            )
        )
    return stations


def add_coordinates(station: ChemStation) -> ChemStation:
    """Read lat/lon out of the Leaflet payload on the station's own page."""
    try:
        html = _get(station.url)
    except RuntimeError:
        return station
    match = re.search(r"LfUMap\.init\((\{.*?\})\);", html, re.S)
    if not match:
        return station
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return station
    for point in payload.get("pointer", []):
        if str(point.get("p")) == station.station_id:
            return ChemStation(
                **{**station.__dict__,
                   "latitude": float(point["lat"]), "longitude": float(point["lon"])}
            )
    return station


def _number(text: str) -> Optional[float]:
    text = (text or "").replace(",", ".").strip()
    if text in ("", "--", "n.b."):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fetch_readings(station: ChemStation) -> List[tuple]:
    """(date, oxygen mg/l, spot temperature °C) for one sampling point."""
    html = _get(
        f"{station.url}/gesamtzeitraum/tabelle",
        params={
            "zr": "gesamt", "msprg": "0",
            "mpnr1": PARAM_OXYGEN, "mpnr2": PARAM_TEMPERATURE,
            "art": "Mittel",
            "beginn": f"01.01.{YEAR_MIN}", "ende": f"31.12.{YEAR_MAX}",
        },
    )
    rows: List[tuple] = []
    for row in re.findall(r"<tr.*?</tr>", html, re.S):
        cells = _cells(row)
        if len(cells) < 2 or not re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", cells[0]):
            continue
        day, month, year = cells[0].split(".")
        oxygen = _number(cells[1])
        temperature = _number(cells[2]) if len(cells) > 2 else None
        if oxygen is None and temperature is None:
            continue
        rows.append((f"{year}-{month}-{day}", oxygen, temperature))

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
    CHEM_DIR.mkdir(parents=True, exist_ok=True)

    print("gkd_chemie: fetching station index ...", flush=True)
    stations = fetch_station_index()
    print(f"gkd_chemie: {len(stations)} chemistry points on study rivers", flush=True)

    located = [add_coordinates(s) for s in stations]
    with STATIONS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["station_id", "name", "river_de", "river", "district", "url",
                         "latitude", "longitude"])
        for s in located:
            writer.writerow([s.station_id, s.name, s.river_de, s.river, s.district,
                             s.url, s.latitude, s.longitude])
    print(f"gkd_chemie: wrote {STATIONS_CSV}", flush=True)

    combined: List[list] = []
    for station in located:
        target = CHEM_DIR / f"{station.station_id}.csv"
        if target.exists():
            with target.open(encoding="utf-8") as handle:
                rows = [tuple(r) for r in csv.reader(handle)][1:]
        else:
            try:
                rows = fetch_readings(station)
            except RuntimeError as error:
                print(f"  {station.name}: {error}", flush=True)
                rows = []
            with target.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["date", "oxygen_mg_l", "temp_spot_c"])
                writer.writerows(rows)
            print(f"  {station.name[:34]:34s} ({station.river}) {len(rows):5d} readings", flush=True)

        if len(rows) < MIN_READINGS:
            continue
        for date, oxygen, temperature in rows:
            if oxygen in (None, "", "None"):
                continue
            combined.append([station.station_id, station.name, station.river,
                             station.latitude, station.longitude, date, oxygen, temperature])

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_PANEL.open("w", newline="", encoding="utf-8") as handle:
        handle.write("# Dissolved oxygen at Bavarian river chemistry sampling points (GKD).\n")
        handle.write(f"# Source: {INDEX_URL}; parameter 'Sauerstoff, geloest' (mpnr 1018),\n")
        handle.write("# with the spot water temperature taken alongside the sample (mpnr 1680).\n")
        handle.write("# Sampling is roughly fortnightly, NOT daily. Built by pipeline/gkd_chemie.py.\n")
        writer = csv.writer(handle)
        writer.writerow(["station_id", "station_name", "river", "latitude", "longitude",
                         "date", "oxygen_mg_l", "temp_spot_c"])
        writer.writerows(combined)
    print(f"gkd_chemie: wrote {len(combined):,} oxygen readings -> {OUT_PANEL}", flush=True)


if __name__ == "__main__":
    build()
