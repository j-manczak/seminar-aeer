# Analysis inputs and outputs

The full methodology is in [`../METHODS.md`](../METHODS.md). Start with
[`DATENAUDIT_UND_2x2.md`](DATENAUDIT_UND_2x2.md) — it explains why the earlier
per-plant results were empty and what replaced them.

## Current analysis (revision of 29 July 2026)

| File / folder | Content |
|---|---|
| [`DATENAUDIT_UND_2x2.md`](DATENAUDIT_UND_2x2.md) | Data audit, corrected design, results and recommendation (German) |
| `station_coverage.csv` | Per site and shutdown: nearest usable upstream/downstream gauge, whether the 2×2 is estimable, and if not why |
| `plant_2x2/plant_2x2_results.csv` | All 2×2 estimates — headline, donut, placebo, season split, distance sensitivity |
| `plant_2x2/station_pairs.csv` | Every candidate gauge per site-event with role, along-river distance and contamination flag |
| `../gkd_water_temperature_daily.csv` | 305,070 daily station readings, GKD Bayern, 1995–2024 (Isar, Danube, Main) |

Figures: `../../figures/plant_2x2/`, `../../figures/study_map.png`,
`../../figures/study_sites_by_reactor.png`.

Rebuild:

```bash
python scripts/extract_waterbase_de.py     # needs the Waterbase SQLite locally
python scripts/pipeline/river_network.py   # downloads HydroRIVERS on first run
python scripts/pipeline/gkd_bayern.py      # ~10 min, cached per station
python scripts/station_coverage_report.py
python scripts/plant_2x2_did.py
python scripts/make_study_map.py
python scripts/make_sites_by_reactor.py
```

## Superseded

`plant_level_did/` and `2x2_2011_shutdowns/` are **not to be used**. They rest on
the Waterbase panel without a water-body-category filter, so their pre-2011
observations come from groundwater wells rather than rivers — Germany reported no
river water temperature to the EEA before 2020. Each folder carries a
`SUPERSEDED.md` with the details.

`did_water_temperature_results.md` and the figures `did_coverage.png` /
`did_trends.png` share the same defect and should be read only as a record of the
first pass.

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
