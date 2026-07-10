"""Entry point: build the group assignment and every filtered analysis file.

Run from the repository root:

    python scripts/build_all.py

Each step prints a short summary. Steps whose raw inputs are not present locally
(Waterbase, GRDC) skip themselves with a hint instead of failing, so the rest of
the pipeline still runs.
"""

import sys
from pathlib import Path

# Make the `pipeline` package importable when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline import discharge, group_assignment, power_plants, waterbase, weather  # noqa: E402


def main() -> None:
    group_assignment.build()
    waterbase.build()
    discharge.build()
    weather.build()
    power_plants.build()


if __name__ == "__main__":
    main()
