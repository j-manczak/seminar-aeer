"""Filter and aggregate DWD daily weather to station-month summaries.

Reads the processed DWD extract (data/processed/dwd_kl_daily_near_nuclear.csv),
keeps stations near a study reactor and dates inside the window, and condenses
the >100k daily rows to one row per station and calendar month. Monthly matches
the resolution of the water outcomes and keeps the file small.
"""

from collections import defaultdict
from typing import Dict, List

from pipeline.config import ANALYSIS_DIR, PROCESSED_DIR, WINDOW_END, WINDOW_START
from pipeline.io_tables import read_rows, to_float, write_table
from pipeline import sites

SOURCE_FILE = PROCESSED_DIR / "dwd_kl_daily_near_nuclear.csv"

OUTPUT_FIELDS = [
    "station_id",
    "station_name",
    "latitude",
    "longitude",
    "year",
    "month",
    "air_temp_mean_c",
    "air_temp_min_c",
    "air_temp_max_c",
    "precipitation_sum_mm",
    "wind_speed_mean_m_s",
    "days_observed",
    "nearest_reactor",
    "nearest_group",
    "distance_km",
]

# Which daily columns feed which monthly statistic.
_DAILY_COLUMNS = {
    "temp_mean": "temperature_celsius",
    "temp_min": "min_temperature_celsius",
    "temp_max": "max_temperature_celsius",
    "precip": "precipitation_mm",
    "wind": "wind_speed_m_s",
}


def _mean(values: List[float]):
    return round(sum(values) / len(values), 3) if values else None


def build() -> None:
    if not SOURCE_FILE.exists():
        print("weather: source file not found, skipping.")
        return

    # (station_id, year, month) -> collected daily values
    buckets: Dict[tuple, dict] = {}
    for row in read_rows(SOURCE_FILE):
        date = (row.get("date") or "").strip()
        lat = to_float(row.get("latitude"))
        lon = to_float(row.get("longitude"))
        if len(date) < 7 or lat is None or lon is None:
            continue
        year = int(date[:4])
        if not (WINDOW_START <= year <= WINDOW_END):
            continue
        matched = sites.match(lat, lon)
        if matched is None:
            continue
        reactor, distance = matched

        key = (row.get("station_id"), year, int(date[5:7]))
        bucket = buckets.get(key)
        if bucket is None:
            bucket = {
                "station_id": row.get("station_id"),
                "station_name": row.get("station_name"),
                "latitude": lat,
                "longitude": lon,
                "year": year,
                "month": int(date[5:7]),
                "nearest_reactor": reactor.reactor,
                "nearest_group": reactor.group,
                "distance_km": round(distance, 3),
                "values": defaultdict(list),
            }
            buckets[key] = bucket
        for name, column in _DAILY_COLUMNS.items():
            value = to_float(row.get(column))
            if value is not None:
                bucket["values"][name].append(value)

    rows: List[dict] = []
    for bucket in buckets.values():
        values = bucket["values"]
        rows.append(
            {
                "station_id": bucket["station_id"],
                "station_name": bucket["station_name"],
                "latitude": bucket["latitude"],
                "longitude": bucket["longitude"],
                "year": bucket["year"],
                "month": bucket["month"],
                "air_temp_mean_c": _mean(values["temp_mean"]),
                "air_temp_min_c": min(values["temp_min"]) if values["temp_min"] else None,
                "air_temp_max_c": max(values["temp_max"]) if values["temp_max"] else None,
                "precipitation_sum_mm": round(sum(values["precip"]), 2) if values["precip"] else None,
                "wind_speed_mean_m_s": _mean(values["wind"]),
                "days_observed": len(values["temp_mean"]),
                "nearest_reactor": bucket["nearest_reactor"],
                "nearest_group": bucket["nearest_group"],
                "distance_km": bucket["distance_km"],
            }
        )
    rows.sort(key=lambda r: (r["station_id"], r["year"], r["month"]))

    header = [
        "Dataset: DWD daily climate observations, aggregated to station-month summaries.",
        "Source: data/processed/dwd_kl_daily_near_nuclear.csv",
        "Site filter: stations within the study radius of a study reactor.",
        f"Window filter: dates in {WINDOW_START}-{WINDOW_END} (inclusive).",
        "Note: the daily extract only spans 2005-2015, so the window is 2006-2015 here.",
        "Note: no station within the radius of the treatment site Unterweser (Biblis is covered).",
        "Added columns: nearest study reactor, its group and the distance in km.",
    ]
    count = write_table(ANALYSIS_DIR / "weather_2006_2018.csv", header, OUTPUT_FIELDS, rows)
    print(f"weather_2006_2018.csv: {count} station-month rows")


if __name__ == "__main__":
    build()
