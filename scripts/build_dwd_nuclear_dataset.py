#!/usr/bin/env python3
"""Build a DWD daily climate dataset for stations near nuclear power plants.

Pipeline steps:
1) Download DWD station list.
2) Select stations within a configurable radius of nuclear plants.
3) Download only ZIP files for selected stations.
4) Build one combined pandas DataFrame and save it as CSV.
"""

from __future__ import annotations

import argparse
import io
import math
import re
import zipfile
from pathlib import Path

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent

STATIONS_TXT_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
    "climate/daily/kl/recent/KL_Tageswerte_Beschreibung_Stationen.txt"
)
DWD_RECENT_INDEX_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
    "climate/daily/kl/recent/"
)
DWD_HISTORICAL_INDEX_URL = (
    "https://opendata.dwd.de/climate_environment/CDC/observations_germany/"
    "climate/daily/kl/historical/"
)

LOCAL_STATIONS_TXT = PROJECT_ROOT / "data" / "raw" / "weather" / "KL_Tageswerte_Beschreibung_Stationen.txt"
LOCAL_STATIONS_CSV = PROJECT_ROOT / "data" / "raw" / "weather" / "stations_DWD.csv"
NUCLEAR_PLANTS_CSV = PROJECT_ROOT / "data" / "processed" / "nuclear_plants_de_clean.csv"
OUTPUT_CSV = PROJECT_ROOT / "data" / "processed" / "dwd_kl_daily_near_nuclear.csv"

ZIP_LINK_RE = re.compile(
    r'href="(tageswerte_KL_(\d{5})(?:_[0-9]{8}_[0-9]{8})?_(akt|hist)\.zip)"',
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--radius-km",
        type=float,
        default=30.0,
        help="Keep DWD stations within this distance from the nearest nuclear plant.",
    )
    parser.add_argument(
        "--dataset",
        choices=["historical", "recent"],
        default="historical",
        help="DWD dataset variant to download for selected stations.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=45,
        help="HTTP timeout for DWD requests.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=OUTPUT_CSV,
        help="Output CSV path for the combined daily climate DataFrame.",
    )
    return parser.parse_args()


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute distance between two points in kilometers."""
    earth_radius_km = 6371.0
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    return 2 * earth_radius_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def download_text_file(url: str, destination: Path, timeout_seconds: int) -> None:
    """Download a text file and save it locally."""
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()
    destination.write_bytes(response.content)


def load_stations_dataframe_from_txt(txt_path: Path) -> pd.DataFrame:
    """Load station metadata from DWD fixed-width TXT into a DataFrame."""
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

    df = pd.read_fwf(
        txt_path,
        skiprows=2,
        header=None,
        names=column_names,
        encoding="latin1",
        dtype=str,
    )
    df = df.dropna(how="all").copy()
    for col in df.columns:
        df[col] = df[col].astype("string").str.strip()
    df = df.reset_index(drop=True)

    df["Stations_id"] = df["Stations_id"].str.zfill(5)
    df["geoBreite"] = pd.to_numeric(df["geoBreite"], errors="coerce")
    df["geoLaenge"] = pd.to_numeric(df["geoLaenge"], errors="coerce")

    return df


def load_nuclear_plants(path: Path) -> pd.DataFrame:
    """Load nuclear plant coordinates from processed project data."""
    df = pd.read_csv(path)
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"]).copy()
    return df


def select_stations_near_nuclear(
    stations_df: pd.DataFrame,
    nuclear_df: pd.DataFrame,
    radius_km: float,
) -> pd.DataFrame:
    """Return stations within radius_km of at least one nuclear plant."""
    selected_rows: list[dict[str, object]] = []

    nuclear_points = [
        (row["latitude"], row["longitude"], row.get("plant_name", ""), row.get("plant_id", ""))
        for _, row in nuclear_df.iterrows()
    ]

    for _, station in stations_df.iterrows():
        lat = station.get("geoBreite")
        lon = station.get("geoLaenge")
        if pd.isna(lat) or pd.isna(lon):
            continue

        nearest_distance: float | None = None
        nearest_name = ""
        nearest_id = ""

        for n_lat, n_lon, n_name, n_id in nuclear_points:
            distance = haversine_km(float(lat), float(lon), float(n_lat), float(n_lon))
            if nearest_distance is None or distance < nearest_distance:
                nearest_distance = distance
                nearest_name = str(n_name)
                nearest_id = str(n_id)

        if nearest_distance is None or nearest_distance > radius_km:
            continue

        selected_rows.append(
            {
                **station.to_dict(),
                "distance_to_nearest_nuclear_km": round(nearest_distance, 3),
                "nearest_nuclear_plant": nearest_name,
                "nearest_nuclear_plant_id": nearest_id,
            }
        )

    return pd.DataFrame(selected_rows)


def discover_station_zip_links(index_url: str, timeout_seconds: int) -> dict[str, str]:
    """Parse station ZIP links from a DWD index page and map station_id -> ZIP URL."""
    response = requests.get(index_url, timeout=timeout_seconds)
    response.raise_for_status()
    html = response.text

    links: dict[str, str] = {}
    for file_name, station_id, _variant in ZIP_LINK_RE.findall(html):
        links[station_id] = index_url + file_name

    return links


def pick_product_txt_member(zip_file: zipfile.ZipFile, station_id: str) -> str | None:
    """Find the product TXT member inside station ZIP archives."""
    station_id = station_id.zfill(5)
    candidates = [
        name
        for name in zip_file.namelist()
        if name.lower().startswith("produkt_klima_tag_")
        and name.lower().endswith(f"_{station_id}.txt")
    ]
    if candidates:
        return sorted(candidates)[0]

    fallback = [name for name in zip_file.namelist() if name.lower().startswith("produkt_klima_tag_")]
    if fallback:
        return sorted(fallback)[0]

    return None


def load_station_daily_from_zip(zip_bytes: bytes, station_id: str) -> pd.DataFrame:
    """Load one station daily KL file from ZIP bytes into DataFrame."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        member = pick_product_txt_member(zf, station_id)
        if member is None:
            raise ValueError(f"No produkt_klima_tag_*.txt found for station {station_id}")

        with zf.open(member) as handle:
            df = pd.read_csv(
                handle,
                sep=";",
                encoding="latin1",
                dtype=str,
                engine="python",
            )

    df.columns = [str(col).strip() for col in df.columns]

    # Drop extra unnamed columns caused by trailing semicolons.
    drop_cols = [col for col in df.columns if col.lower().startswith("unnamed")]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    for col in df.columns:
        df[col] = df[col].astype("string").str.strip()

    df = df[df["MESS_DATUM"].notna()].copy() if "MESS_DATUM" in df.columns else df.copy()
    return df


