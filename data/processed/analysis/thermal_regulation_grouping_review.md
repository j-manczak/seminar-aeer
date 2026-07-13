# Thermal Distance, Regulation, Grouping, and Controls Review

Date: 2026-07-13

## 1) Measurement station distances (calculated from project data)

Source table: `data/processed/analysis/water_quality_summer_by_site.csv`
Derived table: `data/processed/analysis/nuclear_to_monitoring_station_distances.csv`

The derived table contains unique reactor-site downstream pairs with along-river distance in km.
Total unique downstream reactor-site pairs: **36**.

### Distance summary by associated reactor (unique sites)

- Neckarwestheim 1: n=5, min=11.4, p25=12.0, median=14.4, p75=58.9, max=71.7 km
- Biblis A: n=4, min=12.9, p25=23.7, median=30.4, p75=34.0, max=35.9 km
- Isar 1: n=2, min=14.3, p25=22.5, median=30.6, p75=38.8, max=47.0 km
- Grafenrheinfeld: n=7, min=13.7, p25=26.4, median=35.2, p75=76.5, max=129.1 km
- Philippsburg 1: n=4, min=25.5, p25=32.5, median=35.6, p75=39.0, max=46.3 km
- Grohnde: n=9, min=16.6, p25=32.8, median=118.3, p75=141.6, max=154.6 km
- Gundremmingen B: n=5, min=110.3, p25=117.1, median=126.3, p75=129.6, max=154.7 km

## 2) Physical distance where thermal impact becomes negligible

There is **no single universal distance**. It depends on discharge heat load, river flow, season, meteorology, morphology, and cumulative upstream heat loads.

Evidence and interpretation used here:

- EU fish-water framework logic (historical): compliance is checked at the **edge of the mixing zone**, not at a fixed km distance. This implies that physics and local hydrology define "effective impact distance".
  - Source: Directive 2006/44/EC Annex I (adopted text)
  - URL: https://www.legislation.gov.uk/eudr/2006/44/annex/I/adopted/data.xml
- Power-sector thermal impact literature confirms basin-scale dependence and that impacts can propagate non-trivially downstream under low-flow/high-heat periods.
  - Madden et al. 2013, Environmental Research Letters, DOI 10.1088/1748-9326/8/3/035006
  - Miara et al. 2018, Environmental Research Letters, DOI 10.1088/1748-9326/aaac85

Practical study recommendation for this dataset:

- Keep current bins (`0-10`, `10-25`, `25-50`) as near field/mid field.
- Add a **far-field comparator** (`>50`) explicitly in robustness checks because many control/staggered observations are far-field.
- Treat distance as a continuous exposure in the regression (splines or piecewise linear), not only categorical bins.

## 3) Environmental regulations: temperature and discharge constraints

## 3.1 EU-level historical benchmark (fish waters)

Directive 2006/44/EC Annex I (repealed, but still useful as historical benchmark) specifies:

- At edge of mixing zone, temperature increase limit relative to unaffected water:
  - salmonid waters: **+1.5 C**
  - cyprinid waters: **+3.0 C**
- Absolute downstream temperatures at edge of mixing zone:
  - salmonid waters: **21.5 C**
  - cyprinid waters: **28 C**
- Additional 10 C clause for breeding periods in cold-water species waters.

Source URL: https://www.legislation.gov.uk/eudr/2006/44/annex/I/adopted/data.xml

## 3.2 Germany legal structure (current)

- WHG (Wasserhaushaltsgesetz): permitting framework for water use and wastewater discharge; site permits define operational discharge conditions.
  - URL: https://www.gesetze-im-internet.de/whg_2009/
- OGewV (surface water ordinance): status/quality framework for water bodies; supports ecological status protection but does not provide one universal national single number for every discharge case in one simple clause.
  - URL: https://www.gesetze-im-internet.de/ogewv_2016/
- AbwV Annex 31: emission-quality requirements for cooling-system wastewater streams (AOX, chlorine/oxidants, zinc, toxicity etc.) relevant to cooling water management.
  - URL: https://www.gesetze-im-internet.de/abwv/anhang_31.html

Operational implication:

- In Germany, practical curtailment/stop decisions are typically permit-based (plant and river specific) and triggered in heat/low-flow events when downstream limits cannot be met.
- Therefore, exact thresholds for each plant should be read from each plant's permit (`wasserrechtlicher Bescheid`) and temporary derogations if granted.

## 3.3 Must withdrawn cooling water be returned?

- For once-through systems, withdrawn river water is generally returned to the receiving water body after use (with thermal and chemical constraints).
- For recirculating/cooling-tower systems, only part returns as blowdown; a substantial share is evaporative consumption.
- Return/discharge conditions are controlled via permit terms and wastewater standards (e.g., AbwV Annex 31 substance limits).

## 4) Review of current grouping

Current reactor groups are conceptually strong for identifying the 2011 shock:

- `treatment`: full 2011 shutdown shock
- `partial`: partial 2011 shutdown at multi-block sites
- `control`: on-grid across window
- `staggered_treatment`: later in-window shutdowns
- `excluded`: effectively already offline before 2011

However, data support is unbalanced in the near field:

- Mean unique downstream sites/year (2008-2020):
  - treatment: 1.00
  - control: 2.15
  - partial: 3.17
  - staggered_treatment: 4.91
- Control and staggered groups contain many `>50 km` observations.

Suggested refinement for analysis (without deleting existing groups):

1. Keep current structural groups, but add a **distance stratum**:
   - near (`<=25 km`), mid (`25-50 km`), far (`>50 km`).
2. Add **cooling-technology stratum** (`once_through` vs `cooling_tower`) since effect strength should differ physically.
3. For strict 2011 DiD, run a primary spec on `<=50 km`, and a secondary tighter spec on `<=25 km` to improve exposure plausibility.
4. Use staggered-event estimators (Callaway-Sant'Anna or Sun-Abraham style) for all shutdown years.

## 5) Inclusion of non-nuclear thermal power plants

Your current analysis assets already include conventional plants near study reactors:

- `data/processed/conventional_plants_de_relevant_clean.csv`
- `data/processed/analysis/power_plants_2006_2018.csv`

Coverage summary from `power_plants_2006_2018.csv`:

- 38 units (19 unique plant names)
- Capacity by nearest reactor group:
  - control-near units: 18 units, 5827.0 MW total, median distance 37.04 km
  - partial-near units: 18 units, 6530.0 MW total, median distance 21.83 km
  - treatment-near units: 2 units, 907.5 MW total, median distance 21.80 km
- Distance bins:
  - 0-10 km: 7 units
  - 10-25 km: 14 units
  - 25-50 km: 17 units

Conclusion:

- Non-nuclear thermal plants are **already not excluded** from your broader project data layer.
- They should be added explicitly as **time-varying control variables** in treatment-effect models where possible (e.g., nearby conventional thermal capacity weighted by distance and cooling type).

## Recommended next modeling variables

From existing data, construct yearly controls per site:

1. `conv_cap_0_10_km`, `conv_cap_10_25_km`, `conv_cap_25_50_km`
2. `conv_cap_weighted` (e.g., sum(capacity / (distance_km+1)))
3. `conv_once_through_cap_weighted` and `conv_tower_cap_weighted`
4. `nearby_plant_count` and `nearby_chp_count`

These will reduce omitted-variable bias in attributing thermal changes to nuclear shutdown shocks alone.
