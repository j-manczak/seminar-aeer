"""Quick test of individual modules."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("Testing imports...")

try:
    print("1. config...")
    from src import config
    print(f"   ✓ Loaded {len(config.OBSERVATIONS)} observations")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("2. data_loading...")
    from src.data_loading import load_temperature_file, find_station_files
    print("   ✓ Loaded")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("3. data_cleaning...")
    from src.data_cleaning import clean_temperature_data
    print("   ✓ Loaded")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("4. monthly_aggregation...")
    from src.monthly_aggregation import aggregate_to_monthly
    print("   ✓ Loaded")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("5. event_windows...")
    from src.event_windows import create_event_window
    print("   ✓ Loaded")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("6. did_analysis...")
    from src.did_analysis import run_2x2_did_regression
    print("   ✓ Loaded")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("7. visualization...")
    from src.visualization import plot_time_series
    print("   ✓ Loaded")
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting data loading...")
try:
    upstream_files = find_station_files(config.DATA_DIR, "Landshut-Birket", "temperature")
    print(f"Found {len(upstream_files)} temperature files for Landshut-Birket")
    if upstream_files:
        print(f"  {upstream_files[0]}")
except Exception as e:
    print(f"Error finding files: {e}")

print("\nAll module tests completed!")
