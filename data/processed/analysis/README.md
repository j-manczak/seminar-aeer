# Analysis inputs and outputs

The full methodology is in [`../METHODS.md`](../METHODS.md). Start with
[`DATENAUDIT_UND_2x2.md`](DATENAUDIT_UND_2x2.md) — it explains why the earlier
per-plant results were empty and what replaced them.

## Current analysis (revision of 29 July 2026)

| File / folder | Content |
|---|---|
| [`DATENAUDIT_UND_2x2.md`](DATENAUDIT_UND_2x2.md) | Data audit, corrected design, results and recommendation (German) |
| `station_coverage.csv` | Per site and shutdown: nearest usable upstream/downstream gauge, whether the 2×2 is estimable, and if not why |
| `plant_2x2/plant_2x2_results.csv` | All 2×2 estimates, both outcomes — headline, best-coverage pair, donut, placebo, season split, distance sweep, with a minimum-detectable-effect column |
| `plant_2x2/station_pairs.csv` | Every candidate gauge per site-event with role, along-river distance and contamination flag |
| `plant_2x2/distance_sensitivity.csv` | Effect against along-river distance, with a verdict per estimate (effect / drift / underpowered / null) |
| `plant_2x2/analysis_radius.json` | The along-river radius derived from the distance analysis (50 km), read by the confounder report and both maps |
| `plant_2x2/confounders_by_site_event.csv` | Other condensing thermal plants on the same reach, and whether any changed near the shutdown |
| `plant_2x2/thermal_plants_on_study_rivers.csv` | All condensing plants ≥ 50 MW placed on the river network |
| `plant_2x2/effect_per_generation.csv` | Warming per TWh of generation removed and per GW of river-bound waste heat |
| `plant_2x2/reactor_thermal_load.csv` | Thermal rating, waste heat, river share and annual generation per reactor block |
| [`ENERGIEERZEUGER_JE_STANDORT.md`](ENERGIEERZEUGER_JE_STANDORT.md) | Per site: every other power station on the same river, with coordinates, along-river distance to the plant and to both gauges, which side of each gauge it sits on, how it generates, and whether it takes river cooling water |
| `plant_2x2/energy_producers_by_site.csv` | The same inventory as data |
| `../gkd_water_temperature_daily.csv` | 305,070 daily station readings, GKD Bayern, 1995–2024 (Isar, Danube, Main) |
| `../gkd_dissolved_oxygen.csv` | 45,336 dissolved-oxygen readings, GKD chemistry programme, 1990–2024 |

Figures: `../../figures/plant_2x2/`, `../../figures/site_context/`,
`../../figures/study_map.png`, `../../figures/study_sites_by_reactor.png`.

Rebuild:

```bash
python scripts/extract_waterbase_de.py     # needs the Waterbase SQLite locally
python scripts/pipeline/river_network.py   # downloads HydroRIVERS on first run
python scripts/pipeline/gkd_bayern.py      # ~10 min, cached per station
python scripts/pipeline/gkd_chemie.py       # ~5 min, cached per sampling point
python scripts/station_coverage_report.py
python scripts/plant_2x2_did.py
python scripts/distance_sensitivity.py     # writes analysis_radius.json
python scripts/confounder_report.py        # reads the radius
python scripts/effect_per_generation.py
python scripts/make_study_map.py
python scripts/make_sites_by_reactor.py
python scripts/site_energy_context.py     # site inventory + per-site maps
```

## Superseded — moved to `Archiv/`

Everything from the first, Waterbase-based pass now lives under `Archiv/`
(analysis outputs, figures and scripts), with `Archiv/README.md` explaining why.
Nothing was deleted. Short version: those results rest on the Waterbase panel
without a water-body-category filter, so their pre-2011 observations come from
groundwater wells rather than rivers — Germany reported no river water
temperature to the EEA before 2020.

## Original 2006–2018 build (`python scripts/build_all.py`)

Every file below is filtered to the study sites (within the site radius of a
study reactor) and to 2006–2018, and starts with `#` comment lines recording the
exact filter.

| File | Content | In git? |
|---|---|---|
| `power_plants_2006_2018.csv` | conventional thermal plants (confounders) | committed |
| `weather_2006_2018.csv` | DWD weather, station–month aggregates | committed |
| `water_temperature_2006_2018.csv` | Waterbase annual water temperature — **not filtered by water-body category, see above** | built locally from raw Waterbase |
| `dissolved_oxygen_2006_2018.csv` | Waterbase annual dissolved oxygen — same caveat | built locally from raw Waterbase |
| `discharge_2006_2018.csv` | GRDC annual river discharge | built locally from raw GRDC |

The last three need the raw inputs in `data/raw/waterbase/` and
`data/raw/discharge/`. Those inputs are large and kept out of git (see
`.gitignore`); once they are in place, `build_all.py` regenerates the three
files. If the raw inputs are missing, those steps skip themselves with a hint.
