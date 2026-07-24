"""Configuration for 2×2 DiD analysis framework.

This module defines extensible parameters for shutdown year analysis.
To analyze a different shutdown year:

1. Create a new config (e.g., config_2003.py) copying this template
2. Modify SHUTDOWN_YEAR and other parameters as needed
3. Import the config in your analysis script
4. Rerun analysis

Example usage in custom script:
    from config_2011 import SHUTDOWN_YEAR, DISTANCE_THRESHOLDS_KM
"""

# Which year's shutdowns to analyze
SHUTDOWN_YEAR = 2011

# Distance thresholds for sensitivity analysis (km)
# For 2011: limited data makes close proximity focus necessary
DISTANCE_THRESHOLDS_KM = [5.0, 10.0, 20.0, 30.0, 50.0]

# Minimum observations per period (pre/post shutdown)
# For 2011: relaxed to 1 due to data sparsity
# For older shutdowns with more data: consider increasing to 2-3
MIN_OBS_PER_PERIOD = 1

# Which outcome to analyze
OUTCOME = "water_temperature"  # Alternative: "dissolved_oxygen", "ph"

# Analysis period (can constrain to years with better data)
# Set to None for all available data
YEAR_MIN = None  # e.g., 2006 to exclude early/sparse data
YEAR_MAX = None  # e.g., 2018 to exclude recent sparse data

# Regression specification options
USE_TWFE = False  # Two-way Fixed Effects (requires multiple observations per cell)
CLUSTER_BY_SITE = True  # Cluster standard errors at station level
