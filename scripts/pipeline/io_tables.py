"""CSV reading/writing helpers with a documented comment header.

Every filtered output file starts with a few ``#`` comment lines that record
which filter produced it, so the provenance travels with the data. These
helpers keep that behaviour in one place.
"""

import csv
from pathlib import Path
from typing import Iterable, List, Optional


def read_rows(path: Path) -> List[dict]:
    """Read a CSV into a list of dicts, skipping any leading ``#`` comments."""
    with path.open(newline="", encoding="utf-8-sig") as handle:
        lines = [line for line in handle if not line.startswith("#")]
    return list(csv.DictReader(lines))


def write_table(path: Path, header_comments: List[str], fieldnames: List[str], rows: Iterable[dict]) -> int:
    """Write ``rows`` to ``path`` with a ``#`` comment header. Returns row count."""
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        for line in header_comments:
            handle.write(f"# {line}\n")
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})
            written += 1
    return written


def to_float(value: Optional[str]) -> Optional[float]:
    """Parse a float, returning None for empty or non-numeric input."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def to_int(value: Optional[str]) -> Optional[int]:
    """Parse an int via float (handles '2011.0'), None for empty/non-numeric."""
    number = to_float(value)
    return int(number) if number is not None else None
