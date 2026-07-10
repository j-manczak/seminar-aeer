"""Tiny checks for the two raw-file parsers, run against sample fixtures.

These verify the GRDC and Waterbase parsing/filtering logic without needing the
real (large) downloads. Run from the repository root:

    python scripts/pipeline/tests/test_parsers.py
"""

import sys
from pathlib import Path

# Make the `pipeline` package importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline import discharge, waterbase  # noqa: E402

HERE = Path(__file__).resolve().parent


def test_discharge_parser():
    rows = discharge._parse_station_file(HERE / "sample_grdc_station.txt")
    # Only 2010 is inside the 2006-2018 window (2005 and 2019 dropped),
    # and the -999 value is treated as missing.
    assert len(rows) == 1, rows
    row = rows[0]
    assert row["year"] == 2010
    assert row["days_observed"] == 2
    assert row["discharge_min_m3_s"] == 150.25
    assert row["discharge_max_m3_s"] == 250.5
    assert row["discharge_mean_m3_s"] == round((250.5 + 150.25) / 2, 3)
    assert row["nearest_reactor"] == "Grohnde"
    print("discharge parser: OK")


def test_waterbase_filter():
    # Point the module at the sample fixtures instead of data/raw/waterbase/.
    waterbase.SPATIAL_FILE = HERE / "sample_waterbase_spatial.csv"
    waterbase.AGGREGATED_FILE = HERE / "sample_waterbase_aggregated.csv"
    coordinates = waterbase._load_site_coordinates()
    assert "DE_SITE_1" in coordinates
    assert "FR_SITE" not in coordinates  # non-German sites are dropped

    # A single streaming pass returns both determinands.
    results = waterbase._collect(coordinates)

    temperature = results["Water temperature"]
    # DE_SITE_1/2010 kept; 2019 out of window; FAR site out of radius; FR dropped.
    assert len(temperature) == 1, temperature
    assert temperature[0]["site_id"] == "DE_SITE_1"
    assert temperature[0]["nearest_reactor"] == "Brokdorf"

    oxygen = results["Dissolved oxygen"]
    assert len(oxygen) == 1 and oxygen[0]["mean_value"] == 9.8
    print("waterbase filter: OK")


if __name__ == "__main__":
    test_discharge_parser()
    test_waterbase_filter()
    print("all parser tests passed")
