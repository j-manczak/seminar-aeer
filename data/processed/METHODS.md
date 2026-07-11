# Methods

This document records, step by step, how we turn the raw inputs into the
analysis tables for our difference-in-differences (DiD) study of the March 2011
German nuclear moratorium. It names each data source with its retrieval date and
gives the reason for every filtering, aggregation and exclusion decision, so the
text can feed directly into the paper's methods section.

*Last updated: 9 July 2026.*

## 1. Question and study window

We ask whether removing the thermal cooling load of the reactors shut down in
2011 changed the temperature and dissolved-oxygen regime of the affected rivers.
The observation window is **2006–2018 (inclusive)** — five years before and
seven years after the shock, kept symmetric where the data allow. Every filter
below uses this window.

## 2. Data sources and retrieval dates

| Dataset | File(s) | Origin | Retrieved |
|---|---|---|---|
| Reactor sites and rivers | `data/Plants-River-Treatment.xlsx` | group worksheet | 7 Jul 2026 |
| Nuclear plant master data | `data/processed/nuclear_plants_de_clean.csv` | Open Power System Data, `conventional_power_plants_DE` (nuclear subset) | 7 Jul 2026 |
| Conventional thermal plants | `data/processed/conventional_plants_de_relevant_clean.csv` | Open Power System Data | 7 Jul 2026 |
| Water temperature, dissolved oxygen | `data/raw/waterbase/Waterbase_v2020_1_T_WISE6_AggregatedData.csv` (+ `…_S_WISE6_SpatialObject_DerivedData.csv`) | EEA Waterbase v2020_1 | 9 Jul 2026 |
| River discharge | `data/raw/discharge/*.txt` | GRDC (Global Runoff Data Centre, BfG) | 9 Jul 2026 |
| Weather | `data/processed/dwd_kl_daily_near_nuclear.csv` | DWD Climate Data Center, daily KL | 7 Jul 2026 |

Shutdown years and cooling types are not in these raw files. We compiled them
from public documentation, retrieved **7 Jul 2026**:

- BASE (Bundesamt für die Sicherheit der nuklearen Entsorgung), nuclear phase-out pages — shutdown dates.
- World Nuclear News, "Three German reactors cease operation" — the 2021 and 2023 shutdowns.
- Operator/authority documents for cooling type: PreussenElektra site brochure Isar (once-through KKI 1 vs. cooling tower KKI 2), BASE Brokdorf page (once-through from the Elbe), Wikipedia "Kernkraftwerk Grohnde" (cooling tower).

**Open assumption.** The exact download dates of the EEA, OPSD and DWD raw files
are not logged in the repository. We record the dataset versions (Waterbase
v2020_1, OPSD `conventional_power_plants_DE`, DWD daily KL) and will add the
precise dates once recovered from the original download scripts.

## 3. Reactor group assignment

The assignment lives in `data/processed/group_assignment.csv` (columns
`reactor, block, group, river, cooling_type, commissioned_year, shutdown_year,
rationale`) and is generated from the master table in
`scripts/pipeline/reactors.py`.

### 3.1 Full-window operation check (2006–2018)

For every control candidate we checked explicitly whether it ran on-grid across
the whole window, using its shutdown year: it must have started before 2006, not
have shut down before the window ended (shutdown after 2018), and not have been
effectively offline before 2011. Two nominal "still operating" plants fail:

- **Grafenrheinfeld** shut down at the end of **2015**, inside the window.
- **Gundremmingen B** shut down at the end of **2017**, inside the window.

Both are removed from the control group and relabelled as
**`staggered_treatment`**, because their shutdown is itself a (later) removal of
cooling load. For a clean design they should be dropped or modelled with a
reactor-specific treatment time.

### 3.2 Group logic

- **`treatment`** — the site went fully off-grid in 2011, removing the whole
  cooling load: **Biblis A**, **Biblis B**, **Unterweser**.
- **`partial`** — a block went off-grid in 2011 while its sister block at the
  same site kept running, removing only part of the load: **Isar 1**,
  **Neckarwestheim 1**, **Philippsburg 1**.
