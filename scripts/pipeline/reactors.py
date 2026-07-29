"""The study's reactor master table and group logic.

This is the single source of truth for which reactor belongs to which group of
the difference-in-differences design around the March 2011 nuclear moratorium.

Groups are assigned at the SITE level, because the outcome is the river
temperature downstream of a site and it responds to the site's *total* cooling
load. All blocks that share a site therefore share a group -- a block that keeps
running next to one that shut down is not a clean control, its river still lost
heat.

treatment           The whole site went off-grid in 2011; the entire cooling
                    load was removed (both Biblis blocks; Unterweser).
partial             The site lost one block in 2011 while a sister block kept
                    running -- both blocks are `partial` (Isar, Neckarwestheim,
                    Philippsburg).
control             Single-block site that ran continuously across the whole
                    2006-2018 window (Grohnde, Emsland, Brokdorf).
staggered_treatment The site lost cooling load inside the window but not in 2011
                    -- a later, staggered shock; not a valid full-window control
                    (Grafenrheinfeld 2015; Gundremmingen B 2017, C to 2021).
excluded            Already effectively off-grid before 2011, so it carries no
                    2011 shock (Brunsbüttel, Krümmel).

Cooling type and how much heat actually reaches the river
---------------------------------------------------------
This is the part that decides whether a shutdown *can* show up in river
temperature at all, and an earlier version of this table got two sites wrong.

once_through        Fresh river/estuary water, no cooling tower. Essentially all
                    waste heat goes straight into the river, so the downstream
                    signal is strong.
hybrid              Can run either way: heated water is normally returned to the
                    river, with the cooling tower used when the river is too warm
                    or too low. Intermediate signal.
cooling_tower       Closed loop with a wet cooling tower. Most waste heat leaves
                    to the air as vapour and only a small blowdown stream returns
                    to the river, so the river signal is weak.

``river_heat_load`` summarises the expected thermal signal (high / moderate /
low). It is the design-relevant variable: a "treated" plant with a cooling tower
removed almost no heat from its river in 2011, so a null result there is not
evidence against the mechanism.

Documented magnitudes gathered for this table:

* **Biblis A/B** — normally ran on fresh-water (once-through) cooling, taking
  ~60 m³/s from the Rhine and returning it about 10 °C warmer; the two 80 m
  forced-draft towers on block B were a fallback for warm/low-water periods
  only. Previously mis-recorded here as ``cooling_tower``.
* **Isar 1** — once-through, licensed to warm the Isar by up to 2.5 K. Its
  sister block Isar 2 has a 165 m natural-draft tower, so the 2011 shutdown at
  the Isar site removed the *direct* discharge while the tower block ran on.
* **Grafenrheinfeld** — 97 % of waste heat left through the towers as vapour and
  only ~3 % reached the Main, worth roughly 0.5–1 K. A weak treatment by design.
* **Philippsburg 1/2** — natural-draft towers *plus* the option of discharging
  warmed water to the Rhine; recorded here as ``hybrid``.
* **Unterweser** — once-through from the tidal lower Weser.
* **Brokdorf** — once-through from the Elbe (had to throttle in hot summers).
* **Grohnde, Emsland, Gundremmingen B/C, Neckarwestheim 1/2, Isar 2** — wet
  cooling towers; make-up water is drawn to replace evaporation.

Shutdown/commissioning years and cooling types are compiled from public reactor
documentation (BASE, operator brochures, state environment ministries and the
plant articles they cite). See METHODS.md for the sources.
"""

from dataclasses import dataclass, field
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
    river_heat_load: str = "unknown"


