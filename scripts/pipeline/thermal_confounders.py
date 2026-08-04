"""Other thermal power stations that take cooling water from the study rivers.

A nuclear site is not the only heat source on its river. Any condensing thermal
plant — coal, lignite, gas, oil, waste — rejects waste heat to whatever it cools
with, and most large German ones sit on a river for exactly that reason. For the
2x2 this matters in a specific way:

* A plant **between the upstream and the downstream gauge** adds heat to the
  *treated* reach. If its output was stable across the window it differences out
  and is harmless. If it **started up or shut down near the nuclear event**, it
  moves the same gap the nuclear shutdown moves, and the estimate is confounded.
* A plant **upstream of the control gauge** warms both gauges roughly equally and
  is differenced out — unless it changed at the same time, which would shift the
  control alone.

So the question is never "is there another plant nearby" but "did another plant
on this reach change at the same time". This module answers that.

Hydro, pumped storage and other non-condensing technologies are excluded: they
move water, not heat.

    python scripts/pipeline/thermal_confounders.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from pipeline import river_network
from pipeline.config import RAW_DIR

PLANTS_CSV = RAW_DIR / "conventional_power_plants" / "conventional_power_plants_DE.csv"

# Technologies that condense steam and therefore need a heat sink.
CONDENSING_TECHNOLOGIES = {"Steam turbine", "Combined cycle"}
# Everything that only moves water, or burns without a steam cycle.
NON_THERMAL_SOURCES = {"Hydro"}

# Whether a plant plausibly takes cooling water from the river it sits on, and
# why. This is a judgement from technology, not a licence record, so each answer
# carries its reason and the table should be read as "expected", not "verified".
#
#   Steam turbine / combined cycle -> a condenser has to dump the latent heat of
#     the exhaust steam somewhere. On a river that is river water, either
#     once-through or as tower make-up.
#   Open-cycle gas turbine -> exhaust goes up the stack; there is no condenser
#     and therefore no cooling-water demand worth speaking of.
#   Hydro -> the water passes through a turbine and leaves at the temperature it
#     arrived at. No heat is added.
COOLING_WATER_RULES = {
    "Steam turbine": ("ja", "Kondensator braucht eine Wärmesenke"),
    "Combined cycle": ("ja", "Dampfteil mit Kondensator"),
    "Gas turbine": ("nein", "offener Gasturbinenprozess, kein Kondensator"),
    "Combustion Engine": ("unwahrscheinlich", "Motorkühlung meist im geschlossenen Kreis"),
    "Run-of-river": ("nein", "Wasserkraft, keine Wärmeeinleitung"),
    "Reservoir": ("nein", "Wasserkraft, keine Wärmeeinleitung"),
    "Pumped storage": ("nein", "Wasserkraft, keine Wärmeeinleitung"),
    "RES": ("nein", "Wasserkraft, keine Wärmeeinleitung"),
    "Storage technologies": ("nein", "Speicher, keine Wärmeeinleitung"),
}


def classify_cooling_water(technology: str, energy_source: str, chp: str) -> tuple:
    """(nutzt Flusskühlwasser?, Begründung) für eine Anlage."""
    answer, reason = COOLING_WATER_RULES.get(
        technology, ("unklar", "Technologie nicht eindeutig zuzuordnen"))
    if answer == "ja" and str(chp).lower() == "yes":
        reason += "; als KWK-Anlage geht ein Teil der Wärme ins Fernwärmenetz"
    return answer, reason

# A plant this small cannot move a river reach measurably; it only adds noise to
# the confounder table.
MIN_CAPACITY_MW = 50.0

# How close in time a change has to be before we call it a confounder.
CHANGE_WINDOW_YEARS = 3


def load_thermal_plants(max_offset_m: float = 2500.0) -> pd.DataFrame:
    """Condensing thermal plants placed on a study river."""
    if not PLANTS_CSV.exists():
        raise FileNotFoundError(f"{PLANTS_CSV} not found.")
    plants = pd.read_csv(PLANTS_CSV, low_memory=False)

    keep = (
        plants["technology"].isin(CONDENSING_TECHNOLOGIES)
        & ~plants["energy_source"].isin(NON_THERMAL_SOURCES)
        & plants["capacity_net_bnetza"].ge(MIN_CAPACITY_MW)
        & plants["lat"].notna()
        & plants["lon"].notna()
    )
    thermal = plants[keep].copy()
    thermal = thermal.rename(columns={"lat": "latitude", "lon": "longitude"})

    located = river_network.locate_frame(thermal, max_offset_m=max_offset_m)
    located = located[located["river"].notna()].copy()

    located["commissioned_year"] = pd.to_numeric(located["commissioned"], errors="coerce")
    located["shutdown_year"] = pd.to_numeric(located["shutdown"], errors="coerce")
    located["plant"] = (
        located["name_bnetza"].fillna("").astype(str).str.strip()
        + located["block_bnetza"].fillna("").astype(str).apply(lambda b: f" ({b})" if b.strip() else "")
    )
    # The study reactors come through the same OPSD table; they are the treatment,
    # not a confounder, so they are flagged rather than silently mixed in.
    located["is_nuclear"] = located["energy_source"].eq("Nuclear")
    columns = [
        "plant", "company", "city", "state", "energy_source", "technology", "chp",
        "capacity_net_bnetza", "commissioned_year", "shutdown_year", "status",
        "is_nuclear", "latitude", "longitude", "river", "river_km", "offset_m",
    ]
    return located[[c for c in columns if c in located.columns]].sort_values(
        ["river", "river_km"], ascending=[True, False]
    ).reset_index(drop=True)


def load_river_energy_producers(min_capacity_mw: float = 10.0,
                                max_offset_m: float = 2500.0) -> pd.DataFrame:
    """*Every* power station on a study river, not only the condensing ones.

    :func:`load_thermal_plants` answers "what else could be heating this reach".
    This answers the wider question "what else is on this river at all", which is
    what a site inventory needs: run-of-river hydro adds no heat but is still an
    energy producer at the same location, and readers ask about it.
    """
    if not PLANTS_CSV.exists():
        raise FileNotFoundError(f"{PLANTS_CSV} not found.")
    plants = pd.read_csv(PLANTS_CSV, low_memory=False)

    keep = (
        plants["capacity_net_bnetza"].ge(min_capacity_mw)
        & plants["lat"].notna()
        & plants["lon"].notna()
    )
    frame = plants[keep].rename(columns={"lat": "latitude", "lon": "longitude"}).copy()

    located = river_network.locate_frame(frame, max_offset_m=max_offset_m)
    located = located[located["river"].notna()].copy()

    located["commissioned_year"] = pd.to_numeric(located["commissioned"], errors="coerce")
    located["shutdown_year"] = pd.to_numeric(located["shutdown"], errors="coerce")
    located["plant"] = (
        located["name_bnetza"].fillna("").astype(str).str.strip()
        + located["block_bnetza"].fillna("").astype(str).apply(
            lambda b: f" ({b})" if b.strip() else "")
    )
    located["is_nuclear"] = located["energy_source"].eq("Nuclear")

    cooling = located.apply(
        lambda r: classify_cooling_water(r["technology"], r["energy_source"], r.get("chp")),
        axis=1, result_type="expand",
    )
    located["uses_river_cooling_water"] = cooling[0]
    located["cooling_water_reason"] = cooling[1]

    columns = [
        "plant", "company", "city", "state", "energy_source", "technology", "chp",
        "capacity_net_bnetza", "commissioned_year", "shutdown_year", "status",
        "is_nuclear", "uses_river_cooling_water", "cooling_water_reason",
        "latitude", "longitude", "river", "river_km", "offset_m",
    ]
    return located[[c for c in columns if c in located.columns]].sort_values(
        ["river", "river_km"], ascending=[True, False]
    ).reset_index(drop=True)


def _changed_near(plant: pd.Series, event_year: int, window: int = CHANGE_WINDOW_YEARS) -> str:
    """Describe any commissioning/shutdown of this plant close to the event."""
    notes = []
    commissioned = plant.get("commissioned_year")
    shutdown = plant.get("shutdown_year")
    if pd.notna(commissioned) and abs(commissioned - event_year) <= window:
        notes.append(f"commissioned {int(commissioned)}")
    if pd.notna(shutdown) and abs(shutdown - event_year) <= window:
        notes.append(f"shut down {int(shutdown)}")
    return "; ".join(notes)


def confounders_for_pair(plants: pd.DataFrame, river: str, upstream_km: float,
                         downstream_km: float, event_year: int,
                         control_reach_km: float = 50.0,
                         margin_km: float = 0.0) -> pd.DataFrame:
    """Thermal plants that could disturb one upstream/downstream gauge pair.

    ``upstream_km`` and ``downstream_km`` are river kilometres from the mouth, so
    the treated reach is ``downstream_km < river_km < upstream_km``. Plants above
    the control gauge are reported too, within ``control_reach_km``.

    ``margin_km`` additionally keeps plants that fall just outside the reach but
    sit close to a gauge. Plant and gauge coordinates carry a few hundred metres
    of error, so a plant 700 m below the downstream gauge is formally irrelevant
    and practically worth a second look.
    """
    on_river = plants[plants["river"].eq(river) & ~plants["is_nuclear"]].copy()
    if on_river.empty:
        return on_river

    low, high = min(downstream_km, upstream_km), max(downstream_km, upstream_km)
    between = on_river["river_km"].between(low, high)
    above = on_river["river_km"].between(upstream_km, upstream_km + control_reach_km)
    near_gauge = (
        (on_river["river_km"] - upstream_km).abs().le(margin_km)
        | (on_river["river_km"] - downstream_km).abs().le(margin_km)
    ) if margin_km else pd.Series(False, index=on_river.index)

    on_river["reach"] = np.select(
        [between, above], ["between the gauges (treated reach)", "above the control gauge"],
        default="",
    )
    on_river["near_a_gauge"] = near_gauge
    relevant = on_river[(on_river["reach"] != "") | near_gauge].copy()
    if relevant.empty:
        return relevant

    relevant["changed_near_event"] = relevant.apply(lambda r: _changed_near(r, event_year), axis=1)
    relevant["is_confounder"] = relevant["changed_near_event"].ne("")
    # Was it even running around the event?
    relevant["active_at_event"] = (
        (relevant["commissioned_year"].isna() | relevant["commissioned_year"].le(event_year))
        & (relevant["shutdown_year"].isna() | relevant["shutdown_year"].ge(event_year))
    )
    return relevant.sort_values("river_km", ascending=False)


def main() -> int:
    plants = load_thermal_plants()
    pd.set_option("display.width", 240)
    print(f"Condensing thermal plants >= {MIN_CAPACITY_MW:.0f} MW on a study river: {len(plants)}\n")
    print(
        plants.groupby(["river", "energy_source"])
        .agg(n=("plant", "size"), mw=("capacity_net_bnetza", "sum"))
        .to_string()
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