def build_combined_daily_dataframe(
    selected_stations_df: pd.DataFrame,
    zip_links: dict[str, str],
    timeout_seconds: int,
) -> tuple[pd.DataFrame, list[str]]:
    """Download selected station ZIPs and return one combined DataFrame."""
    frames: list[pd.DataFrame] = []
    missing_station_ids: list[str] = []

    for _, station in selected_stations_df.iterrows():
        station_id = str(station["Stations_id"]).zfill(5)
        zip_url = zip_links.get(station_id)
        if not zip_url:
            missing_station_ids.append(station_id)
            continue

        response = requests.get(zip_url, timeout=timeout_seconds)
        response.raise_for_status()
        station_df = load_station_daily_from_zip(response.content, station_id)

        station_df["station_id"] = station_id
        station_df["station_name"] = station.get("Stationsname")
        station_df["station_latitude"] = station.get("geoBreite")
        station_df["station_longitude"] = station.get("geoLaenge")
        station_df["nearest_nuclear_plant"] = station.get("nearest_nuclear_plant")
        station_df["nearest_nuclear_plant_id"] = station.get("nearest_nuclear_plant_id")
        station_df["distance_to_nearest_nuclear_km"] = station.get("distance_to_nearest_nuclear_km")

        if "MESS_DATUM" in station_df.columns:
            station_df["MESS_DATUM"] = pd.to_datetime(station_df["MESS_DATUM"], format="%Y%m%d", errors="coerce")

        frames.append(station_df)

    if not frames:
        return pd.DataFrame(), missing_station_ids

    combined = pd.concat(frames, ignore_index=True)
    return combined, missing_station_ids


def main() -> None:
    """Run the complete DWD station filtering and dataset assembly pipeline."""
    args = parse_args()
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)

    print("Step 1/4: Downloading DWD station list...")
    try:
        download_text_file(STATIONS_TXT_URL, LOCAL_STATIONS_TXT, args.timeout_seconds)
    except requests.RequestException as exc:
        print("Failed to download station list.")
        print(f"Details: {exc}")
        return

    stations_df = load_stations_dataframe_from_txt(LOCAL_STATIONS_TXT)
    stations_df.to_csv(LOCAL_STATIONS_CSV, index=False, encoding="utf-8-sig")
    print(f"Saved station CSV: {LOCAL_STATIONS_CSV}")
    print(f"Station count (all): {len(stations_df)}")

    if not NUCLEAR_PLANTS_CSV.exists():
        print(f"Missing required file: {NUCLEAR_PLANTS_CSV}")
        return

    print("Step 2/4: Selecting stations near nuclear plants...")
    nuclear_df = load_nuclear_plants(NUCLEAR_PLANTS_CSV)
    selected = select_stations_near_nuclear(stations_df, nuclear_df, args.radius_km)
    if selected.empty:
        print(f"No stations found within {args.radius_km} km of nuclear plants.")
        return

    selected_stations_path = args.output_csv.parent / (
        f"dwd_stations_near_nuclear_{int(args.radius_km)}km.csv"
    )
    selected.to_csv(selected_stations_path, index=False, encoding="utf-8-sig")
    print(f"Selected stations: {len(selected)}")
    print(f"Saved selected stations: {selected_stations_path}")

    print("Step 3/4: Discovering and downloading only required ZIP files...")
    index_url = DWD_HISTORICAL_INDEX_URL if args.dataset == "historical" else DWD_RECENT_INDEX_URL
    try:
        zip_links = discover_station_zip_links(index_url, args.timeout_seconds)
    except requests.RequestException as exc:
        print("Failed to fetch DWD ZIP index.")
        print(f"Details: {exc}")
        return

    print(f"Available ZIP links in '{args.dataset}' index: {len(zip_links)}")

    print("Step 4/4: Building combined DataFrame...")
    try:
        combined_df, missing_station_ids = build_combined_daily_dataframe(
            selected_stations_df=selected,
            zip_links=zip_links,
            timeout_seconds=args.timeout_seconds,
        )
    except requests.RequestException as exc:
        print("A ZIP download failed.")
        print(f"Details: {exc}")
        return
    except Exception as exc:
        print("Failed while parsing ZIP content.")
        print(f"Details: {exc}")
        return

    if combined_df.empty:
        print("No daily records were assembled.")
        return

    combined_df.to_csv(args.output_csv, index=False, encoding="utf-8-sig")
    print(f"Combined rows: {len(combined_df)}")
    print(f"Combined columns: {len(combined_df.columns)}")
    print(f"Output CSV: {args.output_csv}")

    if missing_station_ids:
        print(f"Stations without matching ZIP in '{args.dataset}': {len(missing_station_ids)}")
        print(f"Missing IDs sample: {missing_station_ids[:15]}")


if __name__ == "__main__":
    main()
