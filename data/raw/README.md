# Raw Data

Place source CSV files here. These files are the unmodified inputs used by
`scripts/prepare_data.py`.

## Structure

```text
data/raw/
  power_plants/
    conventional_power_plants_DE.csv
  waterbase/
    Waterbase_v2020_1_S_WISE6_SpatialObject_DerivedData.csv
    Waterbase_v2020_1_T_WISE6_AggregatedData.csv
  weather/
    weather_data.csv
```

The large Waterbase and weather CSV files exceed GitHub's regular 100 MB file
limit. Keep them in this folder locally, or upload them with Git LFS or another
data storage service if they need to be available online.
