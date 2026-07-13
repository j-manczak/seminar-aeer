"""Shared configuration for the difference-in-differences data pipeline.

Everything the other modules need to agree on lives here: the study window,
the spatial radius that defines "near a study reactor", and the input/output
paths. Change a value once and the whole pipeline follows.
"""

from pathlib import Path

# scripts/pipeline/config.py -> repo root is two levels up.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
ANALYSIS_DIR = PROCESSED_DIR / "analysis"

# Raw inputs the user places locally (kept out of git; see .gitignore).
WATERBASE_DIR = RAW_DIR / "waterbase"
DISCHARGE_DIR = RAW_DIR / "discharge"

# Observation window, inclusive on both ends.
WINDOW_START = 2006
WINDOW_END = 2018

# A monitoring site or plant belongs to a study reactor when it lies within this
# many kilometres of it. Matches scripts/prepare_data.py.
SITE_RADIUS_KM = 50.0

# Weather is a regional covariate, not a local treatment. 50 km already gives
# every study site several stations (the nearest to Unterweser is ~9 km); widen
# this if a site ever needs more regional support.
WEATHER_RADIUS_KM = 50.0

# Waterbase determinand labels (column observedPropertyDeterminandLabel).
# If a fresh Waterbase release renames these, adjust them here only.
WATER_TEMPERATURE_LABEL = "Water temperature"
DISSOLVED_OXYGEN_LABEL = "Dissolved oxygen"

# DWD open-data endpoints for the daily climate (KL) download.
DWD_KL_HISTORICAL_INDEX = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
    "climate/daily/kl/historical/"
)
DWD_STATIONS_CSV = RAW_DIR / "weather" / "stations_DWD.csv"
DWD_DAILY_CSV = PROCESSED_DIR / "dwd_kl_daily_near_nuclear.csv"
