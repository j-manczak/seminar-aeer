"""Write data/processed/group_assignment.csv from the reactor master table."""

import csv

from pipeline.config import PROCESSED_DIR
from pipeline.reactors import GROUP_ORDER, REACTORS

FIELDNAMES = [
    "reactor",
    "block",
    "group",
    "river",
    "cooling_type",
    "commissioned_year",
    "shutdown_year",
    "rationale",
]


def build() -> None:
    path = PROCESSED_DIR / "group_assignment.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for reactor in REACTORS:
            writer.writerow(
                {
                    "reactor": reactor.reactor,
                    "block": reactor.block,
                    "group": reactor.group,
                    "river": reactor.river,
                    "cooling_type": reactor.cooling_type,
                    "commissioned_year": reactor.commissioned_year,
                    "shutdown_year": reactor.shutdown_year,
                    "rationale": reactor.rationale,
                }
            )

    print(f"group_assignment.csv: {len(REACTORS)} reactors")
    for group in GROUP_ORDER:
        members = [r.reactor for r in REACTORS if r.group == group]
        print(f"  {group}: {len(members)} -> {', '.join(members)}")


if __name__ == "__main__":
    build()