REACTORS: List[Reactor] = [
    # --- treatment: full-site 2011 shutdowns --------------------------------
    # The whole site went off-grid in 2011, so the entire cooling load was removed.
    Reactor("Biblis A", "KWB A", "treatment", "Rhine", "once_through", 1974, 2011, 49.7094, 8.4147,
            "Shut down in 2011. Both Biblis blocks stopped together, so the whole cooling load at the site was removed. "
            "Ran on fresh-water cooling (~60 m3/s returned to the Rhine ~10 K warmer); the block-B towers were a warm-water fallback.",
            "high"),
    Reactor("Biblis B", "KWB B", "treatment", "Rhine", "once_through", 1976, 2011, 49.7094, 8.4147,
            "Shut down in 2011 together with Biblis A; the full site cooling load was removed. "
            "Normally operated once-through, with its two 80 m forced-draft towers reserved for warm or low Rhine water.",
            "high"),
    Reactor("Unterweser", "KKU", "treatment", "Weser", "once_through", 1978, 2011, 53.4286, 8.4769,
            "Single-block site with once-through cooling from the tidal lower Weser; the entire thermal discharge stopped in 2011.",
            "high"),
    # --- partial: site lost one block in 2011, a sister block kept running ---
    # Grouping is at SITE level: the downstream thermal signal is the whole
    # site's load, so BOTH blocks of a partially-shut site are `partial` (the
    # continuing block is not a clean control -- its river still lost heat in 2011).
    Reactor("Isar 1", "KKI 1", "partial", "Isar", "once_through", 1977, 2011, 48.6048, 12.2955,
            "Isar site partially treated in 2011: block 1 shut down while Isar 2 kept running. Isar 1 was once-through and "
            "licensed to warm the Isar by up to 2.5 K, so 2011 removed the only direct thermal discharge at the site.",
            "high"),
    Reactor("Isar 2", "KKI 2", "partial", "Isar", "cooling_tower", 1988, 2023, 48.6046, 12.2951,
            "Isar site partially treated in 2011: sister block Isar 1 shut down; Isar 2 ran on to 2023. Grouped with its site (partial), "
            "not as a clean control. Isar 2 uses a 165 m natural-draft tower, so it adds little heat directly to the river.",
            "low"),
    Reactor("Neckarwestheim 1", "GKN I", "partial", "Neckar", "cooling_tower", 1976, 2011, 49.0411, 9.1750,
            "Neckarwestheim site partially treated in 2011: block 1 shut down while Neckarwestheim 2 kept running. "
            "Tower cooling, so only a small share of the waste heat ever reached the Neckar.",
            "low"),
    Reactor("Neckarwestheim 2", "GKN II", "partial", "Neckar", "cooling_tower", 1989, 2023, 49.0411, 9.1750,
            "Neckarwestheim site partially treated in 2011: sister block 1 shut down; block 2 ran on to 2023. Grouped with its site (partial).",
            "low"),
    Reactor("Philippsburg 1", "KKP 1", "partial", "Rhine", "hybrid", 1979, 2011, 49.2527, 8.4354,
            "Philippsburg site partially treated in 2011: block 1 shut down while Philippsburg 2 kept running. "
            "The site could both discharge warmed water to the Rhine and dump heat through its natural-draft towers.",
            "moderate"),
    Reactor("Philippsburg 2", "KKP 2", "partial", "Rhine", "hybrid", 1985, 2019, 49.2527, 8.4354,
            "Philippsburg site partially treated in 2011: sister block 1 shut down; block 2 ran on to 2019. Grouped with its site (partial).",
            "moderate"),
    # --- control: single-block sites with no cooling-load change in the window
    Reactor("Grohnde", "KWG", "control", "Weser", "cooling_tower", 1985, 2021, 52.0356, 9.4135,
            "Single-block site, on-grid through the whole window (shut down only end of 2021). No cooling-load change -- a clean control. "
            "Tower cooling on the Weser.",
            "low"),
    Reactor("Emsland", "KKE", "control", "Ems", "cooling_tower", 1988, 2023, 52.4819, 7.3067,
            "Single-block site, on-grid through the whole window (shut down only 2023). No cooling-load change -- a clean control. "
            "Tower cooling, topped up from the Ems via the Geeste reservoir.",
            "low"),
    Reactor("Brokdorf", "KBR", "control", "Elbe", "once_through", 1986, 2021, 53.8511, 9.3459,
            "Single-block site with once-through cooling from the Elbe, on-grid through the whole window (shut down only end of 2021) -- a clean control.",
            "high"),
    # --- staggered_treatment: site lost load inside the window, not in 2011 --
    Reactor("Grafenrheinfeld", "KKG", "staggered_treatment", "Main", "cooling_tower", 1982, 2015, 49.9844, 10.1818,
            "Single-block site shut down end of 2015, i.e. INSIDE the window. Not a valid full-window control; a later, staggered treatment (load removed 2015). "
            "97 % of the waste heat left through the towers as vapour and only ~3 % reached the Main (~0.5-1 K), so the expected signal is small.",
            "low"),
    Reactor("Gundremmingen B", "KRB B", "staggered_treatment", "Danube", "cooling_tower", 1984, 2017, 48.5150, 10.4016,
            "Gundremmingen site treated in a staggered way: block B shut down end of 2017 (inside the window). Natural-draft tower cooling, "
            "with make-up water drawn from the Danube through a 1.4 km canal.",
            "low"),
    Reactor("Gundremmingen C", "KRB C", "staggered_treatment", "Danube", "cooling_tower", 1984, 2021, 48.5161, 10.3982,
            "Same site as Gundremmingen B (staggered): block B shut 2017, block C ran on to 2021. Grouped with its site (staggered), not a clean control.",
            "low"),
    # --- excluded: already offline well before 2011 -------------------------
    Reactor("Krümmel", "KKK", "excluded", "Elbe", "once_through", 1984, 2011, 53.4109, 10.4092,
            "Formal grid disconnection in 2011, but effectively off-grid since the 2007 transformer fire and fully offline from 2009. No real 2011 shock, so excluded.",
            "high"),
    Reactor("Brunsbüttel", "KKB", "excluded", "Elbe", "once_through", 1976, 2011, 53.8918, 9.2026,
            "Formal grid disconnection in 2011, but effectively offline since a 2007 incident. No real 2011 shock, so excluded.",
            "high"),
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
