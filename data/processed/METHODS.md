# Methods

This document records, step by step, how we turn the raw inputs into the
analysis tables for our difference-in-differences (DiD) study of the March 2011
German nuclear moratorium. It names each data source with its retrieval date and
gives the reason for every filtering, aggregation and exclusion decision, so the
text can feed directly into the paper's methods section.

*Last updated: 29 July 2026.*

> **Revision of 29 July 2026.** A data audit found that the EEA Waterbase
> contains **no German river water temperature before 2020** — every pre-2020
> German temperature record in it is groundwater. Sections 2, 3.5, 4.6, 8 and 10
> are rewritten accordingly, and the analysis now rests on daily data from the
> Bavarian Gewässerkundlicher Dienst. Section 9 records the superseded first
> pass. Full audit: [`analysis/DATENAUDIT_UND_2x2.md`](analysis/DATENAUDIT_UND_2x2.md).

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
| Water temperature, dissolved oxygen (annual) | `data/raw/waterbase/Waterbase_v2020_1_T_WISE6_AggregatedData.csv` (+ `…_S_WISE6_SpatialObject_DerivedData.csv`) | EEA Waterbase v2020_1 | 9 Jul 2026 |
| Water temperature, dissolved oxygen (individual samples) | `data/raw/waterbase/Waterbase_v2025_1_WISE6_DisaggregatedData.sqlite` | EEA Waterbase v2025_1 (Part 1, DisaggregatedData) | 12 Jul 2026 |
| River discharge | `data/raw/discharge/*.txt` | GRDC (Global Runoff Data Centre, BfG) | 9 Jul 2026 |
| Weather | `data/processed/dwd_kl_daily_near_nuclear.csv` (built by `weather_download.py`) | DWD Climate Data Center, daily KL (historical) | 11 Jul 2026 |
| **Water temperature (daily)** | `data/processed/gkd_water_temperature_daily.csv` | **Gewässerkundlicher Dienst Bayern**, station pages under `gkd.bayern.de/de/fluesse/wassertemperatur` | 29 Jul 2026 |
| **River network** | `data/raw/rivers/HydroRIVERS_v10_eu_shp/` | **HydroRIVERS v1.0** (HydroSHEDS, WWF) — Europe | 29 Jul 2026 |
| **Tidal river reaches** | `data/raw/rivers/osm_tidal_reaches.geojson` | **OpenStreetMap** via Overpass (`waterway=river`, lower Elbe and Weser) | 29 Jul 2026 |
| **National boundary** | `data/raw/borders/germany.geo.json` | deutschlandGeoJSON (derived from BKG data), medium resolution | 29 Jul 2026 |

### 2.1 What the Waterbase actually contains — and why it is not enough

We scanned the complete disaggregated Waterbase once
(`scripts/extract_waterbase_de.py`) and extracted **every** German temperature
and oxygen sample. Broken down by water-body category:

| `parameterWaterBodyCategory` | before 2020 | 2020 onward |
|---|---:|---:|
| `GW` groundwater | 17,262 | 9,200 |
| `RW` **river** | **0** | 25,482 |
| `LW` lake | 0 | 808 |
| `TW` drinking water | 0 | 352 |

**Germany reported no river water temperature to the EEA before 2020.** Any
pre-2011 "river temperature" in an earlier version of this pipeline came from
groundwater wells, deep wells and spring catchments that happen to lie within a
kilometre or two of a river centre-line (station names such as
`GWM FLACH KIRSCHGARTSHAUSEN…`, `TB SCHLIENGEN`, `QF WEST UND OST…`). Every
analysis file must therefore filter on `parameterWaterBodyCategory = 'RW'`, and
the Waterbase can only support the **2021/2023** shutdowns, never 2011.

### 2.2 Bavarian daily data

