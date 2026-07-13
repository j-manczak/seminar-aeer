"""The study's reactor master table and group logic.

This is the single source of truth for which reactor belongs to which group of
the difference-in-differences design around the March 2011 nuclear moratorium.

Groups
------
treatment           Whole site went off-grid in 2011; the entire cooling load
                    was removed.
partial             One block went off-grid in 2011 while a sister block at the
                    same site kept running (only part of the load removed).
control             Ran continuously across the whole 2006-2018 window.
staggered_treatment Operation ended inside the window (a later, staggered load
                    shock); not a valid full-window control.
excluded            Already effectively off-grid before 2011, so it carries no
                    2011 shock.

Cooling type
------------
once_through        Fresh river/estuary water, no cooling tower. Waste heat goes
                    straight into the river, so the thermal signal downstream is
                    stronger.
cooling_tower       Closed loop with a wet cooling tower; most waste heat leaves
                    to the air, so the river signal is weaker.

Shutdown/commissioning years and cooling types are compiled from public reactor
documentation (BASE, World Nuclear News, operator brochures), because they are
not contained in the project's raw data. See METHODS.md for the sources.
"""

from dataclasses import dataclass
from typing import List

GROUP_ORDER = ["treatment", "partial", "control", "staggered_treatment", "excluded"]


@dataclass(frozen=True)
class Reactor:
    reactor: str
    block: str
    group: str
    river: str
    cooling_type: str
    commissioned_year: int
    shutdown_year: int
    latitude: float
    longitude: float
    rationale: str


REACTORS: List[Reactor] = [
    # --- treatment: full-site 2011 shutdowns --------------------------------
    Reactor("Biblis A", "KWB A", "treatment", "Rhine", "cooling_tower", 1974, 2011, 49.7094, 8.4147,
            "Shut down in 2011. Both Biblis blocks stopped together, so the whole cooling load at the site was removed."),
    Reactor("Biblis B", "KWB B", "treatment", "Rhine", "cooling_tower", 1976, 2011, 49.7094, 8.4147,
            "Shut down in 2011 together with Biblis A; the full site cooling load was removed."),
    Reactor("Unterweser", "KKU", "treatment", "Weser", "once_through", 1978, 2011, 53.4286, 8.4769,
            "Single-block site with once-through cooling from the tidal lower Weser; the entire thermal discharge stopped in 2011."),
    # --- partial: 2011 block shutdown, sister block continued ---------------
    Reactor("Isar 1", "KKI 1", "partial", "Isar", "once_through", 1977, 2011, 48.6048, 12.2955,
            "Shut down in 2011 while Isar 2 kept running; only block 1's once-through load was removed."),
    Reactor("Neckarwestheim 1", "GKN I", "partial", "Neckar", "cooling_tower", 1976, 2011, 49.0411, 9.1750,
            "Shut down in 2011 while Neckarwestheim 2 kept running; only block 1's load was removed."),
    Reactor("Philippsburg 1", "KKP 1", "partial", "Rhine", "cooling_tower", 1979, 2011, 49.2527, 8.4354,
            "Shut down in 2011 while Philippsburg 2 kept running; only block 1's load was removed."),
    # --- control: continuous operation across the full 2006-2018 window ------
    Reactor("Grohnde", "KWG", "control", "Weser", "cooling_tower", 1985, 2021, 52.0356, 9.4135,
            "On-grid through the whole window (shut down only end of 2021). Clean single-load site, no block change in the window."),
    Reactor("Emsland", "KKE", "control", "Ems", "cooling_tower", 1988, 2023, 52.4819, 7.3067,
            "On-grid through the whole window (shut down only 2023). Single-block site, no cooling-load change in the window."),
    Reactor("Brokdorf", "KBR", "control", "Elbe", "once_through", 1986, 2021, 53.8511, 9.3459,
            "On-grid through the whole window (shut down only end of 2021). Single-block site, once-through cooling from the Elbe."),
    Reactor("Isar 2", "KKI 2", "control", "Isar", "cooling_tower", 1988, 2023, 48.6046, 12.2951,
            "On-grid through the whole window (shut down 2023). Control at reactor level; note the site saw a partial load cut in 2011 (Isar 1)."),
    Reactor("Neckarwestheim 2", "GKN II", "control", "Neckar", "cooling_tower", 1989, 2023, 49.0411, 9.1750,
            "On-grid through the whole window (shut down 2023). Control at reactor level; the site saw a partial load cut in 2011 (Neckarwestheim 1)."),
    Reactor("Philippsburg 2", "KKP 2", "control", "Rhine", "cooling_tower", 1985, 2019, 49.2527, 8.4354,
            "On-grid through the whole window (shut down end of 2019, after the window). Control at reactor level; the site saw a partial load cut in 2011 (Philippsburg 1)."),
    Reactor("Gundremmingen C", "KRB C", "control", "Danube", "cooling_tower", 1984, 2021, 48.5161, 10.3982,
            "On-grid through the whole window (shut down end of 2021). No 2011 shutdown; the sister block Gundremmingen B went off-grid end of 2017."),
    # --- staggered_treatment: operation ends inside the window --------------
    Reactor("Grafenrheinfeld", "KKG", "staggered_treatment", "Main", "cooling_tower", 1982, 2015, 49.9844, 10.1818,
            "Shut down end of 2015, i.e. INSIDE the 2006-2018 window. Not a valid full-window control; treat as a later, staggered treatment (load removed in 2015)."),
    Reactor("Gundremmingen B", "KRB B", "staggered_treatment", "Danube", "cooling_tower", 1984, 2017, 48.5150, 10.4016,
            "Shut down end of 2017, i.e. INSIDE the window. Not a valid full-window control; treat as a staggered treatment (load removed in 2017). Sister block Gundremmingen C kept running."),
    # --- excluded: already offline well before 2011 -------------------------
    Reactor("Krümmel", "KKK", "excluded", "Elbe", "once_through", 1984, 2011, 53.4109, 10.4092,
            "Formal grid disconnection in 2011, but effectively off-grid since the 2007 transformer fire and fully offline from 2009. No real 2011 shock, so excluded."),
    Reactor("Brunsbüttel", "KKB", "excluded", "Elbe", "once_through", 1976, 2011, 53.8918, 9.2026,
            "Formal grid disconnection in 2011, but effectively offline since a 2007 incident. No real 2011 shock, so excluded."),
]

# Reactors used for spatial filtering (everything except the excluded ones).
STUDY_REACTORS: List[Reactor] = [r for r in REACTORS if r.group != "excluded"]


def is_full_window_control(reactor: Reactor, window_start: int, window_end: int) -> bool:
    """True if the reactor ran on-grid across the entire window.

    A valid full-window control must have started before the window and must not
    have shut down before the window ended, i.e. shutdown strictly after
    ``window_end``.
    """
    return reactor.commissioned_year <= window_start and reactor.shutdown_year > window_end
