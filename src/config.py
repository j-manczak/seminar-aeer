"""Central configuration for the nuclear power plant shutdown analysis.

All key assumptions, plant/station mappings, shutdown dates, and file paths
are defined here to ensure consistency across the entire analysis pipeline.
"""

from pathlib import Path
from datetime import datetime
import pandas as pd

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data_temperature_oxygen"
SRC_DIR = PROJECT_ROOT / "src"
FINAL_RESULTS_DIR = PROJECT_ROOT / "final_results"
RESULTS_DIR = FINAL_RESULTS_DIR / "results"
TABLES_DIR = FINAL_RESULTS_DIR / "tables"
FIGURES_DIR = FINAL_RESULTS_DIR / "figures"
REPORTS_DIR = FINAL_RESULTS_DIR / "reports"
DATA_QUALITY_DIR = FINAL_RESULTS_DIR / "data_quality"

# Ensure directories exist
for d in [RESULTS_DIR, TABLES_DIR, FIGURES_DIR, REPORTS_DIR, DATA_QUALITY_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Analysis window configuration
MAIN_WINDOW_YEARS = 5
SENSITIVITY_WINDOWS = [3, 4, 5, 6, 7]

# The eight nuclear shutdown observations
# Source: Wikipedia, BASE (Bundesamt für Sicherheit und Entsorgungswirtschaft), 
# and official plant documentation
OBSERVATIONS = [
    {
        "obs_id": 1,
        "plant": "Isar 1",
        "river": "Isar",
        "upstream_station": "Landshut-Birket",
        "downstream_station": "Landau",
        "shutdown_date": datetime(2011, 8, 6),
        "shutdown_year": 2011,
        "temp_file_pattern": "2011-5_C",
        "oxygen_file_pattern": "2011-5_CO",
    },
    {
        "obs_id": 2,
        "plant": "Neckarwestheim 1",
        "river": "Neckar",
        "upstream_station": "Lauffen",
        "downstream_station": "Besigheim",
        "shutdown_date": datetime(2011, 8, 6),
        "shutdown_year": 2011,
        "temp_file_pattern": "2011-5_C",
        "oxygen_file_pattern": "2011-5_CO",
    },
    {
        "obs_id": 3,
        "plant": "Philippsburg 1",
        "river": "Rhine",
        "upstream_station": "Karlsruhe",
        "downstream_station": "Mannheim",
        "shutdown_date": datetime(2011, 8, 6),
        "shutdown_year": 2011,
        "temp_file_pattern": "2011-5_C",
        "oxygen_file_pattern": "2011-5_CO",
    },
    {
        "obs_id": 4,
        "plant": "Gundremmingen B",
        "river": "Danube",
        "upstream_station": "Neu-Ulm",
        "downstream_station": "Donauwörth",
        "shutdown_date": datetime(2017, 12, 31),
        "shutdown_year": 2017,
        "temp_file_pattern": None,  # Will check availability
        "oxygen_file_pattern": None,
    },
    {
        "obs_id": 5,
        "plant": "Philippsburg 2",
        "river": "Rhine",
        "upstream_station": "Karlsruhe",
        "downstream_station": "Mannheim",
        "shutdown_date": datetime(2019, 12, 31),
        "shutdown_year": 2019,
        "temp_file_pattern": "2019-5_C",
        "oxygen_file_pattern": "2019-5_CO",
    },
    {
        "obs_id": 6,
        "plant": "Gundremmingen C",
        "river": "Danube",
        "upstream_station": "Neu-Ulm",
        "downstream_station": "Donauwörth",
        "shutdown_date": datetime(2021, 12, 31),
        "shutdown_year": 2021,
        "temp_file_pattern": None,
        "oxygen_file_pattern": None,
    },
    {
        "obs_id": 7,
        "plant": "Isar 2",
        "river": "Isar",
        "upstream_station": "Landshut-Birket",
        "downstream_station": "Landau",
        "shutdown_date": datetime(2023, 4, 15),
        "shutdown_year": 2023,
        "temp_file_pattern": "2023-5_C",
        "oxygen_file_pattern": "2023-5_CO",
    },
    {
        "obs_id": 8,
        "plant": "Neckarwestheim 2",
        "river": "Neckar",
        "upstream_station": "Lauffen",
        "downstream_station": "Besigheim",
        "shutdown_date": datetime(2023, 4, 15),
        "shutdown_year": 2023,
        "temp_file_pattern": "2023-5_C",
        "oxygen_file_pattern": "2023-5_CO",
    },
]

# Create a DataFrame for easy reference
OBSERVATIONS_DF = pd.DataFrame(OBSERVATIONS)

# Station name mappings (for matching file names with station names)
STATION_NAME_MAP = {
    "Landshut_Birket": "Landshut-Birket",
    "Landshut-Birket": "Landshut-Birket",
    "Landau": "Landau",
    "Lauffen": "Lauffen",
    "Besigheim": "Besigheim",
    "Karlsruhe": "Karlsruhe",
    "Mannheim": "Mannheim",
    "Neu_Ulm": "Neu-Ulm",
    "Donaworth": "Donauwörth",
    "Donauworth": "Donauwörth",
}

# River mapping for discharge / context
RIVERS = {
    "Isar": {"country": "Germany", "notes": "Tributary of the Danube"},
    "Neckar": {"country": "Germany", "notes": "Tributary of the Rhine"},
    "Rhine": {"country": "Germany", "notes": "Main European river"},
    "Danube": {"country": "Germany", "notes": "Second-largest river in Europe"},
}

# Temperature and oxygen units
TEMPERATURE_UNIT = "°C"
OXYGEN_UNIT = "mg/L"

# Statistical configuration
CONFIDENCE_LEVEL = 0.95

print(f"Configuration loaded: {len(OBSERVATIONS)} observations")
print(f"Analysis window: ±{MAIN_WINDOW_YEARS} years")
print(f"Sensitivity windows: {SENSITIVITY_WINDOWS}")