The Gewässerkundlicher Dienst Bayern publishes **daily mean water temperature**
for ~150 river gauges, many reaching back to the 1980s.
`scripts/pipeline/gkd_bayern.py` reads the public station index, takes each
gauge's coordinates from the Leaflet payload on its own page, and pulls daily
means (`wertart=tmw`) in five-year chunks. For the three study rivers Bavaria
covers this yields **305,070 station-days at 35 gauges, 1995–2024** — on the
Isar, Danube and Main. This is the only source in the project that reaches
before 2011, and it is what makes the Isar 2011 estimate possible.

Requests are spaced 0.7 s apart and each station is cached under
`data/raw/gkd/daily/`, so a re-run costs nothing.

Shutdown years and cooling types are not in any of these raw files. We compiled
them from public documentation, retrieved **7 Jul 2026** and revised
**29 Jul 2026** (see §3.5 for the two corrections):

- BASE (Bundesamt für die Sicherheit der nuklearen Entsorgung), nuclear phase-out pages — shutdown dates.
- World Nuclear News, "Three German reactors cease operation" — the 2021 and 2023 shutdowns.
- Operator and state-authority documents plus the plant articles citing them, for cooling type and the documented warming spans.

**Open assumption.** The exact download dates of the EEA, OPSD and DWD raw files
are not logged in the repository. We record the dataset versions (Waterbase
v2020_1 and v2025_1, OPSD `conventional_power_plants_DE`, DWD daily KL) and will
add the precise dates once recovered from the original download scripts. The
GKD, HydroRIVERS, OSM and boundary retrievals above are logged.

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

Groups are assigned at the **site level**. The outcome is the river temperature
*downstream* of a site, which responds to the site's **total** cooling load, so
all blocks that share a site share a group. A block that keeps running next to
one that shut down is **not** a clean control — its river still lost heat.

- **`treatment`** — the whole site went off-grid in 2011: **Biblis A**,
  **Biblis B**, **Unterweser**.
- **`partial`** — the site lost one block in 2011 while a sister block kept
  running; **both blocks** are partial: **Isar 1 + Isar 2**,
  **Neckarwestheim 1 + 2**, **Philippsburg 1 + 2**.
- **`control`** — single-block sites that ran continuously 2006–2018:
  **Grohnde**, **Emsland**, **Brokdorf**.

This is a deliberate change from an earlier reactor-level labelling, where the
continuing blocks (Isar 2, Neckarwestheim 2, Philippsburg 2) were called
controls. That was inconsistent: because the two blocks of a site sit at the
same coordinates, the downstream attribution (nearest upstream reactor in
`river_position.py`) could assign a partial-site observation to either group.
Grouping at the site level removes that ambiguity and leaves only the three
clean single-block sites as controls. In practice the summer panel already
attributed every downstream control site to Grohnde/Emsland/Brokdorf, so the
headline coverage and trend figures are unchanged; the fix corrects the group
labels and the straight-line group columns in the other tables.

### 3.3 Exclusions

**Brunsbüttel** and **Krümmel** were formally disconnected in 2011 but had been
effectively offline since 2007 (Brunsbüttel after an incident; Krümmel after the
2007 transformer fire, fully offline from 2009). They deliver no real 2011 shock
and are neither valid treatments nor valid controls, so we exclude them
(`excluded`).

### 3.4 Result

17 reactors: 3 treatment, 6 partial, 3 control, 3 staggered_treatment, 2 excluded.

### 3.5 Cooling type and how much heat actually reaches the river

*Revised 29 July 2026. Two entries were wrong and are corrected below.*

Cooling type decides whether a shutdown can show up in river temperature at all,
so it is a design variable, not a footnote. `reactors.py` now carries three
categories plus a summary field `river_heat_load` (`high` / `moderate` / `low`):

- **once_through** — fresh river or estuary water, no tower; essentially all
  waste heat enters the river.
- **hybrid** — heated water is normally returned to the river, with the tower
  used when the river is too warm or too low.
- **cooling_tower** — closed loop; most heat leaves as vapour and only a small
  blowdown stream returns.