- **`control`** — ran continuously 2006–2018: **Grohnde**, **Emsland**,
  **Brokdorf**, **Isar 2**, **Neckarwestheim 2**, **Philippsburg 2**,
  **Gundremmingen C**.

The continuing sister blocks (Isar 2, Neckarwestheim 2, Philippsburg 2) are
controls **at reactor level** because the block itself ran throughout; the
`rationale` column notes that their **site** still saw a partial load cut in
2011. Whoever models at site rather than reactor level must treat these blocks
accordingly. The same caveat applies to Gundremmingen C, whose sister block B
was shut down in 2017.

### 3.3 Exclusions

**Brunsbüttel** and **Krümmel** were formally disconnected in 2011 but had been
effectively offline since 2007 (Brunsbüttel after an incident; Krümmel after the
2007 transformer fire, fully offline from 2009). They deliver no real 2011 shock
and are neither valid treatments nor valid controls, so we exclude them
(`excluded`).

### 3.4 Result

17 reactors: 3 treatment, 3 partial, 7 control, 2 staggered_treatment, 2 excluded.

### 3.5 Cooling type

Cooling type matters for interpretation: **once-through** plants (fresh
river/estuary water, no tower) discharge waste heat straight into the river and
leave a stronger downstream signal, whereas **cooling-tower** plants release most
heat to the air. Classification:

- **once_through:** Unterweser, Brokdorf, Krümmel, Brunsbüttel, Isar 1 (with
  auxiliary cell coolers).
- **cooling_tower:** Biblis A/B, Neckarwestheim 1/2, Philippsburg 1/2,
  Grafenrheinfeld, Grohnde, Gundremmingen B/C, Emsland, Isar 2.

**Open assumption.** This is literature-based, not from the project data. The
clearly documented cases (Isar 1 vs. Isar 2, Brokdorf, Grohnde, Unterweser) are
solid; the remaining blocks should be checked against a primary source before
publication.

## 4. Filtered analysis outputs

Each dataset yields exactly one filtered file in `data/processed/analysis/`,
restricted to the study sites and to 2006–2018. "Study sites" means within
`SITE_RADIUS_KM` (50 km, matching `scripts/prepare_data.py`) of one of the 15
study reactors (all except the excluded Krümmel and Brunsbüttel); distance is a
haversine distance to the nearest study reactor. Every file carries a `#` comment
header with its filter. All files are produced by `python scripts/build_all.py`.

### 4.1 Water temperature — `water_temperature_2006_2018.csv`

From the EEA Waterbase `AggregatedData` table (annual value per site), joined to
the site coordinates in `SpatialObject_DerivedData`, kept for German sites within
the radius and inside the window. **No extra aggregation** is applied — Waterbase
already provides annual mean/min/max per site. Coverage note: Waterbase has no
rows for 2006, 2007 and 2015 at these sites, so the window materialises as
2008–2014 plus 2016–2018.

### 4.2 Dissolved oxygen — `dissolved_oxygen_2006_2018.csv`

Same source, join and filter as water temperature, but for the determinand
`Dissolved oxygen` (configurable in `scripts/pipeline/config.py`, in case a newer
Waterbase release renames it). Dissolved oxygen is a second water-quality outcome
and is physically coupled to temperature.

### 4.3 River discharge — `discharge_2006_2018.csv`

From the GRDC daily export files in `data/raw/discharge/`. Each gauge file's
`#` header supplies its coordinates; the daily values (with `-999` treated as
missing) are aggregated per station and year to mean/min/max discharge plus
`days_observed`, then restricted to gauges within the radius and to the window.
We requested the Rhine (incl. Neckar and Main), Danube (incl. Isar), Weser, Elbe
and Ems sub-regions. Discharge is a key covariate: water temperature and the
dilution of thermal discharges depend strongly on streamflow.

### 4.4 Weather — `weather_2006_2018.csv`

From the DWD daily extract, kept for stations within the radius and inside the
window, then **aggregated per station and calendar month** (mean/min/max air
temperature, precipitation sum, mean wind speed, and `days_observed`). Monthly
matches the resolution of the water outcomes and keeps the file small; finer
resolution can be regenerated from the same source. Coverage note: the daily
extract only spans 2005–2015, so the window is 2006–2015 here, and there is no
station within the radius of the treatment site Unterweser (Biblis is covered).

