"""Build time-varying conventional thermal controls by monitoring site and year.

The goal is to reduce omitted-variable bias in the DiD: nearby non-nuclear
thermal plants can also heat rivers, so their active capacity should enter the
model as controls.
"""

from collections import defaultdict
from typing import Dict, List

from pipeline.config import ANALYSIS_DIR
from pipeline.geo import haversine_km
from pipeline.io_tables import read_rows, to_float, to_int, write_table

SITES_FILE = ANALYSIS_DIR / "water_quality_summer_by_site.csv"
PLANTS_FILE = ANALYSIS_DIR / "power_plants_2006_2018.csv"
OUT_FILE = ANALYSIS_DIR / "conventional_controls_by_site_year.csv"


def _is_active(commissioned_year: int, shutdown_year: int, year: int) -> bool:
    if commissioned_year is not None and commissioned_year > year:
        return False
    if shutdown_year is not None and shutdown_year < year:
        return False
    return True


def _weight(distance_km: float) -> float:
    # Smooth inverse-distance weighting (bounded at very short distance).
    return 1.0 / (distance_km + 1.0)


def build() -> None:
    if not SITES_FILE.exists() or not PLANTS_FILE.exists():
        print("conventional_controls: required inputs missing, skipping.")
        return

    site_rows = read_rows(SITES_FILE)
    plant_rows = read_rows(PLANTS_FILE)

    # Unique site-year rows from the observed panel (all determinands/positions).
    site_years: List[dict] = []
    seen = set()
    for row in site_rows:
        site_id = row.get("site_id", "").strip()
        year = to_int(row.get("year"))
        lat = to_float(row.get("latitude"))
        lon = to_float(row.get("longitude"))
        if not site_id or year is None or lat is None or lon is None:
            continue
        key = (site_id, year)
        if key in seen:
            continue
        seen.add(key)
        site_years.append(
            {
                "site_id": site_id,
                "year": year,
                "site_latitude": lat,
                "site_longitude": lon,
            }
        )

    plants = []
    for row in plant_rows:
        lat = to_float(row.get("latitude"))
        lon = to_float(row.get("longitude"))
        cap = to_float(row.get("capacity_mw"))
        if lat is None or lon is None or cap is None:
            continue
        plants.append(
            {
                "commissioned_year": to_int(row.get("commissioned_year")),
                "shutdown_year": to_int(row.get("shutdown_year")),
                "capacity_mw": cap,
                "latitude": lat,
                "longitude": lon,
            }
        )

    out_rows: List[Dict] = []
    for rec in site_years:
        site_id = rec["site_id"]
        year = rec["year"]
        lat = rec["site_latitude"]
        lon = rec["site_longitude"]

        cap_0_10 = 0.0
        cap_10_25 = 0.0
        cap_25_50 = 0.0
        cap_gt_50 = 0.0
        weighted = 0.0
        nearby_count = 0

        for plant in plants:
            if not _is_active(plant["commissioned_year"], plant["shutdown_year"], year):
                continue
            distance = haversine_km(lat, lon, plant["latitude"], plant["longitude"])
            cap = plant["capacity_mw"]
            weighted += cap * _weight(distance)

            if distance <= 10:
                cap_0_10 += cap
                nearby_count += 1
            elif distance <= 25:
                cap_10_25 += cap
                nearby_count += 1
            elif distance <= 50:
                cap_25_50 += cap
                nearby_count += 1
            else:
                cap_gt_50 += cap

        out_rows.append(
            {
                "site_id": site_id,
                "year": year,
                "conv_cap_0_10_mw": round(cap_0_10, 3),
                "conv_cap_10_25_mw": round(cap_10_25, 3),
                "conv_cap_25_50_mw": round(cap_25_50, 3),
                "conv_cap_gt_50_mw": round(cap_gt_50, 3),
                "conv_cap_weighted_mw": round(weighted, 6),
                "nearby_thermal_plant_count": nearby_count,
            }
        )

    header = [
        "Dataset: site-year conventional thermal controls for DiD.",
        "Built from data/processed/analysis/water_quality_summer_by_site.csv and",
        "data/processed/analysis/power_plants_2006_2018.csv.",
        "Capacity controls are active-year filtered using commissioned/shutdown year.",
        "Distance weighting uses capacity/(distance_km+1).",
    ]
    fieldnames = [
        "site_id",
        "year",
        "conv_cap_0_10_mw",
        "conv_cap_10_25_mw",
        "conv_cap_25_50_mw",
        "conv_cap_gt_50_mw",
        "conv_cap_weighted_mw",
        "nearby_thermal_plant_count",
    ]
    written = write_table(OUT_FILE, header, fieldnames, out_rows)
    print(f"conventional_controls_by_site_year.csv: {written} site-year rows")


if __name__ == "__main__":
    build()