| Block(s) | Classification | `river_heat_load` | Evidence |
|---|---|---|---|
| Biblis A/B | `once_through` *(was `cooling_tower`)* | high | Normally ran fresh-water cooled: ~60 m³/s drawn from the Rhine and returned about 10 K warmer. The two 80 m forced-draft towers on block B were a fallback for warm or low Rhine water only. |
| Philippsburg 1/2 | `hybrid` *(was `cooling_tower`)* | moderate | Natural-draft towers **and** the option of discharging warmed water directly to the Rhine. |
| Unterweser | `once_through` | high | Once-through from the tidal lower Weser. |
| Isar 1 | `once_through` | high | Licensed to warm the Isar by up to **2.5 K**; auxiliary cell coolers only when the river could not carry the load. |
| Isar 2 | `cooling_tower` | low | 165 m natural-draft tower. |
| Brokdorf | `once_through` | high | Fresh-water cooled from the Elbe; had to throttle in hot summers. |
| Grafenrheinfeld | `cooling_tower` | low | **97 % of the waste heat left through the towers as vapour**; only ~3 % reached the Main, worth roughly 0.5–1 K. |
| Gundremmingen B/C | `cooling_tower` | low | Natural-draft wet towers, make-up water from the Danube via a 1.4 km canal. |
| Neckarwestheim 1/2, Grohnde, Emsland | `cooling_tower` | low | Wet towers. |
| Krümmel, Brunsbüttel | `once_through` | high | Excluded on other grounds (§3.3). |

**Design consequence.** "Treatment" is not homogeneous. A null result at
Grafenrheinfeld or Neckarwestheim is **not** evidence against the mechanism —
those sites never put meaningful heat into their river. The sites with real
signal potential for 2011 are **Unterweser, Biblis and Isar 1**. Results should
be reported split by `river_heat_load`, not pooled.

**Open assumption.** Still literature-based rather than from primary licence
documents. The magnitudes quoted above (60 m³/s at Biblis, 2.5 K at Isar 1, 97 %
at Grafenrheinfeld) come from public plant documentation; a licence-level source
would be better before publication.

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

`weather_download.py` pulls the DWD daily climate (KL) *historical* archive live
for every station within `WEATHER_RADIUS_KM` (50 km) of a study reactor and
writes the daily intermediate `dwd_kl_daily_near_nuclear.csv`. Weather is a
regional covariate rather than a local treatment, so a station radius equal to
the site radius is generous enough — every study site, including Unterweser (its
nearest station is ~9 km away), is covered by several stations. `weather.py` then
keeps the window and **aggregates per station and calendar month** (mean/min/max
air temperature, precipitation sum, mean wind speed, `days_observed`); monthly
matches the resolution of the water outcomes and keeps the file small. The daily
intermediate is large (~80 MB) and reproducible, so it is git-ignored; run
`python scripts/pipeline/weather_download.py` to rebuild it. The result now spans
the full 2006–2018 window (the earlier 2015 cut-off came from an older extract).

### 4.5 Power plants — `power_plants_2006_2018.csv`

Conventional thermal plants from OPSD, kept within the radius and with an
operating life overlapping the window (commissioned by 2018, not shut down before
2006). These are potential thermal confounders near the study rivers; the study
reactors themselves are documented in `group_assignment.csv`.

### 4.6 River position (upstream / downstream) — superseded by §4.7

`river_position.py` enriched the analysis files with a `position`, a
`nearest_upstream_plant` and an approximate `along_river_km`. Up/downstream and
distance came from projecting the straight line onto **one fixed direction
vector per river** (`FLOW`). That heuristic is unreliable wherever a river
meanders — on the Main, Neckar and Isar it can invert the sign, i.e. call an
upstream gauge downstream — and it produced distances that are not comparable
across reaches. It also attached every downstream gauge to the "nearest upstream
reactor", which broke down for blocks sharing a site (see §4.7).

