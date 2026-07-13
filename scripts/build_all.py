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

from pipeline import (  # noqa: E402
    conventional_controls,
    discharge,
    group_assignment,
    power_plants,
    river_position,
    waterbase,
    weather,
)


def main() -> None:
    group_assignment.build()
    waterbase.build()
    discharge.build()
    river_position.build()  # adds same-river up/downstream position to the above
    weather.build()
    power_plants.build()
    conventional_controls.build()


if __name__ == "__main__":
    main()
