"""Filter EEA Waterbase annual values (water temperature, dissolved oxygen).

Reads the raw Part-2 files the user downloads into data/raw/waterbase/:

  Waterbase_v2020_1_T_WISE6_AggregatedData.csv        annual value per site
  Waterbase_v2020_1_S_WISE6_SpatialObject_DerivedData annual site coordinates

The AggregatedData table is already one annual value per site and determinand,
so no further aggregation is needed here -- we only join coordinates, restrict
to the study sites and the window, and label each row with its nearest reactor.

That table is large (>1 GB), so we stream it once and pick up both determinands
in a single pass instead of reading it per determinand. If the raw files are
missing (they are large and kept out of git), the builder prints a hint and
skips, so the rest of the pipeline still runs.
"""

from typing import Dict, List

from pipeline.config import (
    ANALYSIS_DIR,
    DISSOLVED_OXYGEN_LABEL,
    WATERBASE_DIR,
    WATER_TEMPERATURE_LABEL,
    WINDOW_END,
    WINDOW_START,
)
from pipeline.io_tables import stream_rows, to_float, to_int, write_table
from pipeline import sites

AGGREGATED_FILE = WATERBASE_DIR / "Waterbase_v2020_1_T_WISE6_AggregatedData.csv"
SPATIAL_FILE = WATERBASE_DIR / "Waterbase_v2020_1_S_WISE6_SpatialObject_DerivedData.csv"

# Determinand label -> (variable name for the header, output file name).
DETERMINANDS = {
    WATER_TEMPERATURE_LABEL: ("water temperature", "water_temperature_2006_2018.csv"),
    DISSOLVED_OXYGEN_LABEL: ("dissolved oxygen", "dissolved_oxygen_2006_2018.csv"),
}

OUTPUT_FIELDS = [
    "site_id",
    "site_name",
    "water_body_name",
    "latitude",
    "longitude",
    "year",
    "mean_value",
    "min_value",
    "max_value",
    "sample_count",
    "unit",
    "nearest_reactor",
    "nearest_group",
    "distance_km",
]


def _load_site_coordinates() -> Dict[str, dict]:
    """Map monitoringSiteIdentifier -> {name, water_body, lat, lon} for Germany."""
    coordinates: Dict[str, dict] = {}
    for row in stream_rows(SPATIAL_FILE):
        if row.get("countryCode", "").strip() != "DE":
            continue
        site_id = row.get("monitoringSiteIdentifier", "").strip()
        lat = to_float(row.get("lat"))
        lon = to_float(row.get("lon"))
        if not site_id or lat is None or lon is None:
            continue
        coordinates[site_id] = {
            "name": row.get("monitoringSiteName", "").strip(),
            "water_body": row.get("waterBodyName", "").strip(),
            "lat": lat,
            "lon": lon,
        }
    return coordinates


def _collect(coordinates: Dict[str, dict]) -> Dict[str, List[dict]]:
    """Stream the aggregated table once and gather rows per wanted determinand,
    joined to coordinates and restricted to the study sites and the window."""
    results: Dict[str, List[dict]] = {label: [] for label in DETERMINANDS}
    for row in stream_rows(AGGREGATED_FILE):
        label = row.get("observedPropertyDeterminandLabel", "").strip()
        if label not in results:
            continue
        site = coordinates.get(row.get("monitoringSiteIdentifier", "").strip())
        year = to_int(row.get("phenomenonTimeReferenceYear"))
        mean_value = to_float(row.get("resultMeanValue"))
        if site is None or year is None or mean_value is None:
            continue
        if not (WINDOW_START <= year <= WINDOW_END):
            continue
        matched = sites.match(site["lat"], site["lon"])
        if matched is None:
            continue
        reactor, distance = matched
        results[label].append(
            {
                "site_id": row.get("monitoringSiteIdentifier", "").strip(),
                "site_name": site["name"],
                "water_body_name": site["water_body"],
                "latitude": site["lat"],
                "longitude": site["lon"],
                "year": year,
                "mean_value": mean_value,
                "min_value": to_float(row.get("resultMinimumValue")),
                "max_value": to_float(row.get("resultMaximumValue")),
                "sample_count": to_int(row.get("resultNumberOfSamples")),
                "unit": row.get("resultUom", "").strip(),
                "nearest_reactor": reactor.reactor,
                "nearest_group": reactor.group,
                "distance_km": round(distance, 3),
            }
        )
    return results


def _header(variable: str, label: str) -> List[str]:
    return [
        f"Dataset: annual {variable} at German monitoring sites (EEA Waterbase v2020_1).",
        f"Source: data/raw/waterbase/ Aggregated + Spatial files, determinand '{label}'.",
        "Site filter: monitoring sites within the study radius of a study reactor.",
        f"Window filter: observation years {WINDOW_START}-{WINDOW_END} (inclusive).",
        "Added columns: nearest study reactor, its group and the distance in km.",
    ]


def build() -> None:
    if not AGGREGATED_FILE.exists() or not SPATIAL_FILE.exists():
        print("waterbase: raw files not found in data/raw/waterbase/, skipping "
              "water temperature and dissolved oxygen.")
        return

    coordinates = _load_site_coordinates()
    results = _collect(coordinates)
    for label, (variable, out_name) in DETERMINANDS.items():
        rows = results[label]
        count = write_table(ANALYSIS_DIR / out_name, _header(variable, label), OUTPUT_FIELDS, rows)
        years = sorted({r["year"] for r in rows})
        span = (years[0], years[-1]) if years else "no rows"
        print(f"{out_name}: {count} rows; years {span}")


if __name__ == "__main__":
    build()