The module is kept because older outputs reference its columns, but nothing in
the current analysis uses it.

### 4.7 River position from the real network — `pipeline/river_network.py`

Geometry and flow direction now come from data rather than from a bearing.

**Network.** `HydroRIVERS v1.0` (Europe) supplies the river network *with flow
topology*: every reach links to the one below it via `NEXT_DOWN`, so "downstream"
is read off the network. Each study river's main stem is grown from a seed point
that sits unambiguously on the main channel: walk down via `NEXT_DOWN` to the
mouth, and up by repeatedly taking the tributary with the largest upstream
catchment (`UPLAND_SKM`), which is the main stem by definition. The three
tributary study rivers (Neckar, Main, Isar) are cut at an explicitly stated
confluence — a catchment-ratio rule was tried first and misfires where a
tributary rivals its receiving river (the Aller is nearly as large as the Weser).

**Tidal reaches.** HydroRIVERS ends at the tidal limit, so the lower Elbe
(Brokdorf) and lower Weser (Unterweser) are missing from it. Those two are
appended from OpenStreetMap `waterway=river` geometry fetched via Overpass.

**Chainage.** Every point is projected onto its stem in EPSG:25832 (UTM 32N),
giving `river_km` measured **from the river mouth**, so it decreases downstream.
For a plant *P* and a gauge *g*, `river_km(P) − river_km(g)` is the true
along-channel distance and its sign gives up/downstream. Nothing is estimated.

**Validation.** Independent checks against official kilometrage:

| Check | Ours | Official | Deviation |
|---|---:|---:|---:|
| Neckarwestheim | Neckar-km 124.5 | 125.0 | 0.4 % |
| Isar 1 (Ohu) | Isar-km 63.8 | 63.5 | 0.5 % |
| Maxau → Speyer | 39.9 km | 38.3 km | +4 % |
| Speyer → Worms | 43.2 km | 42.8 km | +1 % |
| Worms → Mainz | 56.0 km | 55.0 km | +2 % |
| Mainz → Kaub | 51.7 km | 47.8 km | +8 % |
| Kaub → Köln | 146.8 km | 141.8 km | +4 % |
| Main-stem length, Neckar | 342 km | 362 km | −6 % |
| Main-stem length, Isar | 287 km | 295 km | −3 % |
| Main-stem length, Main | 549 km | 527 km | +4 % |

**Cached artefacts.** The 320 MB HydroRIVERS download is git-ignored, but the two
derived files — `study_river_stems.geojson` and `osm_tidal_reaches.geojson` —
are small and **are** committed, so the river kilometres and both maps reproduce
without re-downloading the network.

### 4.8 Which gauges count as being on the study river

`pipeline/monitoring_stations.py` builds one station table across both
temperature sources and applies two filters that the earlier pipeline lacked:

1. **Water-body category.** Waterbase samples are restricted to
   `parameterWaterBodyCategory = 'RW'` (§2.1). Without this, groundwater wells
   near a river enter the panel as river gauges.
2. **Tributary check.** Even among river sites, some sit within a kilometre of
   the main stem but belong to a *tributary* — at Biblis the Weschnitz and the
   Schwarzbach both join the Rhine within a few kilometres of the plant. The
   filter reads the **first substantive token** of the water-body name, because
   that is the river the name describes: `DONAU VON EINMUENDUNG LECH BIS …` is
   the Danube, whereas `LECH VON … BIS MUENDUNG IN DIE DONAU` is the Lech and
   merely mentions the Danube. A plain substring test accepts both; the token
   test separates them. Leading qualifiers (`OBERER`, `UNTERE`, `FREIFLIESSENDE`,
   …) are skipped, canals are rejected, and where the name is missing or a
   placeholder the site must instead lie within 300 m of the centre-line.
   This removes 29 Waterbase sites. GKD gauges are exempt: GKD states the river
   per gauge in its own index.

### 4.9 Pairing gauges to plants — `pipeline/station_pairs.py`

