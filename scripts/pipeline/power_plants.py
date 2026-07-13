"""Filter conventional thermal power plants near the study sites.

These plants are potential thermal confounders: their own waste-heat discharge
and their on/off switching during the window can move river temperature
independently of the nuclear moratorium. We keep the plants within the study
radius of a reactor whose operating life overlaps the window.
"""

from typing import List

from pipeline.config import ANALYSIS_DIR, PROCESSED_DIR, WINDOW_END, WINDOW_START
from pipeline.io_tables import read_rows, to_float, to_int, write_table
from pipeline import sites

SOURCE_FILE = PROCESSED_DIR / "conventional_plants_de_relevant_clean.csv"


def _overlaps_window(commissioned: int, shutdown: int) -> bool:
    if commissioned is not None and commissioned > WINDOW_END:
        return False
    if shutdown is not None and shutdown < WINDOW_START:
        return False
    return True


def build() -> None:
    if not SOURCE_FILE.exists():
        print("power_plants: source file not found, skipping.")
        return

    source_rows = read_rows(SOURCE_FILE)
    output: List[dict] = []
    for row in source_rows:
        lat = to_float(row.get("latitude"))
        lon = to_float(row.get("longitude"))
        if lat is None or lon is None:
            continue
        if not _overlaps_window(to_int(row.get("commissioned_year")), to_int(row.get("shutdown_year"))):
            continue
        matched = sites.match(lat, lon)
        if matched is None:
            continue
        reactor, distance = matched
        enriched = dict(row)
        enriched["nearest_reactor"] = reactor.reactor
        enriched["nearest_group"] = reactor.group
        enriched["distance_km"] = round(distance, 3)
        output.append(enriched)

    fieldnames = list(source_rows[0].keys()) + ["nearest_reactor", "nearest_group", "distance_km"]
    header = [
        "Dataset: conventional thermal power plants (Open Power System Data).",
        "Source: data/processed/conventional_plants_de_relevant_clean.csv",
        "Site filter: plants within the study radius of a study reactor.",
        f"Window filter: operating life overlaps {WINDOW_START}-{WINDOW_END}.",
        "Purpose: potential thermal confounders near the study rivers.",
        "Added columns: nearest study reactor, its group and the distance in km.",
    ]
    count = write_table(ANALYSIS_DIR / "power_plants_2006_2018.csv", header, fieldnames, output)
    print(f"power_plants_2006_2018.csv: {count} plants near study sites")


if __name__ == "__main__":
    build()
