"""How much heat each reactor actually put into its river, and how much power it made.

To compare shutdowns we need a denominator. Two are useful and they answer
different questions:

``electricity``   °C per TWh of annual net generation removed. This is the
                  economically natural normalisation — "what did a unit of
                  nuclear electricity cost the river?" — and it is what the
                  supervisor's question asks for.
``river heat``    °C per GW of waste heat that actually reached the water. This
                  is the physically correct one, and it is where the cooling
                  technology enters: a tower plant of the same electrical size
                  put roughly thirty times less heat into its river.

Reporting only the first makes cooling-tower sites look like failed treatments.
Reporting both shows that they were never treatments of comparable size.

Derivation per block
--------------------
    waste heat        P_thermal − P_electric_net        (MW)
    heat to the river waste heat × river_share          (MW)

``river_share`` follows the cooling classification in :mod:`pipeline.reactors`:

* ``once_through`` → **0.95**. Essentially everything goes to the water; a few
  per cent leaves as evaporation and radiation from the discharge plume.
* ``hybrid`` → **0.50**. The site could run either way and did both; without
  operating records this is an explicit half-way assumption, and the sensitivity
  of any conclusion to it should be stated.
* ``cooling_tower`` → **0.03**. Grafenrheinfeld is documented at 97 % of waste
  heat leaving through the towers as vapour, i.e. ~3 % to the Main. We apply
  that measured split to the other tower sites.

Thermal ratings and generation are from the plant documentation (German/English
Wikipedia reactor-block tables, which cite operator and IAEA PRIS figures);
retrieved 30 July 2026.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from pipeline.reactors import REACTORS

# Share of waste heat that reaches the river, by cooling technology.
RIVER_SHARE: Dict[str, float] = {
    "once_through": 0.95,
    "hybrid": 0.50,
    "cooling_tower": 0.03,
}


@dataclass(frozen=True)
class BlockThermal:
    """Documented ratings for one reactor block."""

    block: str
    electric_net_mw: float
    thermal_mw: float
    annual_net_gwh: Optional[float]
    generation_note: str


# thermal_mw and annual_net_gwh from the plant articles' block tables.
# Where only a lifetime total is published, the annual figure is that total
# divided by the number of full operating years, which is stated in the note.
BLOCK_THERMAL: Dict[str, BlockThermal] = {
    "Isar 1": BlockThermal(
        "Isar 1", 878, 2575, 6009,
        "198,270 GWh lifetime over 33 operating years (1978-2011); the final "
        "years were below average (Feb 2010 fuel-element outage)."),
    "Isar 2": BlockThermal(
        "Isar 2", 1410, 3950, 11477,
        "Metered 2018 generation, a normal full year."),
    "Grafenrheinfeld": BlockThermal(
        "Grafenrheinfeld", 1275, 3765, 9425,
        "Published annual net output; capacity factor 80 %."),
    "Gundremmingen B": BlockThermal(
        "Gundremmingen B", 1284, 3840, 10500,
        "Site output ~21 TWh/a split evenly between the two identical blocks."),
    "Gundremmingen C": BlockThermal(
        "Gundremmingen C", 1288, 3840, 10500,
        "Site output ~21 TWh/a split evenly between the two identical blocks."),
    # The remaining blocks are carried for completeness; none of them has an
    # estimable 2x2, so they only appear in the descriptive table.
    "Biblis A": BlockThermal("Biblis A", 1167, 3517, 8000, "Rated thermal power; annual output approximate."),
    "Biblis B": BlockThermal("Biblis B", 1240, 3733, 8500, "Rated thermal power; annual output approximate."),
    "Unterweser": BlockThermal("Unterweser", 1345, 3900, 10000, "Rated thermal power; annual output approximate."),
    "Philippsburg 1": BlockThermal("Philippsburg 1", 890, 2575, 6000, "Rated thermal power; annual output approximate."),
    "Philippsburg 2": BlockThermal("Philippsburg 2", 1402, 3950, 11000, "Rated thermal power; annual output approximate."),
    "Neckarwestheim 1": BlockThermal("Neckarwestheim 1", 785, 2497, 5500, "Rated thermal power; annual output approximate."),
    "Neckarwestheim 2": BlockThermal("Neckarwestheim 2", 1310, 3850, 10500, "Rated thermal power; annual output approximate."),
    "Grohnde": BlockThermal("Grohnde", 1360, 3900, 10500, "Rated thermal power; annual output approximate."),
    "Emsland": BlockThermal("Emsland", 1336, 3850, 11000, "Rated thermal power; annual output approximate."),
    "Brokdorf": BlockThermal("Brokdorf", 1410, 3900, 11000, "Rated thermal power; annual output approximate."),
}

# Blocks whose figures are rated/approximate rather than metered.
APPROXIMATE = {b for b, t in BLOCK_THERMAL.items() if "approximate" in t.generation_note}


def block_table() -> pd.DataFrame:
    """One row per reactor block with its heat and generation figures."""
    rows = []
    for reactor in REACTORS:
        thermal = BLOCK_THERMAL.get(reactor.reactor)
        if thermal is None:
            continue
        share = RIVER_SHARE.get(reactor.cooling_type)
        waste_mw = thermal.thermal_mw - thermal.electric_net_mw
        rows.append({
            "block": reactor.reactor,
            "river": reactor.river,
            "cooling_type": reactor.cooling_type,
            "river_heat_load": reactor.river_heat_load,
            "shutdown_year": reactor.shutdown_year,
            "electric_net_mw": thermal.electric_net_mw,
            "thermal_mw": thermal.thermal_mw,
            "efficiency": round(thermal.electric_net_mw / thermal.thermal_mw, 3),
            "waste_heat_mw": waste_mw,
            "river_share": share,
            "heat_to_river_mw": round(waste_mw * share, 1) if share is not None else None,
            "annual_net_gwh": thermal.annual_net_gwh,
            "figures_approximate": reactor.reactor in APPROXIMATE,
            "generation_note": thermal.generation_note,
        })
    return pd.DataFrame(rows)


def site_event_load(site_blocks, event_year: int) -> dict:
    """Heat and generation removed at one site by one shutdown event."""
    table = block_table().set_index("block")
    shut = [b.reactor for b in site_blocks if b.shutdown_year == event_year]
    known = [b for b in shut if b in table.index]
    if not known:
        return {}
    subset = table.loc[known]
    return {
        "blocks_shut": ", ".join(known),
        "electric_net_mw": float(subset["electric_net_mw"].sum()),
        "waste_heat_mw": float(subset["waste_heat_mw"].sum()),
        "heat_to_river_mw": float(subset["heat_to_river_mw"].sum()),
        "annual_net_twh": round(float(subset["annual_net_gwh"].sum()) / 1000.0, 3),
        "figures_approximate": bool(subset["figures_approximate"].any()),
    }


def main() -> int:
    pd.set_option("display.width", 240)
    table = block_table()
    print(table[["block", "river", "cooling_type", "electric_net_mw", "thermal_mw",
                 "efficiency", "waste_heat_mw", "river_share", "heat_to_river_mw",
                 "annual_net_gwh", "figures_approximate"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