The unit of analysis is the **physical site**, not the block. Blocks that share a
site share exact coordinates, so a "nearest upstream reactor" rule broke ties by
list order: Biblis A took every downstream gauge and **Biblis B got none**, and
likewise Philippsburg 2, Neckarwestheim 2, Isar 2 and Gundremmingen C. That
alone produced five of the empty rows in the earlier per-plant table. Site level
is also the right physical unit — the river responds to the site's *total*
cooling load, which is how the group logic in §3 already argues.

For each site and each shutdown year the module ranks every gauge within 120 km
along the channel as `upstream` (control) or `downstream` (treated) and flags
contamination: a gauge is **not clean** if another study site lies between it and
the focal plant *and* that other site also changed load within ±2 years. The
estimation takes the nearest clean gauge on each side; the remaining downstream
gauges form the distance-sensitivity curve.

Coverage result (`analysis/station_coverage.csv`): **8 of 14 site-events** have a
usable upstream *and* downstream gauge with data starting before the shutdown —
but only **one** of those is a 2011 event (Isar). For Biblis, Philippsburg,
Neckarwestheim and Unterweser the pre-period does not exist in any source we have
so far opened.

## 5. Summary of exclusion / flagging decisions

| Unit | Decision | Reason |
|---|---|---|
| Grafenrheinfeld | out of control, flagged `staggered_treatment` | shutdown 2015, inside the window |
| Gundremmingen B | out of control, flagged `staggered_treatment` | shutdown 2017, inside the window |
| Krümmel | excluded | effectively offline since 2007/2009, no 2011 shock |
| Brunsbüttel | excluded | effectively offline since 2007, no 2011 shock |
| Isar 2 / Neckarwestheim 2 / Philippsburg 2 | control, with a site-level 2011 partial-load note | block ran throughout; sister block shut in 2011 |
| Sites/stations/plants > radius | filtered out | outside the spatial study area |
| Waterbase sites with category ≠ `RW` | filtered out | groundwater / drinking water / lake, not a river (§2.1) |
| Waterbase sites on a tributary | filtered out | near the main stem but on another water body (§4.8) |
| Gauges > 120 km along the channel | filtered out | beyond any plausible plume, and the pairing radius (§4.9) |
| Gauges downstream of another simultaneously changing site | flagged `clean = False` | the control or treated reading is contaminated (§4.9) |
| Event year itself | dropped from the 2×2 | partly treated, partly not |
| Years touching the event (donut spec) | dropped in a robustness run | plants ramp down before the formal date (§10) |

## 6. Open assumptions and next steps

**Resolved in the 29 July revision.** Flow direction is no longer a heuristic
(§4.7). The reactor-vs-site modelling level is settled: **site** (§4.9). Cooling
type has been re-checked and two entries corrected (§3.5). The Waterbase coverage
question is answered — and the answer removes 2011 from that source entirely
(§2.1).

**Still open.**

1. Raw-file download dates for the EEA, OPSD and DWD inputs are not logged;
   versions are recorded (§2).
2. Cooling type is still literature-based rather than licence-based (§3.5).
3. **The binding constraint is now the pre-2011 record for the Rhine, Neckar,
   Weser and Elbe.** The gauges exist physically — PEGELONLINE lists water
   temperature at Rechtenfleth (Weser-km 46.5) and Nordenham (55.8), which
   bracket Unterweser at ~52 — but PEGELONLINE serves only 30 days of history.
   The archives sit with the states: LUBW / HVZ (Neckar, Rhine), HLNUG and
   LfU RLP (Rhine at Biblis), NLWKN and FGG Weser (Weser, Ems), FGG Elbe
   (Brokdorf). `pipeline/gkd_bayern.py` is a template for adding one.
4. **Parallel trends do not hold for a hard 2011 cut on the Isar.** Isar 1 lost a
   fuel element in February 2010 and ran at reduced availability into 2011, so
   treatment intensity fell before the formal shutdown. The donut specification
   (§10) is the honest headline; the effect is robust but the timing is a
   phase-out over 2009–2011, not a step.
