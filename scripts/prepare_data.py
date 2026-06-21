"""Prepare clean input tables for a German nuclear shutdown DiD analysis.

The script intentionally uses only the Python standard library because the
current project virtual environment does not include pandas.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"


def raw_path(preferred_path: Path, legacy_filename: str) -> Path:
    if preferred_path.exists():
        return preferred_path
    return PROJECT_ROOT / legacy_filename


PLANTS_FILE = raw_path(
    RAW_DIR / "power_plants" / "conventional_power_plants_DE.csv",
    "conventional_power_plants_DE.csv",
)
SPATIAL_FILE = raw_path(
    RAW_DIR / "waterbase" / "Waterbase_v2020_1_S_WISE6_SpatialObject_DerivedData.csv",
    "Waterbase_v2020_1_S_WISE6_SpatialObject_DerivedData.csv",
)
WATER_FILE = raw_path(
    RAW_DIR / "waterbase" / "Waterbase_v2020_1_T_WISE6_AggregatedData.csv",
    "Waterbase_v2020_1_T_WISE6_AggregatedData.csv",
)
WEATHER_FILE = raw_path(
    RAW_DIR / "weather" / "weather_data.csv",
    "weather_data.csv",
)


@dataclass(frozen=True)
class Plant:
    plant_id: str
    plant_name: str
    block_name: str
    state: str
    capacity_mw: float | None
    commissioned_year: int | None
    shutdown_year: int | None
    status: str
    latitude: float | None
    longitude: float | None


@dataclass(frozen=True)
class MonitoringSite:
    site_id: str
    site_name: str
    water_body_id: str
    water_body_name: str
    water_body_category: str
    latitude: float | None
    longitude: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--treatment-radius-km",
        type=float,
        default=50.0,
        help="Monitoring sites within this distance of a shutdown nuclear plant are marked as treated.",
    )
    parser.add_argument(
        "--preview-rows",
        type=int,
        default=20,
        help="Number of rows to include in the Markdown preview table.",
    )
    return parser.parse_args()


def clean_text(value: str | None) -> str:
    return (value or "").strip()


def parse_float(value: str | None) -> float | None:
    text = clean_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_year(value: str | None) -> int | None:
    number = parse_float(value)
    if number is None:
        return None
    return int(number)


def read_csv_rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as file:
        yield from csv.DictReader(file)


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "" if row.get(key) is None else row.get(key) for key in fieldnames})
            row_count += 1
    return row_count


def haversine_km(
    first_latitude: float,
    first_longitude: float,
    second_latitude: float,
    second_longitude: float,
) -> float:
    earth_radius_km = 6371.0
    first_latitude_rad = math.radians(first_latitude)
    second_latitude_rad = math.radians(second_latitude)
    delta_latitude = math.radians(second_latitude - first_latitude)
    delta_longitude = math.radians(second_longitude - first_longitude)
    angle = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(first_latitude_rad)
        * math.cos(second_latitude_rad)
        * math.sin(delta_longitude / 2) ** 2
    )
    return 2 * earth_radius_km * math.atan2(math.sqrt(angle), math.sqrt(1 - angle))


def load_nuclear_plants() -> list[Plant]:
    plants: list[Plant] = []
    for row in read_csv_rows(PLANTS_FILE):
        if clean_text(row.get("energy_source")) != "Nuclear":
            continue
        plants.append(
            Plant(
                plant_id=clean_text(row.get("id")),
                plant_name=clean_text(row.get("name_bnetza")),
                block_name=clean_text(row.get("block_bnetza")),
                state=clean_text(row.get("state")),
                capacity_mw=parse_float(row.get("capacity_net_bnetza")),
                commissioned_year=parse_year(row.get("commissioned")),
                shutdown_year=parse_year(row.get("shutdown")),
                status=clean_text(row.get("status")),
                latitude=parse_float(row.get("lat")),
                longitude=parse_float(row.get("lon")),
            )
        )
    return plants


def load_german_monitoring_sites() -> dict[str, MonitoringSite]:
    sites: dict[str, MonitoringSite] = {}
    for row in read_csv_rows(SPATIAL_FILE):
        if clean_text(row.get("countryCode")) != "DE":
            continue
        site_id = clean_text(row.get("monitoringSiteIdentifier"))
        if not site_id:
            continue
        sites[site_id] = MonitoringSite(
            site_id=site_id,
            site_name=clean_text(row.get("monitoringSiteName")),
            water_body_id=clean_text(row.get("waterBodyIdentifier")),
            water_body_name=clean_text(row.get("waterBodyName")),
            water_body_category=clean_text(row.get("specialisedZoneType")),
            latitude=parse_float(row.get("lat")),
            longitude=parse_float(row.get("lon")),
        )
    return sites


def build_air_temperature_rows() -> list[dict[str, object]]:
    yearly_values: dict[int, list[float]] = defaultdict(list)
    for row in read_csv_rows(WEATHER_FILE):
        timestamp = clean_text(row.get("utc_timestamp"))
        temperature = parse_float(row.get("DE_temperature"))
        if len(timestamp) < 4 or temperature is None:
            continue
        yearly_values[int(timestamp[:4])].append(temperature)

    rows = []
    for year, values in sorted(yearly_values.items()):
        rows.append(
            {
                "year": year,
                "air_temperature_de_mean_c": round(sum(values) / len(values), 4),
                "air_temperature_observations": len(values),
            }
        )
    return rows


def find_nearest_shutdown_plant(
    site: MonitoringSite,
    shutdown_plants: list[Plant],
) -> tuple[Plant | None, float | None]:
    if site.latitude is None or site.longitude is None:
        return None, None

    nearest_plant: Plant | None = None
    nearest_distance: float | None = None
    for plant in shutdown_plants:
        if plant.latitude is None or plant.longitude is None:
            continue
        distance = haversine_km(site.latitude, site.longitude, plant.latitude, plant.longitude)
        if nearest_distance is None or distance < nearest_distance:
            nearest_plant = plant
            nearest_distance = distance
    return nearest_plant, nearest_distance


def build_water_temperature_rows(
    sites: dict[str, MonitoringSite],
    shutdown_plants: list[Plant],
    treatment_radius_km: float,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    nearest_cache: dict[str, tuple[Plant | None, float | None]] = {}

    for row in read_csv_rows(WATER_FILE):
        if clean_text(row.get("observedPropertyDeterminandLabel")) != "Water temperature":
            continue
        site_id = clean_text(row.get("monitoringSiteIdentifier"))
        site = sites.get(site_id)
        year = parse_year(row.get("phenomenonTimeReferenceYear"))
        mean_temperature = parse_float(row.get("resultMeanValue"))
        if site is None or year is None or mean_temperature is None:
            continue

        if site_id not in nearest_cache:
            nearest_cache[site_id] = find_nearest_shutdown_plant(site, shutdown_plants)
        nearest_plant, nearest_distance = nearest_cache[site_id]
        is_treated = (
            nearest_plant is not None
            and nearest_distance is not None
            and nearest_distance <= treatment_radius_km
        )
        is_post_treatment = bool(is_treated and nearest_plant.shutdown_year and year >= nearest_plant.shutdown_year)

        rows.append(
            {
                "site_id": site.site_id,
                "site_name": site.site_name,
                "water_body_id": site.water_body_id,
                "water_body_name": site.water_body_name,
                "water_body_category": site.water_body_category,
                "site_latitude": site.latitude,
                "site_longitude": site.longitude,
                "year": year,
                "water_temperature_mean_c": mean_temperature,
                "water_temperature_min_c": parse_float(row.get("resultMinimumValue")),
                "water_temperature_max_c": parse_float(row.get("resultMaximumValue")),
                "water_temperature_observations": parse_year(row.get("resultNumberOfSamples")),
                "nearest_shutdown_plant_id": nearest_plant.plant_id if nearest_plant else "",
                "nearest_shutdown_plant_name": nearest_plant.plant_name if nearest_plant else "",
                "shutdown_year": nearest_plant.shutdown_year if nearest_plant else None,
                "distance_to_shutdown_plant_km": round(nearest_distance, 3) if nearest_distance is not None else None,
                "treatment_group": int(is_treated),
                "post_treatment": int(is_post_treatment),
                "did_interaction": int(is_treated and is_post_treatment),
            }
        )
    return rows


def build_did_panel_rows(
    water_rows: list[dict[str, object]],
    air_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    air_by_year = {row["year"]: row["air_temperature_de_mean_c"] for row in air_rows}
    panel_rows = []
    for row in water_rows:
        year = row["year"]
        if year not in air_by_year:
            continue
        panel_row = dict(row)
        panel_row["air_temperature_de_mean_c"] = air_by_year[year]
        panel_rows.append(panel_row)
    return panel_rows


def plants_to_rows(plants: list[Plant]) -> list[dict[str, object]]:
    return [
        {
            "plant_id": plant.plant_id,
            "plant_name": plant.plant_name,
            "block_name": plant.block_name,
            "state": plant.state,
            "capacity_mw": plant.capacity_mw,
            "commissioned_year": plant.commissioned_year,
            "shutdown_year": plant.shutdown_year,
            "status": plant.status,
            "latitude": plant.latitude,
            "longitude": plant.longitude,
        }
        for plant in plants
    ]


def sites_to_rows(sites: dict[str, MonitoringSite]) -> list[dict[str, object]]:
    return [
        {
            "site_id": site.site_id,
            "site_name": site.site_name,
            "water_body_id": site.water_body_id,
            "water_body_name": site.water_body_name,
            "water_body_category": site.water_body_category,
            "latitude": site.latitude,
            "longitude": site.longitude,
        }
        for site in sorted(sites.values(), key=lambda item: item.site_id)
    ]


def write_preview(path: Path, rows: list[dict[str, object]], preview_rows: int) -> None:
    columns = [
        "site_id",
        "water_body_name",
        "year",
        "water_temperature_mean_c",
        "air_temperature_de_mean_c",
        "nearest_shutdown_plant_name",
        "shutdown_year",
        "distance_to_shutdown_plant_km",
        "treatment_group",
        "post_treatment",
        "did_interaction",
    ]
    treated_rows = [row for row in rows if row.get("treatment_group") == 1]
    control_rows = [row for row in rows if row.get("treatment_group") == 0]
    sample_rows = (treated_rows[: preview_rows // 2] + control_rows[: preview_rows - preview_rows // 2])

    with path.open("w", encoding="utf-8") as file:
        file.write("# Clean DiD Panel Preview\n\n")
        file.write("| " + " | ".join(columns) + " |\n")
        file.write("| " + " | ".join("---" for _ in columns) + " |\n")
        for row in sample_rows:
            values = [str(row.get(column, "")) for column in columns]
            file.write("| " + " | ".join(values) + " |\n")


def main() -> None:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    nuclear_plants = load_nuclear_plants()
    shutdown_plants = [plant for plant in nuclear_plants if plant.shutdown_year is not None]
    sites = load_german_monitoring_sites()
    air_rows = build_air_temperature_rows()
    water_rows = build_water_temperature_rows(sites, shutdown_plants, args.treatment_radius_km)
    panel_rows = build_did_panel_rows(water_rows, air_rows)

    counts = {
        "nuclear_plants": write_csv(
            OUTPUT_DIR / "nuclear_plants_de_clean.csv",
            plants_to_rows(nuclear_plants),
            [
                "plant_id",
                "plant_name",
                "block_name",
                "state",
                "capacity_mw",
                "commissioned_year",
                "shutdown_year",
                "status",
                "latitude",
                "longitude",
            ],
        ),
        "monitoring_sites": write_csv(
            OUTPUT_DIR / "water_monitoring_sites_de_clean.csv",
            sites_to_rows(sites),
            [
                "site_id",
                "site_name",
                "water_body_id",
                "water_body_name",
                "water_body_category",
                "latitude",
                "longitude",
            ],
        ),
        "air_temperature_years": write_csv(
            OUTPUT_DIR / "air_temperature_de_annual_clean.csv",
            air_rows,
            ["year", "air_temperature_de_mean_c", "air_temperature_observations"],
        ),
        "water_temperature_rows": write_csv(
            OUTPUT_DIR / "water_temperature_de_annual_clean.csv",
            water_rows,
            [
                "site_id",
                "site_name",
                "water_body_id",
                "water_body_name",
                "water_body_category",
                "site_latitude",
                "site_longitude",
                "year",
                "water_temperature_mean_c",
                "water_temperature_min_c",
                "water_temperature_max_c",
                "water_temperature_observations",
                "nearest_shutdown_plant_id",
                "nearest_shutdown_plant_name",
                "shutdown_year",
                "distance_to_shutdown_plant_km",
                "treatment_group",
                "post_treatment",
                "did_interaction",
            ],
        ),
        "did_panel_rows": write_csv(
            OUTPUT_DIR / "did_panel_clean.csv",
            panel_rows,
            [
                "site_id",
                "site_name",
                "water_body_id",
                "water_body_name",
                "water_body_category",
                "site_latitude",
                "site_longitude",
                "year",
                "water_temperature_mean_c",
                "water_temperature_min_c",
                "water_temperature_max_c",
                "water_temperature_observations",
                "air_temperature_de_mean_c",
                "nearest_shutdown_plant_id",
                "nearest_shutdown_plant_name",
                "shutdown_year",
                "distance_to_shutdown_plant_km",
                "treatment_group",
                "post_treatment",
                "did_interaction",
            ],
        ),
    }

    write_preview(OUTPUT_DIR / "did_panel_preview.md", panel_rows, args.preview_rows)
    for name, count in counts.items():
        print(f"{name}: {count}")
    print(f"preview: {OUTPUT_DIR / 'did_panel_preview.md'}")


if __name__ == "__main__":
    main()
