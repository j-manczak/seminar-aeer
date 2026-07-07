"""Build the reactor group assignment and the filtered analysis inputs.

This script turns the raw/processed project data into the artefacts needed for
the difference-in-differences design of the German 2011 nuclear moratorium:

1. ``data/processed/group_assignment.csv`` -- one row per reactor with its
   study group, river, cooling type, shutdown year and a written justification.
2. Filtered per-dataset files in ``data/processed/analysis/`` restricted to the
   study reactor sites and the 2006-2018 observation window. Every output file
   carries a leading comment block that documents exactly which filter was
   applied so the provenance travels with the data.

The script deliberately relies on the Python standard library only, mirroring
``scripts/prepare_data.py``.

Run: ``python scripts/build_group_assignment_and_filters.py``
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"

# Observation window for the study (inclusive on both ends).
WINDOW_START = 2006
WINDOW_END = 2018

# A monitoring/weather/conventional-plant location counts as belonging to a
# study site when it lies within this radius of a study reactor. 50 km matches
# the treatment radius used in scripts/prepare_data.py.
SITE_RADIUS_KM = 50.0


# --------------------------------------------------------------------------- #
# Master reactor table
# --------------------------------------------------------------------------- #
# Cooling type ("Kühlungstyp"), commissioning and shutdown years are compiled
# from public reactor documentation (BASE, operator brochures, World Nuclear
# News); they are not contained in the project's raw data files. See METHODS.md
# for the individual sources and the residual uncertainties.
#
# group values:
#   Treatment              -- whole site went off-grid in 2011 (full cooling
#                             load removed).
#   Partial                -- one block went off-grid in 2011 while a sister
#                             block at the same site kept running.
#   Kontrolle              -- ran continuously across the full 2006-2018 window.
#   Gestaffeltes Treatment -- operation ends inside the window (later, staggered
#                             cooling-load shock); not a valid full-window
#                             control.
#   Ausgeschlossen         -- already effectively off-grid before 2011, delivers
#                             no 2011 shock.


@dataclass(frozen=True)
class Reactor:
    reaktor: str
    block: str
    gruppe: str
    fluss: str
    kuehlungstyp: str
    commissioned_year: int
    stilllegungsjahr: int
    latitude: float
    longitude: float
    begruendung: str


REACTORS: list[Reactor] = [
    # --- Treatment: full-site 2011 shutdowns --------------------------------
    Reactor(
        "Biblis A", "KWB A", "Treatment", "Rhein", "Kreislaufkühlung (Naturzug-Nasskühlturm)",
        1974, 2011, 49.7094, 8.4147,
        "2011 im Zuge des Moratoriums abgeschaltet. Am Standort Biblis wurde mit "
        "beiden Blöcken die gesamte Kühllast entfernt, daher voller Treatment-Schock.",
    ),
    Reactor(
        "Biblis B", "KWB B", "Treatment", "Rhein", "Kreislaufkühlung (Naturzug-Nasskühlturm)",
        1976, 2011, 49.7094, 8.4147,
        "2011 abgeschaltet. Schwesterblock Biblis A wurde gleichzeitig stillgelegt, "
        "so dass am Standort die vollständige Kühllast wegfiel (voller Treatment-Schock).",
    ),
    Reactor(
        "Unterweser", "KKU", "Treatment", "Weser", "Durchlaufkühlung (Frischwasser, kein Kühlturm)",
        1978, 2011, 53.4286, 8.4769,
        "2011 abgeschaltet. Einblockstandort mit Durchlaufkühlung aus der tidebeeinflussten "
        "Unterweser; die gesamte thermische Einleitung entfiel 2011 (voller Treatment-Schock).",
    ),
    # --- Partial: 2011 block shutdown, sister block continued ---------------
    Reactor(
        "Isar 1", "KKI 1", "Partial", "Isar", "Durchlaufkühlung (Frischwasser, Zellenkühler)",
        1977, 2011, 48.6048, 12.2955,
        "2011 abgeschaltet, während Isar 2 am selben Standort weiterlief. Nur ein Teil der "
        "Kühllast (Block 1, Durchlaufkühlung der Isar) entfiel, daher partieller Schock.",
    ),
    Reactor(
        "Neckarwestheim 1", "GKN I", "Partial", "Neckar", "Kreislaufkühlung (Nasskühlturm)",
        1976, 2011, 49.0411, 9.1750,
        "2011 abgeschaltet, während Neckarwestheim 2 am selben Standort weiterlief. Nur die "
        "Kühllast von Block 1 entfiel, daher partieller Schock.",
    ),
    Reactor(
        "Philippsburg 1", "KKP 1", "Partial", "Rhein", "Kreislaufkühlung (Nasskühlturm)",
        1979, 2011, 49.2527, 8.4354,
        "2011 abgeschaltet, während Philippsburg 2 am selben Standort weiterlief. Nur die "
        "Kühllast von Block 1 entfiel, daher partieller Schock.",
    ),
    # --- Kontrolle: continuous operation across the full 2006-2018 window ----
    Reactor(
        "Grohnde", "KWG", "Kontrolle", "Weser", "Kreislaufkühlung (Naturzug-Nasskühlturm)",
        1985, 2021, 52.0356, 9.4135,
        "Lief 2006-2018 durchgehend am Netz (Stilllegung erst Ende 2021), keine Kühllast-"
        "änderung im Fenster. Sauberer Standort ohne Blockabschaltung im Fenster.",
    ),
    Reactor(
        "Emsland", "KKE", "Kontrolle", "Ems", "Kreislaufkühlung (Naturzug-Nasskühlturm)",
        1988, 2023, 52.4819, 7.3067,
        "Lief 2006-2018 durchgehend am Netz (Stilllegung erst 2023). Einblockstandort ohne "
        "Kühllaständerung im Fenster, sauberer Kontrollstandort.",
    ),
    Reactor(
        "Brokdorf", "KBR", "Kontrolle", "Elbe", "Durchlaufkühlung (Frischwasser, kein Kühlturm)",
        1986, 2021, 53.8511, 9.3459,
        "Lief 2006-2018 durchgehend am Netz (Stilllegung erst Ende 2021). Einblockstandort mit "
        "Durchlaufkühlung der Elbe, keine Kühllaständerung im Fenster.",
    ),
    Reactor(
        "Isar 2", "KKI 2", "Kontrolle", "Isar", "Kreislaufkühlung (Naturzug-Nasskühlturm)",
        1988, 2023, 48.6046, 12.2951,
        "Lief 2006-2018 durchgehend am Netz (Stilllegung erst 2023). Als weiterlaufender "
        "Schwesterblock von Isar 1 Kontrolle auf Reaktorebene; am Standort trat 2011 jedoch "
        "eine partielle Lastreduktion auf (siehe Isar 1).",
    ),
    Reactor(
        "Neckarwestheim 2", "GKN II", "Kontrolle", "Neckar", "Kreislaufkühlung (Nasskühlturm)",
        1989, 2023, 49.0411, 9.1750,
        "Lief 2006-2018 durchgehend am Netz (Stilllegung erst 2023). Als weiterlaufender "
        "Schwesterblock von Neckarwestheim 1 Kontrolle auf Reaktorebene; am Standort trat 2011 "
        "eine partielle Lastreduktion auf (siehe Neckarwestheim 1).",
    ),
    Reactor(
        "Philippsburg 2", "KKP 2", "Kontrolle", "Rhein", "Kreislaufkühlung (Naturzug-Nasskühlturm)",
        1985, 2019, 49.2527, 8.4354,
        "Lief 2006-2018 durchgehend am Netz (Stilllegung erst Ende 2019, also nach dem Fenster). "
        "Als weiterlaufender Schwesterblock von Philippsburg 1 Kontrolle auf Reaktorebene; am "
        "Standort trat 2011 eine partielle Lastreduktion auf (siehe Philippsburg 1).",
    ),
    Reactor(
        "Gundremmingen C", "KRB C", "Kontrolle", "Donau", "Kreislaufkühlung (Naturzug-Nasskühlturm)",
        1984, 2021, 48.5161, 10.3982,
        "Lief 2006-2018 durchgehend am Netz (Stilllegung erst Ende 2021). Keine Abschaltung 2011; "
        "am Standort ging jedoch der Schwesterblock Gundremmingen B Ende 2017 vom Netz (siehe dort).",
    ),
    # --- Gestaffeltes Treatment: operation ends inside the window -----------
    Reactor(
        "Grafenrheinfeld", "KKG", "Gestaffeltes Treatment", "Main", "Kreislaufkühlung (Naturzug-Nasskühlturm)",
        1982, 2015, 49.9844, 10.1818,
        "Ende 2015 stillgelegt und damit MITTEN im Fenster 2006-2018 vom Netz. Keine gültige "
        "Vollzeit-Kontrolle; als spätere, gestaffelte Behandlung (Kühllast-Wegfall 2015) zu behandeln.",
    ),
    Reactor(
        "Gundremmingen B", "KRB B", "Gestaffeltes Treatment", "Donau", "Kreislaufkühlung (Naturzug-Nasskühlturm)",
        1984, 2017, 48.5150, 10.4016,
        "Ende 2017 stillgelegt und damit MITTEN im Fenster 2006-2018 vom Netz. Keine gültige "
        "Vollzeit-Kontrolle; als spätere, gestaffelte Behandlung (Kühllast-Wegfall 2017) zu behandeln. "
        "Schwesterblock Gundremmingen C lief weiter.",
    ),
    # --- Ausgeschlossen: already offline well before 2011 -------------------
    Reactor(
        "Krümmel", "KKK", "Ausgeschlossen", "Elbe", "Durchlaufkühlung (Frischwasser, kein Kühlturm)",
        1984, 2011, 53.4109, 10.4092,
        "Formale Netztrennung 2011, faktisch aber seit dem Transformatorbrand 2007 nur noch kurz "
        "und ab 2009 gar nicht mehr am Netz. Liefert 2011 keinen echten Kühllast-Schock und wird "
        "daher ausgeschlossen.",
    ),
    Reactor(
        "Brunsbüttel", "KKB", "Ausgeschlossen", "Elbe", "Durchlaufkühlung (Frischwasser, kein Kühlturm)",
        1976, 2011, 53.8918, 9.2026,
        "Formale Netztrennung 2011, faktisch aber seit einem Störfall 2007 dauerhaft abgeschaltet. "
        "Liefert 2011 keinen echten Kühllast-Schock und wird daher ausgeschlossen.",
    ),
]

# Sites that belong to the study for spatial filtering (everything except the
# excluded reactors). Reactors that share a site are de-duplicated by rounding.
STUDY_REACTORS = [r for r in REACTORS if r.gruppe != "Ausgeschlossen"]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return 2 * earth_radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_study_reactor(lat: float, lon: float) -> tuple[Reactor, float]:
    best_r = STUDY_REACTORS[0]
    best_d = float("inf")
    for r in STUDY_REACTORS:
        d = haversine_km(lat, lon, r.latitude, r.longitude)
        if d < best_d:
            best_d = d
            best_r = r
    return best_r, best_d


def parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value: str | None) -> int | None:
    f = parse_float(value)
    return int(f) if f is not None else None


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def write_with_header(path: Path, header_lines: list[str], fieldnames: list[str], rows: list[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        for line in header_lines:
            fh.write(f"# {line}\n")
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
    return len(rows)


# --------------------------------------------------------------------------- #
# 1) group_assignment.csv
# --------------------------------------------------------------------------- #
def write_group_assignment() -> None:
    fieldnames = ["Reaktor", "Gruppe", "Fluss", "Kühlungstyp", "Stilllegungsjahr", "Begründung"]
    path = PROCESSED_DIR / "group_assignment.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in REACTORS:
            writer.writerow(
                {
                    "Reaktor": r.reaktor,
                    "Gruppe": r.gruppe,
                    "Fluss": r.fluss,
                    "Kühlungstyp": r.kuehlungstyp,
                    "Stilllegungsjahr": r.stilllegungsjahr,
                    "Begründung": r.begruendung,
                }
            )
    print(f"group_assignment.csv: {len(REACTORS)} reactors")
    for grp in ["Treatment", "Partial", "Kontrolle", "Gestaffeltes Treatment", "Ausgeschlossen"]:
        members = [r.reaktor for r in REACTORS if r.gruppe == grp]
        print(f"  {grp}: {len(members)} -> {', '.join(members)}")


# --------------------------------------------------------------------------- #
# 2a) Water temperature
# --------------------------------------------------------------------------- #
def filter_water_temperature() -> None:
    src = PROCESSED_DIR / "water_temperature_de_annual_clean.csv"
    rows = read_rows(src)
    out_rows: list[dict] = []
    for row in rows:
        year = parse_int(row.get("year"))
        lat = parse_float(row.get("site_latitude"))
        lon = parse_float(row.get("site_longitude"))
        if year is None or lat is None or lon is None:
            continue
        if not (WINDOW_START <= year <= WINDOW_END):
            continue
        reactor, dist = nearest_study_reactor(lat, lon)
        if dist > SITE_RADIUS_KM:
            continue
        new = dict(row)
        new["nearest_study_reactor"] = reactor.reaktor
        new["nearest_study_group"] = reactor.gruppe
        new["nearest_study_river"] = reactor.fluss
        new["distance_to_study_reactor_km"] = round(dist, 3)
        out_rows.append(new)

    fieldnames = list(rows[0].keys()) + [
        "nearest_study_reactor",
        "nearest_study_group",
        "nearest_study_river",
        "distance_to_study_reactor_km",
    ]
    header = [
        "Dataset: annual water temperature at German monitoring sites (EEA Waterbase v2020_1).",
        "Source file: data/processed/water_temperature_de_annual_clean.csv",
        f"Filter 1 (site): kept only monitoring sites within {SITE_RADIUS_KM:.0f} km of a study reactor",
        f"          site (all reactors except the excluded Krümmel/Brunsbüttel).",
        f"Filter 2 (window): kept only observation years {WINDOW_START}-{WINDOW_END} (inclusive).",
        "Note: Waterbase supplies no rows for 2006, 2007 and 2015 for these sites; the window",
        "      therefore materialises as 2008-2014 plus 2016-2018.",
        "Added columns: nearest study reactor, its group and river, and the distance in km.",
    ]
    n = write_with_header(ANALYSIS_DIR / "water_temperature_2006_2018_study_sites.csv", header, fieldnames, out_rows)
    yrs = sorted({parse_int(r["year"]) for r in out_rows})
    print(f"water_temperature analysis file: {n} rows; years present: {yrs}")


# --------------------------------------------------------------------------- #
# 2b) Weather (DWD daily)
# --------------------------------------------------------------------------- #
def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def filter_weather() -> None:
    src = PROCESSED_DIR / "dwd_kl_daily_near_nuclear.csv"
    rows = read_rows(src)
    # Bucket the daily observations by station and calendar month; the raw daily
    # extract (>100k rows) is aggregated to station-month summaries so the file
    # stays compact and matches the annual/monthly resolution of the outcome data.
    buckets: dict[tuple, dict] = {}
    for row in rows:
        date = (row.get("date") or "").strip()
        lat = parse_float(row.get("latitude"))
        lon = parse_float(row.get("longitude"))
        if len(date) < 7 or lat is None or lon is None:
            continue
        year = int(date[:4])
        if not (WINDOW_START <= year <= WINDOW_END):
            continue
        reactor, dist = nearest_study_reactor(lat, lon)
        if dist > SITE_RADIUS_KM:
            continue
        key = (row.get("station_id"), year, int(date[5:7]))
        b = buckets.setdefault(
            key,
            {
                "station_id": row.get("station_id"),
                "station_name": row.get("station_name"),
                "latitude": lat,
                "longitude": lon,
                "year": year,
                "month": int(date[5:7]),
                "nearest_study_reactor": reactor.reaktor,
                "nearest_study_group": reactor.gruppe,
                "distance_to_study_reactor_km": round(dist, 3),
                "_tmean": [],
                "_tmin": [],
                "_tmax": [],
                "_precip": [],
                "_wind": [],
            },
        )
        for field, col in (
            ("_tmean", "temperature_celsius"),
            ("_tmin", "min_temperature_celsius"),
            ("_tmax", "max_temperature_celsius"),
            ("_precip", "precipitation_mm"),
            ("_wind", "wind_speed_m_s"),
        ):
            v = parse_float(row.get(col))
            if v is not None:
                b[field].append(v)

    out_rows: list[dict] = []
    for b in buckets.values():
        out_rows.append(
            {
                "station_id": b["station_id"],
                "station_name": b["station_name"],
                "latitude": b["latitude"],
                "longitude": b["longitude"],
                "year": b["year"],
                "month": b["month"],
                "air_temperature_mean_c": _mean(b["_tmean"]),
                "air_temperature_min_c": min(b["_tmin"]) if b["_tmin"] else None,
                "air_temperature_max_c": max(b["_tmax"]) if b["_tmax"] else None,
                "precipitation_sum_mm": round(sum(b["_precip"]), 2) if b["_precip"] else None,
                "wind_speed_mean_m_s": _mean(b["_wind"]),
                "days_observed": len(b["_tmean"]),
                "nearest_study_reactor": b["nearest_study_reactor"],
                "nearest_study_group": b["nearest_study_group"],
                "distance_to_study_reactor_km": b["distance_to_study_reactor_km"],
            }
        )
    out_rows.sort(key=lambda r: (r["station_id"], r["year"], r["month"]))

    fieldnames = [
        "station_id", "station_name", "latitude", "longitude", "year", "month",
        "air_temperature_mean_c", "air_temperature_min_c", "air_temperature_max_c",
        "precipitation_sum_mm", "wind_speed_mean_m_s", "days_observed",
        "nearest_study_reactor", "nearest_study_group", "distance_to_study_reactor_km",
    ]
    header = [
        "Dataset: DWD daily climate observations (KL) at stations near the nuclear sites,",
        "         aggregated to station-month summaries.",
        "Source file: data/processed/dwd_kl_daily_near_nuclear.csv",
        f"Filter 1 (site): kept only stations within {SITE_RADIUS_KM:.0f} km of a study reactor site.",
        f"Filter 2 (window): kept only dates in {WINDOW_START}-{WINDOW_END} (inclusive).",
        "Aggregation: per station and calendar month -- mean/min/max air temperature,",
        "         precipitation sum, mean wind speed, and the number of observed days.",
        "         The >100k daily rows are condensed to keep the file compact and to match",
        "         the monthly/annual resolution of the water outcome data; days_observed lets",
        "         you re-weight or drop sparsely observed station-months.",
        "Note: the daily DWD extract only spans 2005-2015, so the window materialises as 2006-2015.",
        "Note: the extract contains no station within 50 km of the treatment site Unterweser;",
        "      Biblis is covered (stations on the middle Rhine fall closest to Biblis).",
        "Added columns: nearest study reactor, its group and the distance in km.",
    ]
    n = write_with_header(ANALYSIS_DIR / "weather_2006_2018_study_sites.csv", header, fieldnames, out_rows)
    yrs = sorted({r["year"] for r in out_rows})
    plants = sorted({r["nearest_study_reactor"] for r in out_rows})
    print(f"weather analysis file: {n} station-month rows; years {yrs[0]}-{yrs[-1]}; sites: {plants}")


# --------------------------------------------------------------------------- #
# 2c) Power plants (conventional thermal plants near the study sites)
# --------------------------------------------------------------------------- #
def filter_power_plants() -> None:
    src = PROCESSED_DIR / "conventional_plants_de_relevant_clean.csv"
    rows = read_rows(src)
    out_rows: list[dict] = []
    for row in rows:
        lat = parse_float(row.get("latitude"))
        lon = parse_float(row.get("longitude"))
        if lat is None or lon is None:
            continue
        commissioned = parse_int(row.get("commissioned_year"))
        shutdown = parse_int(row.get("shutdown_year"))
        # Keep plants whose operating life overlaps the window at all.
        if commissioned is not None and commissioned > WINDOW_END:
            continue
        if shutdown is not None and shutdown < WINDOW_START:
            continue
        reactor, dist = nearest_study_reactor(lat, lon)
        if dist > SITE_RADIUS_KM:
            continue
        new = dict(row)
        new["nearest_study_reactor"] = reactor.reaktor
        new["nearest_study_group"] = reactor.gruppe
        new["distance_to_study_reactor_km"] = round(dist, 3)
        out_rows.append(new)

    fieldnames = list(rows[0].keys()) + [
        "nearest_study_reactor",
        "nearest_study_group",
        "distance_to_study_reactor_km",
    ]
    header = [
        "Dataset: conventional thermal power plants (Open Power System Data, conventional_power_plants_DE).",
        "Source file: data/processed/conventional_plants_de_relevant_clean.csv",
        f"Filter 1 (site): kept only plants within {SITE_RADIUS_KM:.0f} km of a study reactor site.",
        f"Filter 2 (window): kept only plants whose operating life overlaps {WINDOW_START}-{WINDOW_END}",
        "          (commissioned no later than 2018 and not shut down before 2006).",
        "Purpose: these are potential thermal confounders near the study rivers.",
        "The study nuclear reactors themselves are documented in data/processed/group_assignment.csv.",
        "Added columns: nearest study reactor, its group and the distance in km.",
    ]
    n = write_with_header(ANALYSIS_DIR / "power_plants_2006_2018_study_sites.csv", header, fieldnames, out_rows)
    print(f"power_plants analysis file: {n} rows")


# --------------------------------------------------------------------------- #
# 2d/2e) Placeholders for dissolved oxygen and discharge (no source data yet)
# --------------------------------------------------------------------------- #
def write_missing_dataset_placeholder(name: str, german_label: str, expected_source: str, columns: list[str]) -> None:
    header = [
        f"Dataset: {german_label} -- PLACEHOLDER, NO SOURCE DATA PRESENT IN THE REPOSITORY.",
        f"Expected source: {expected_source}",
        f"Intended filter (once data is available): monitoring stations within {SITE_RADIUS_KM:.0f} km of a",
        f"          study reactor site, observation years {WINDOW_START}-{WINDOW_END} (inclusive).",
        "This file intentionally contains no data rows. It fixes the target schema and the filter",
        "definition so the group can drop in the raw dataset later without changing the pipeline.",
        "See METHODS.md, section on dissolved oxygen / discharge, for details.",
    ]
    path = ANALYSIS_DIR / f"{name}_2006_2018_study_sites.PLACEHOLDER.csv"
    write_with_header(path, header, columns, [])
    print(f"placeholder written: {path.name}")


def main() -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    write_group_assignment()
    filter_water_temperature()
    filter_weather()
    filter_power_plants()
    write_missing_dataset_placeholder(
        "dissolved_oxygen",
        "gelöster Sauerstoff (dissolved oxygen) an Gewässer-Messstellen",
        "EEA Waterbase v2020_1 T_WISE6 AggregatedData, determinand 'Dissolved oxygen' "
        "(same raw file as water temperature; not committed to the repo because of GitHub's size limit).",
        [
            "site_id", "site_name", "water_body_name", "site_latitude", "site_longitude",
            "year", "dissolved_oxygen_mean_mg_l", "dissolved_oxygen_min_mg_l",
            "dissolved_oxygen_max_mg_l", "observations",
            "nearest_study_reactor", "nearest_study_group", "distance_to_study_reactor_km",
        ],
    )
    write_missing_dataset_placeholder(
        "discharge",
        "Abfluss (river discharge) an Pegeln",
        "German gauging-station discharge, e.g. GRDC or BfG/PEGELONLINE daily/annual discharge "
        "(Q in m3/s); no such raw file is present in the repository yet.",
        [
            "gauge_id", "gauge_name", "river", "latitude", "longitude",
            "year", "discharge_mean_m3_s", "discharge_min_m3_s", "discharge_max_m3_s",
            "nearest_study_reactor", "nearest_study_group", "distance_to_study_reactor_km",
        ],
    )


if __name__ == "__main__":
    main()