5. **No second downstream gauge on the Isar within 120 km.** Plattling sits
   54 km below the plant but only has data from 2020, so the distance decay
   cannot be traced for the one event that identifies an effect. This is the
   largest gap in the sensitivity analysis.
6. Discharge as a continuous exposure/intensity term is not yet used; a plume is
   diluted by streamflow, so low-flow days should carry the largest effect.
7. Staggered sites (Grafenrheinfeld 2015, Gundremmingen 2017/2021) are still not
   part of a *2011* DiD, but they are now estimated in their own right (§10) —
   and they serve as informative negative controls, because their tower cooling
   predicts no effect.

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
    waterbase.py          water temperature + dissolved oxygen (annual, v2020_1)
    waterbase_disaggregated.py  dense monthly/summer panel from the v2025_1 SQLite
    discharge.py          annual discharge from raw GRDC files
    river_position.py     superseded direction-vector position (§4.6)
    weather_download.py   downloads DWD daily KL (historical) for the study sites
    weather.py            DWD monthly aggregation
    power_plants.py       conventional-plant confounders
    tests/test_parsers.py checks the parsers and river-position logic on fixtures
```

Added in the 29 July revision:

```
scripts/
  extract_waterbase_de.py      one full scan of the 30 GB Waterbase SQLite ->
                               every German temperature/oxygen sample (§2.1)
  station_coverage_report.py   the per-site upstream/downstream table (§4.9)
  plant_2x2_did.py             the 2x2 estimation (§10)
  pipeline/
    river_network.py           real river stems, true river kilometres (§4.7)
    gkd_bayern.py              daily temperature from GKD Bayern (§2.2)
    monitoring_stations.py     one station table, RW + tributary filters (§4.8)
    station_pairs.py           site-level upstream/downstream pairing (§4.9)
    boundaries.py              cached national boundary for the maps (§8)
