# Analysis inputs (2006–2018 window, study sites)

Every file here is produced by

```
python scripts/build_all.py
```

and is filtered to the study sites (within the site radius of a study reactor)
and to the years 2006–2018. Each file starts with `#` comment lines that record
the exact filter. The full methodology is in [`../METHODS.md`](../METHODS.md).

| File | Content | In git? |
|---|---|---|
| `power_plants_2006_2018.csv` | conventional thermal plants (confounders) | committed |
| `weather_2006_2018.csv` | DWD weather, station–month aggregates | committed |
| `water_temperature_2006_2018.csv` | Waterbase annual water temperature | built locally from raw Waterbase |
| `dissolved_oxygen_2006_2018.csv` | Waterbase annual dissolved oxygen | built locally from raw Waterbase |
| `discharge_2006_2018.csv` | GRDC annual river discharge | built locally from raw GRDC |

The last three need the raw inputs in `data/raw/waterbase/` and
`data/raw/discharge/`. Those inputs are large and kept out of git (see
`.gitignore`); once they are in place, `build_all.py` regenerates the three
files. If the raw inputs are missing, those steps skip themselves with a hint.
