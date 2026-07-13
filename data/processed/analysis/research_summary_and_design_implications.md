# Research Summary and Practical Design Implications

Date: 2026-07-13

## Important Research Information

## A) Plant-station distances in this project

- Distance table: `data/processed/analysis/nuclear_to_monitoring_station_distances.csv`
- Unique downstream reactor-site pairs: 36
- Coverage is uneven by reactor and by group, with substantial far-field (`>50 km`) observations in control and staggered groups.

## B) Thermal dispersion and effective impact distance

- There is no universal fixed distance where thermal impact is always negligible.
- Impact attenuation depends on discharge heat load, flow, morphology, season, and cumulative upstream heat loads.
- Historical EU fish-water logic evaluates compliance at the edge of the mixing zone rather than at a fixed kilometer cutoff.

Relevant sources used in project notes:
- Directive 2006/44/EC Annex I adopted XML:
  https://www.legislation.gov.uk/eudr/2006/44/annex/I/adopted/data.xml
- Madden et al. (2013), ERL, once-through impacts:
  DOI 10.1088/1748-9326/8/3/035006
- Miara et al. (2018), ERL, basin-scale thermal constraints:
  DOI 10.1088/1748-9326/aaac85

## C) Environmental regulation context

- Historical EU benchmark (fish waters, Annex I):
  - +1.5 C (salmonid), +3.0 C (cyprinid) max increase at mixing-zone edge
  - absolute temperatures: 21.5 C (salmonid), 28 C (cyprinid)
- Germany legal structure:
  - WHG permit framework: https://www.gesetze-im-internet.de/whg_2009/
  - OGewV ecological framework: https://www.gesetze-im-internet.de/ogewv_2016/
  - AbwV Annex 31 cooling-related wastewater requirements:
    https://www.gesetze-im-internet.de/abwv/anhang_31.html
- Practical curtailment thresholds are permit-specific at plant/river level.

## D) Conventional thermal plants as confounders

- Existing project files already include relevant non-nuclear thermal plants near study reactors:
  - `data/processed/conventional_plants_de_relevant_clean.csv`
  - `data/processed/analysis/power_plants_2006_2018.csv`
- These plants should be treated as explicit time-varying confounders in the DiD specification.

## Practical Implication for Your Design

Keep the original reactor-shock groups for interpretation, but strengthen identification with additional structure and controls.

### Suggested refinements

1. Keep existing structural groups.
2. Add distance strata: `<=25 km`, `25-50 km`, `>50 km`.
3. Add cooling-technology strata: `once-through` vs `cooling_tower`.
4. Use staggered-event estimators for multi-year shutdown timing.
5. Add conventional thermal plants as explicit time-varying controls.

### Implemented in pipeline/code

- New pipeline output:
  - `data/processed/analysis/conventional_controls_by_site_year.csv`
- New controls include:
  - `conv_cap_0_10_mw`
  - `conv_cap_10_25_mw`
  - `conv_cap_25_50_mw`
  - `conv_cap_gt_50_mw`
  - `conv_cap_weighted_mw` (distance-weighted)
  - `nearby_thermal_plant_count`
- DiD script now merges these controls and reports a controls-augmented estimate.