```

Run the original pipeline with `python scripts/build_all.py`; steps whose raw
inputs are absent skip themselves with a hint. Run the parser checks with
`python scripts/pipeline/tests/test_parsers.py`. The window and radius are the
constants `WINDOW_START`, `WINDOW_END` and `SITE_RADIUS_KM` in `config.py`.

The revised chain runs in this order; each step caches, so only the first run is
slow:

```bash
python scripts/extract_waterbase_de.py     # needs the Waterbase SQLite locally
python scripts/pipeline/river_network.py   # downloads HydroRIVERS on first run
python scripts/pipeline/gkd_bayern.py      # ~10 min, cached per station
python scripts/station_coverage_report.py
python scripts/plant_2x2_did.py
python scripts/make_study_map.py
python scripts/make_sites_by_reactor.py
```

New third-party dependencies: `geopandas`, `shapely`, `pyogrio` (river geometry)
and `requests` (GKD, Overpass).

## 8. Figures

*Rewritten 29 July 2026.* Both maps now draw the **same geometry the estimation
uses** — the HydroRIVERS/OSM stems of §4.7, not a separate cartographic layer —
so a reader can check the up/downstream claim directly off the map. Flow arrows
follow the stem's own ordering, i.e. the network topology, and are not drawn from
a compass bearing. The national boundary comes from `pipeline/boundaries.py`
(cached, §2); the rivers run past it, so the outline is what makes clear which
reach is inside the sample.

- `scripts/make_study_map.py` → `figures/study_map.png`. National overview:
  plant sites shaped and coloured by group, the eight study rivers with flow
  arrows and names, and every gauge that is within the 120 km pairing radius.
  Gauges are coloured by source (GKD green = daily and usable before 2011,
  Waterbase grey = spot samples from 2020). Each gauge carries a number on the
  map and is listed **by name below the map**, with its river, river kilometre
  and the span of available readings — that keeps the map legible while still
  naming every station.
- `scripts/make_sites_by_reactor.py` → `figures/study_sites_by_reactor.png`. One
  zoomed panel per site, with each gauge labelled by **name and along-river
  distance** (↑ upstream, ↓ downstream) and the pair actually used by the 2×2
  drawn larger. This is the figure that shows, per plant, whether the design has
  a control and a treated gauge at all.
- `figures/plant_2x2/<site>_<year>_2x2.png` — monthly upstream and downstream
  series with the gap underneath, per site-event.
- `figures/plant_2x2/long_run_gap.png` — the annual gap over the whole record.
  This is the diagnostic that shows *when* the gap moved, which the ±3-year
  window cannot.
- `figures/plant_2x2/distance_sensitivity.png` — estimate against the along-river
  distance of the downstream gauge.

The maps download the boundary and river network once and then work offline.

## 9. Analysis: first difference-in-differences pass *(superseded)*

> **Superseded on 29 July 2026.** Everything in this section rests on the
> Waterbase panel *without* a water-body-category filter, so its pre-2011
> observations are groundwater, not river water (§2.1). It is kept as a record of
> what was tried. The current design is §10.

**Dense outcome panel.** The annual AggregatedData is too sparse for a DiD, so
we switched the water outcomes to the **Waterbase v2025_1 disaggregated
(individual-sample) data**. `scripts/pipeline/waterbase_disaggregated.py` reads
the ~97 M-row SQLite, keeps German water-temperature and dissolved-oxygen samples
within 50 km of a study reactor, and aggregates them to a **monthly** and a
**summer (Jun–Sep)** panel per site
(`water_quality_{monthly,summer}_by_site.csv`). Because the disaggregated table's
`waterBodyName` is frequently the placeholder `"NAME"`, the river is matched
**geometrically** from the coordinates (`mapdata.river_matcher`, ≤ 2.5 km to a
Natural-Earth centre-line) rather than by name; this recovered continuous
2008–2024 coverage that name matching missed.

**Coverage is the binding constraint.** `scripts/did_analysis.py` maps the
downstream summer-temperature coverage by group and year
(`figures/did_coverage.png`). The result: the clean **treatment** (Biblis,
Unterweser) and **control** reactors (Grohnde, Emsland, Brokdorf) are barely
monitored downstream — the control group has **no observation before 2011** — so
a strict treatment-vs-control 2011 DiD is **not identified**. The coverage sits
with the **partial** (Philippsburg, Neckarwestheim; 9 sites) and **staggered**
(Grafenrheinfeld 2015, Gundremmingen 2017; 5 sites) reactors.

**Recommended design (data-driven).** Use a **generalised / staggered DiD**: a
downstream site becomes treated in the year its nearest upstream reactor shut
down (2011 partial/treatment, 2015 Grafenrheinfeld, 2017 Gundremmingen), with
still-running reactors as (not-yet-)controls — estimated with Callaway–Sant'Anna
to avoid the two-way-FE bias. A within-river **downstream-vs-upstream** contrast
per shutdown is a complementary clean identification. Full write-up and figures:
`data/processed/analysis/did_water_temperature_results.md`,
`figures/did_coverage.png`, `figures/did_trends.png`.

## 10. Analysis: the per-site 2×2 (current design)

*Added 29 July 2026. Code: `scripts/plant_2x2_did.py`. Results:
`analysis/plant_2x2/plant_2x2_results.csv`. Full write-up:
`analysis/DATENAUDIT_UND_2x2.md`.*

### 10.1 The estimand

For one site and one shutdown year the 2×2 is

|  | before | after |
|---|---|---|
| upstream (control) | mean T_up,before | mean T_up,after |
| downstream (treated) | mean T_down,before | mean T_down,after |

and the estimate is the difference of the two differences.

### 10.2 Specification

Because both gauges sit on the same river and are read on the same days, the
sharper way to write the identical quantity is the **paired daily difference**:

```
ΔT_t = T_downstream,t − T_upstream,t
ΔT_t = a + b · post_t + month fixed effects + e_t
```

`b` is numerically the DiD estimate but differences out weather, season and any
river-wide trend before estimation rather than relying on the regression to
absorb them. Daily river temperature is strongly persistent, so standard errors
are **Newey–West (HAC) with a 30-day bandwidth**. The window is ±3 years around
the shutdown, with the event year itself dropped. The textbook pooled two-gauge
regression (`temp ~ treated * post + month FE`, clustered on the gauge) is
reported alongside as a cross-check and agrees to three decimals.

### 10.3 Robustness shipped with every estimate

- **Donut** — drop the whole year either side of the shutdown. Plants do not
  switch off cleanly, so those years are neither properly treated nor properly
  untreated.
- **Placebo** — the same regression on a fake shutdown three years earlier, with
  the sample truncated before the real event so the placebo cannot inherit part
  of the true effect.
- **Season split** — summer (Jun–Sep, low flow, warm water) against the rest of
  the year, where a thermal plume should matter most.
- **Distance sensitivity** — re-estimated against every available downstream
  gauge, so the effect can be plotted against along-river distance.
- **Long-run gap** — the annual gap across the whole record, which shows *when*
  the gap moved.

### 10.4 Results

| Site | Event | `river_heat_load` | Gap before | Gap after | **DiD** | p | Donut | Placebo |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| **Isar** | **2011** | **high** | **+1.90 °C** | **−0.03 °C** | **−1.93 °C** | <1e−16 | **−2.08** | −0.20 (n.s.) |
| Isar | 2023 | low | +0.19 °C | +0.05 °C | −0.14 °C | 0.15 | — | +0.19 |
| Grafenrheinfeld | 2015 | low | +0.09 °C | +0.50 °C | +0.41 °C | <1e−4 | +0.55 | −0.05 (n.s.) |
| Gundremmingen | 2017 | low | +0.65 °C | +0.86 °C | +0.21 °C | 0.002 | +0.12 | **−0.52** |
| Gundremmingen | 2021 | low | +0.86 °C | +1.08 °C | +0.22 °C | 0.0003 | +0.31 | **+0.32** |

**Isar 2011 is the result.** The gap between Landau (34 km below) and
Landshut-Birket (16 km above) sits at +1.9 to +2.2 °C from 2007 to 2009, falls,
and is flat at about zero from 2012 to 2024. The magnitude matches Isar 1's
licensed warming span of up to 2.5 K. The placebo is null.

**The strongest robustness check is internal to the site.** The same gauge pair
sees two shutdowns:

- Isar 1, 2011, **once-through** → −1.93 °C, highly significant
- Isar 2, 2023, **cooling tower** → −0.14 °C, not significant

Same river, same gauges, same method; the only difference is the cooling
technology. That is a tighter test of the mechanism than any cross-plant
comparison in this data could give.

**The cooling-tower sites are not identified, not "zero".** At Gundremmingen 2021
the placebo (+0.32) is as large as the "effect" (+0.31), and the annual gap
wanders between 0.35 and 1.4 °C across the record with no visible break at either
shutdown. At Grafenrheinfeld the estimate has the **wrong sign** — downstream
gets *warmer* after the shutdown. Both are consistent with the physics (§3.5:
almost no heat reached those rivers), but neither should be reported as an effect
estimate. They belong in the paper as a heterogeneity result: **the effect appears
exactly where the cooling technology predicts it**.

### 10.5 Known limitations of this design

1. Parallel trends fail for a hard 2011 cut on the Isar (§6, item 4); the donut
   specification is the honest headline.
2. Only one 2011 event is estimable at all (§4.9), so the 2011 evidence rests on
   a single site.
3. The distance decay cannot be traced on the Isar for lack of a second
   downstream gauge with pre-2011 data (§6, item 5).
4. Discharge is not yet used as an exposure term (§6, item 6).