### 4.5 Power plants — `power_plants_2006_2018.csv`

Conventional thermal plants from OPSD, kept within the radius and with an
operating life overlapping the window (commissioned by 2018, not shut down before
2006). These are potential thermal confounders near the study rivers; the study
reactors themselves are documented in `group_assignment.csv`.

### 4.6 River position (upstream / downstream)

A straight-line radius alone is too coarse for a thermal design: a plant's
waste-heat plume only reaches monitoring points that are on the *same* river and
*downstream* of it, and it decays with distance. `river_position.py` therefore
enriches the water-temperature, dissolved-oxygen and discharge files with, per
site: the matched `study_river`, its `position` (downstream / upstream /
off_river), the `nearest_upstream_plant` and its group, an approximate
`along_river_km`, a `distance_band` (0–10 / 10–25 / 25–50 / >50 km) and
`downstream_of_shock` (1 below a 2011/staggered shutdown). River membership comes
from the water-body / GRDC river name (with the REMS≠EMS and canal traps
handled); up/downstream comes from a per-river downstream flow vector. The
along-flow *sign* is robust; the exact distance is approximate and should later
be replaced by true river kilometres from a river network.

This step is decisive for sample size. Of 245 water-temperature stations inside
the 50 km radius, only 41 are downstream of a study reactor (187 are off-river,
17 upstream), and just **6** lie downstream of a full-shutdown *treatment* plant
(3 of them within 0–10 km). The plume-relevant treatment sample is therefore
small, which the analysis must acknowledge.

## 5. Summary of exclusion / flagging decisions

| Unit | Decision | Reason |
|---|---|---|
| Grafenrheinfeld | out of control, flagged `staggered_treatment` | shutdown 2015, inside the window |
| Gundremmingen B | out of control, flagged `staggered_treatment` | shutdown 2017, inside the window |
| Krümmel | excluded | effectively offline since 2007/2009, no 2011 shock |
| Brunsbüttel | excluded | effectively offline since 2007, no 2011 shock |
| Isar 2 / Neckarwestheim 2 / Philippsburg 2 | control, with a site-level 2011 partial-load note | block ran throughout; sister block shut in 2011 |
| Sites/stations/plants > radius | filtered out | outside the spatial study area |

## 6. Open assumptions and next steps

1. Raw-file download dates are not logged; versions are recorded, exact dates to follow (§2).
2. Cooling type is literature-based; verify the non-obvious blocks against a primary source (§3.5).
3. Coverage gaps: water temperature has no 2006/2007/2015; weather ends in 2015. Decide before estimation whether to extend the series to 2018 or adjust the window.
4. Modelling level: reactor vs. site is a deliberate choice (§3.2); fix and justify it in the analysis.

## 7. Reproducibility

The pipeline is a small package of single-purpose modules under
`scripts/pipeline/`, orchestrated by `scripts/build_all.py`:

```
scripts/
  build_all.py            entry point; runs every step
  pipeline/
    config.py             window, radius, paths, determinand labels
    geo.py                haversine distance, nearest reactor
    io_tables.py          CSV read/write with a comment header, parsing helpers
    reactors.py           reactor master table + group logic (single source of truth)
    sites.py              match an observation to the nearest study reactor
    group_assignment.py   writes group_assignment.csv
    waterbase.py          water temperature + dissolved oxygen from raw Waterbase
    discharge.py          annual discharge from raw GRDC files
    river_position.py     same-river up/downstream position + distance bands
    weather.py            DWD monthly aggregation
    power_plants.py       conventional-plant confounders
    tests/test_parsers.py checks the parsers and river-position logic on fixtures
```

Run everything with `python scripts/build_all.py`; steps whose raw inputs are
absent skip themselves with a hint. Run the parser checks with
`python scripts/pipeline/tests/test_parsers.py`. The window and radius are the
constants `WINDOW_START`, `WINDOW_END` and `SITE_RADIUS_KM` in `config.py`.
