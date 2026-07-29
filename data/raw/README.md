# Raw Data

Source files used by the pipeline. Most are unmodified downloads; a few are
fetched automatically on first use and then cached here.

## Structure

```text
data/raw/
  power_plants/
    conventional_power_plants_DE.csv          manual download (OPSD)
  waterbase/
    Waterbase_v2020_1_S_WISE6_SpatialObject_DerivedData.csv   manual
    Waterbase_v2020_1_T_WISE6_AggregatedData.csv              manual
    Waterbase_v2025_1_WISE6_DisaggregatedData.sqlite          manual, ~30 GB
    de_sites_raw.csv        <- written by scripts/extract_waterbase_de.py
    de_samples_raw.csv      <- written by scripts/extract_waterbase_de.py
  discharge/
    *_Q_Day.Cmd.txt                           manual download (GRDC)
  weather/
    stations_DWD.csv                          manual; daily data is downloaded
  rivers/
    HydroRIVERS_v10_eu_shp/     <- auto-downloaded by pipeline/river_network.py
    study_river_stems.geojson   <- derived, COMMITTED
    osm_tidal_reaches.geojson   <- derived from Overpass, COMMITTED
  borders/
    germany.geo.json            <- auto-downloaded by pipeline/boundaries.py
  gkd/
    gkd_stations.csv            <- written by pipeline/gkd_bayern.py
    daily/<station_id>.csv      <- one file per gauge, cached
```

## What is and is not in git

The Waterbase, GRDC and HydroRIVERS inputs exceed GitHub's file limits or are
simply large, so `.gitignore` keeps them local. Two small derived files under
`rivers/` **are** committed — `study_river_stems.geojson` and
`osm_tidal_reaches.geojson` — so the river kilometres and both maps reproduce
without re-downloading the 320 MB river network.

## Where to get each input

| Input | Source |
|---|---|
| Conventional power plants | Open Power System Data, `conventional_power_plants_DE` |
| Waterbase (aggregated / disaggregated) | EEA Waterbase WISE6, v2020_1 and v2025_1 |
| River discharge | GRDC (Global Runoff Data Centre, BfG) |
| Weather | DWD Climate Data Center, daily climate (KL), historical |
| River network | <https://www.hydrosheds.org/products/hydrorivers> (Europe) — auto |
| Tidal Elbe / Weser geometry | OpenStreetMap via Overpass, © OSM contributors, ODbL — auto |
| National boundary | <https://github.com/isellsoap/deutschlandGeoJSON> — auto |
| Daily water temperature | <https://www.gkd.bayern.de/de/fluesse/wassertemperatur> — auto |

A caveat worth repeating: the Waterbase mixes groundwater, drinking-water and
lake monitoring points into the same table, and Germany reported **no river
water temperature before 2020**. Always filter on
`parameterWaterBodyCategory = 'RW'`. See `../processed/METHODS.md` §2.1.
