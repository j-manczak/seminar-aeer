"""One station table for every river temperature source the study uses.

Two sources are combined and placed on the real river network, so the maps and
the estimation always talk about the same gauges:

``gkd``        Bavarian Gewässerkundlicher Dienst — *daily* means, back to the
               1980s at many gauges. The only source that reaches before 2011.
``waterbase``  EEA Waterbase v2025 disaggregated, German sites, filtered to the
               river water-body category (``RW``). Useful from 2020 onward only;
               kept so the newer shutdowns and the map stay comparable.

The ``RW`` filter matters. Waterbase mixes groundwater (``GW``), drinking water
(``TW``) and lake (``LW``) monitoring points into the same file, and hundreds of
German groundwater wells sit within a kilometre of a river centre-line. Without
the filter they are silently treated as river gauges — which is how the earlier
analysis produced "river temperature" for years in which Germany reported none.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from pipeline import river_network
from pipeline.config import PROCESSED_DIR, RAW_DIR

GKD_PANEL = PROCESSED_DIR / "gkd_water_temperature_daily.csv"
WATERBASE_SITES = RAW_DIR / "waterbase" / "de_sites_raw.csv"
WATERBASE_SAMPLES = RAW_DIR / "waterbase" / "de_samples_raw.csv"

MAX_OFFSET_M = 2500.0
# Without a water-body name to check against, only accept a site sitting almost
# exactly on the centre-line.
UNNAMED_MAX_OFFSET_M = 300.0

# German river-name tokens per study river, as they appear in Waterbase.
RIVER_TOKENS = {
    "Rhine": "RHEIN", "Danube": "DONAU", "Main": "MAIN", "Neckar": "NECKAR",
    "Isar": "ISAR", "Weser": "WESER", "Elbe": "ELBE", "Ems": "EMS",
}
# Leading qualifiers that describe a reach rather than name the river.
_QUALIFIERS = {
    "OBERER", "OBERE", "OBERH", "UNTERER", "UNTERE", "UNTERH", "MITTLERE", "MITTLERER",
    "ALTER", "ALTE", "FREIFLIESSENDE", "FREIFLIESSENDER", "TIDE", "LINKE", "RECHTE",
    "NOERDLICHE", "SUEDLICHE", "GROSSE", "KLEINE", "DER", "DIE", "DAS", "AM", "IM",
}
_PLACEHOLDER_NAMES = {"", "NAME", "KEIN NAME", "UNBEKANNT", "NAN"}


def gkd_stations() -> pd.DataFrame:
    """Bavarian daily-temperature gauges with their coverage."""
    if not GKD_PANEL.exists():
        return pd.DataFrame()
    daily = pd.read_csv(GKD_PANEL, comment="#", parse_dates=["date"])
    daily = daily.dropna(subset=["temp_mean_c", "latitude", "longitude"])
    daily["year"] = daily["date"].dt.year
    stations = (
        daily.groupby(["station_id", "station_name", "latitude", "longitude"], as_index=False)
        .agg(n_obs=("temp_mean_c", "size"), year_min=("year", "min"), year_max=("year", "max"))
    )
    stations["source"] = "gkd"
    stations["resolution"] = "daily"
    # GKD publishes the river per station, so the tributary check is already
    # satisfied upstream of here; carry it as the water-body name.
    stations = stations.merge(
        daily[["station_id", "river"]].drop_duplicates(), on="station_id", how="left"
    ).rename(columns={"river": "water_body_name"})
    return stations


def names_the_river(water_body_name: str, river: str) -> Optional[bool]:
    """Does this water-body name describe the study river itself, or a tributary?

    Waterbase water-body names lead with the river they describe and then say
    which reach: ``"DONAU VON EINMUENDUNG LECH BIS EINMUENDUNG PAAR"`` is the
    Danube, while ``"LECH VON EINMUENDUNG LECHKANAL MEITINGEN BIS MUENDUNG IN
    DIE DONAU"`` is the Lech and merely *mentions* the Danube. Testing the first
    substantive token separates the two; a plain substring test does not.

    Returns ``None`` when the name is missing or a placeholder, so the caller can
    fall back to a distance rule.
    """
    text = (water_body_name or "").strip().upper()
    if text in _PLACEHOLDER_NAMES:
        return None
    tokens = [t for t in re.split(r"[^A-ZÄÖÜ]+", text) if t]
    head = next((t for t in tokens if t not in _QUALIFIERS), None)
    if head is None:
        return None
    if "KANAL" in head:  # a canal is not the river itself
        return False
    return RIVER_TOKENS[river] in head


def waterbase_stations(river_only: bool = True) -> pd.DataFrame:
    """German Waterbase temperature sites, by default rivers only."""
    if not (WATERBASE_SITES.exists() and WATERBASE_SAMPLES.exists()):
        return pd.DataFrame()
    sites = pd.read_csv(WATERBASE_SITES).dropna(subset=["latitude", "longitude"])
    samples = pd.read_csv(WATERBASE_SAMPLES, dtype={"sampling_date": str})
    samples = samples[samples["determinand_label"].eq("Water temperature")]
    if river_only:
        samples = samples[samples["water_body_category"].eq("RW")]
    samples["year"] = pd.to_numeric(samples["sampling_date"].str[:4], errors="coerce")

    summary = (
        samples.groupby("site_id", as_index=False)
        .agg(n_obs=("value", "size"), year_min=("year", "min"), year_max=("year", "max"))
    )
    stations = summary.merge(
        sites[["site_id", "site_name", "water_body_name", "latitude", "longitude"]],
        on="site_id", how="inner",
    )
    stations = stations.rename(columns={"site_id": "station_id", "site_name": "station_name"})
    stations["source"] = "waterbase"
    stations["resolution"] = "spot sample"
    stations["year_min"] = stations["year_min"].astype("Int64")
    stations["year_max"] = stations["year_max"].astype("Int64")
    return stations


def all_stations(river_only: bool = True, max_offset_m: float = MAX_OFFSET_M) -> pd.DataFrame:
    """Every gauge from both sources, placed on a study river stem."""
    frames = [f for f in (gkd_stations(), waterbase_stations(river_only)) if not f.empty]
    if not frames:
        return pd.DataFrame()
    stations = pd.concat(frames, ignore_index=True)
    located = river_network.locate_frame(stations, max_offset_m=max_offset_m)
    located = located[located["river"].notna()].copy()

    # A site can sit within a kilometre of the main stem and still be on a
    # tributary — the Weschnitz and the Schwarzbach both join the Rhine right at
    # Biblis. Keep only sites whose water-body name is the study river; where
    # there is no usable name, demand a much smaller offset instead.
    #
    # Only Waterbase needs this. GKD lists the river for each gauge in its own
    # index, so those rows are already known-good and are exempt.
    if "water_body_name" in located.columns:
        checked = located["source"].ne("gkd")
        named = located[checked].apply(
            lambda row: names_the_river(row.get("water_body_name"), row["river"]), axis=1
        )
        keep = pd.Series(True, index=located.index)
        keep.loc[checked] = (
            named.fillna(False)
            | (named.isna() & located.loc[checked, "offset_m"].le(UNNAMED_MAX_OFFSET_M))
        )
        dropped = int((~keep).sum())
        if dropped:
            print(f"monitoring_stations: dropped {dropped} Waterbase sites that sit on a "
                  f"tributary, not on the study river itself.")
        located = located[keep].copy()

    located["river_km"] = located["river_km"].round(2)
    located["offset_m"] = located["offset_m"].round(0)
    return located.sort_values(["river", "river_km"], ascending=[True, False]).reset_index(drop=True)


def main() -> int:
    stations = all_stations()
    if stations.empty:
        print("monitoring_stations: no station data found.")
        return 1
    pd.set_option("display.width", 220)
    print(
        stations.groupby(["river", "source"])
        .agg(gauges=("station_id", "nunique"), obs=("n_obs", "sum"),
             first=("year_min", "min"), last=("year_max", "max"))
        .to_string()
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
