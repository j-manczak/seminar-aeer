#!/usr/bin/env python3
"""Download the DWD weather station list and save it as CSV.

The script:
1) downloads the TXT file directly from the internet (requests),
2) saves it in the same directory as the script,
3) loads the data into pandas,
4) prints basic dataset information,
5) saves the result as stations_DWD.csv in data/raw/weather.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

# DWD source URL.
DWD_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
    "climate/daily/kl/recent/KL_Tageswerte_Beschreibung_Stationen.txt"
)

# Output file names saved in data/raw/weather.
TXT_FILENAME = "KL_Tageswerte_Beschreibung_Stationen.txt"
CSV_FILENAME = "stations_DWD.csv"


def download_station_file(url: str, output_path: Path, timeout_seconds: int = 30) -> None:
    """Download the station file from the internet and save it locally.

    Raises:
        requests.RequestException: If an HTTP/network error occurs.
    """
    # requests.get(...) performs an HTTP GET request to the data source.
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()  # Raise an exception on 4xx/5xx responses.

    # Save the raw TXT file content as bytes.
    output_path.write_bytes(response.content)


def load_stations_to_dataframe(txt_path: Path) -> pd.DataFrame:
    """Load the DWD station TXT file into a pandas DataFrame.

    The DWD file uses fixed-width columns, so read_fwf is used.
    """
    # Explicitly define columns because the file uses fixed-width formatting.
    column_names = [
        "Stations_id",
        "von_datum",
        "bis_datum",
        "Stationshoehe",
        "geoBreite",
        "geoLaenge",
        "Stationsname",
        "Bundesland",
        "Abgabe",
    ]

    # skiprows=2 skips the technical header and dashed separator line.
    # header=None ensures the first data row is not treated as a header.
    df = pd.read_fwf(
        txt_path,
        skiprows=2,
        header=None,
        names=column_names,
        encoding="latin1",
        dtype=str,
    )

    # Remove blank rows (the DWD file may include spacing between records).
    df = df.dropna(how="all").copy()

    # Trim extra whitespace in all text columns.
    for col in df.columns:
        df[col] = df[col].astype("string").str.strip()

    # Normalize column names for consistency.
    df.columns = [str(col).strip() for col in df.columns]

    # Reset index after dropping blank rows.
    df = df.reset_index(drop=True)

    return df


def main() -> None:
    """Main entry point that orchestrates the full workflow."""
    project_root = Path(__file__).resolve().parents[1]
    weather_dir = project_root / "data" / "raw" / "weather"
    weather_dir.mkdir(parents=True, exist_ok=True)
    txt_path = weather_dir / TXT_FILENAME
    csv_path = weather_dir / CSV_FILENAME

    # Handle download errors as required (try/except for requests).
    try:
        print(f"Downloading file from: {DWD_URL}")
        download_station_file(DWD_URL, txt_path)
        print(f"TXT file saved: {txt_path}")
    except requests.RequestException as exc:
        print("Error while downloading the file from the internet.")
        print(f"Details: {exc}")
        return

    # Load data and save CSV output.
    try:
        df = load_stations_to_dataframe(txt_path)

        # Print required output summary.
        print("\nColumn names:")
        print(df.columns.tolist())

        print("\nNumber of stations:")
        print(len(df))

        print("\nFirst 10 rows:")
        print(df.head(10))

        # Save CSV in the same directory as the script.
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"\nCSV file saved: {csv_path}")
    except Exception as exc:
        print("Error while processing data or saving CSV.")
        print(f"Details: {exc}")


if __name__ == "__main__":
    main()
