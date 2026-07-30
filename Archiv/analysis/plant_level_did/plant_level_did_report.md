# Plant-Level 2x2 Difference-in-Differences Review

This report summarizes exploratory per-plant 2x2 DiD diagnostics using
upstream stations as control and downstream stations as treated units.

## Plant Summary

| Plant            |   Shutdown |   Upstream stations |   Downstream stations | DiD estimable   |       beta |   N |   upstream_pre_n |   upstream_post_n |   downstream_pre_n |   downstream_post_n |
|:-----------------|-----------:|--------------------:|----------------------:|:----------------|-----------:|----:|-----------------:|------------------:|-------------------:|--------------------:|
| Biblis A         |       2011 |                   6 |                     4 | True            |   2.11257  |  51 |                2 |                38 |                  3 |                   8 |
| Biblis B         |       2011 |                   6 |                     0 | False           | nan        |  40 |                2 |                38 |                  0 |                   0 |
| Unterweser       |       2011 |                  10 |                     0 | False           | nan        |  54 |                5 |                49 |                  0 |                   0 |
| Isar 1           |       2011 |                   2 |                     2 | False           | nan        |  24 |                0 |                14 |                  0 |                  10 |
| Isar 2           |       2023 |                   2 |                     0 | False           | nan        |  12 |               11 |                 1 |                  0 |                   0 |
| Neckarwestheim 1 |       2011 |                   4 |                     5 | False           | nan        |  59 |                0 |                27 |                  0 |                  32 |
| Neckarwestheim 2 |       2023 |                   4 |                     0 | False           | nan        |  23 |               19 |                 4 |                  0 |                   0 |
| Philippsburg 1   |       2011 |                   2 |                     4 | False           | nan        |  40 |                0 |                10 |                  2 |                  28 |
| Philippsburg 2   |       2019 |                   2 |                     0 | False           | nan        |  10 |                2 |                 8 |                  0 |                   0 |
| Grohnde          |       2021 |                   1 |                     9 | True            |   3.95341  |  48 |                1 |                 2 |                 28 |                  17 |
| Emsland          |       2023 |                   3 |                     0 | False           | nan        |  17 |               15 |                 2 |                  0 |                   0 |
| Brokdorf         |       2021 |                   4 |                     0 | False           | nan        |   7 |                4 |                 3 |                  0 |                   0 |
| Grafenrheinfeld  |       2015 |                   6 |                     7 | True            |   0.583542 |  92 |               13 |                27 |                 14 |                  38 |
| Gundremmingen B  |       2017 |                   2 |                     5 | False           | nan        |  42 |                0 |                 8 |                 11 |                  23 |
| Gundremmingen C  |       2021 |                   2 |                     0 | False           | nan        |   6 |                2 |                 4 |                  0 |                   0 |

## Distance Sensitivity (Temperature, Simple DiD)

| Plant            | Distance   |       beta |          SE |       p-value |   N | estimable   | message                                                                           |
|:-----------------|:-----------|-----------:|------------:|--------------:|----:|:------------|:----------------------------------------------------------------------------------|
| Biblis A         | <= 10      | nan        | nan         | nan           |  40 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Biblis A         | <= 25      | nan        | nan         | nan           |  43 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Biblis A         | <= 50      |   2.11257  |   2.44021   |   0.386635    |  51 | True        |                                                                                   |
| Biblis A         | <= 75      |   2.11257  |   2.44021   |   0.386635    |  51 | True        |                                                                                   |
| Biblis B         | <= 10      | nan        | nan         | nan           |  40 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Biblis B         | <= 25      | nan        | nan         | nan           |  40 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Biblis B         | <= 50      | nan        | nan         | nan           |  40 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Biblis B         | <= 75      | nan        | nan         | nan           |  40 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Unterweser       | <= 10      | nan        | nan         | nan           |  54 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Unterweser       | <= 25      | nan        | nan         | nan           |  54 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Unterweser       | <= 50      | nan        | nan         | nan           |  54 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Unterweser       | <= 75      | nan        | nan         | nan           |  54 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Isar 1           | <= 10      | nan        | nan         | nan           |  14 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Isar 1           | <= 25      | nan        | nan         | nan           |  20 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Isar 1           | <= 50      | nan        | nan         | nan           |  24 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Isar 1           | <= 75      | nan        | nan         | nan           |  24 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Isar 2           | <= 10      | nan        | nan         | nan           |  12 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Isar 2           | <= 25      | nan        | nan         | nan           |  12 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Isar 2           | <= 50      | nan        | nan         | nan           |  12 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Isar 2           | <= 75      | nan        | nan         | nan           |  12 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Neckarwestheim 1 | <= 10      | nan        | nan         | nan           |  27 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Neckarwestheim 1 | <= 25      | nan        | nan         | nan           |  42 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Neckarwestheim 1 | <= 50      | nan        | nan         | nan           |  42 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Neckarwestheim 1 | <= 75      | nan        | nan         | nan           |  59 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Neckarwestheim 2 | <= 10      | nan        | nan         | nan           |  23 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Neckarwestheim 2 | <= 25      | nan        | nan         | nan           |  23 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Neckarwestheim 2 | <= 50      | nan        | nan         | nan           |  23 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Neckarwestheim 2 | <= 75      | nan        | nan         | nan           |  23 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Philippsburg 1   | <= 10      | nan        | nan         | nan           |  10 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Philippsburg 1   | <= 25      | nan        | nan         | nan           |  10 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Philippsburg 1   | <= 50      | nan        | nan         | nan           |  40 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Philippsburg 1   | <= 75      | nan        | nan         | nan           |  40 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Philippsburg 2   | <= 10      | nan        | nan         | nan           |  10 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Philippsburg 2   | <= 25      | nan        | nan         | nan           |  10 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Philippsburg 2   | <= 50      | nan        | nan         | nan           |  10 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Philippsburg 2   | <= 75      | nan        | nan         | nan           |  10 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Grohnde          | <= 10      | nan        | nan         | nan           |   3 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Grohnde          | <= 25      |   0.533167 |   0.0451335 |   3.34053e-32 |  12 | True        |                                                                                   |
| Grohnde          | <= 50      |   1.88117  |   1.33841   |   0.159867    |  22 | True        |                                                                                   |
| Grohnde          | <= 75      |   1.88117  |   1.33841   |   0.159867    |  22 | True        |                                                                                   |
| Emsland          | <= 10      | nan        | nan         | nan           |  17 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Emsland          | <= 25      | nan        | nan         | nan           |  17 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Emsland          | <= 50      | nan        | nan         | nan           |  17 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Emsland          | <= 75      | nan        | nan         | nan           |  17 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Brokdorf         | <= 10      | nan        | nan         | nan           |   7 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Brokdorf         | <= 25      | nan        | nan         | nan           |   7 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Brokdorf         | <= 50      | nan        | nan         | nan           |   7 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Brokdorf         | <= 75      | nan        | nan         | nan           |   7 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Grafenrheinfeld  | <= 10      | nan        | nan         | nan           |  40 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Grafenrheinfeld  | <= 25      |   1.01063  |   3.61055   |   0.779546    |  55 | True        |                                                                                   |
| Grafenrheinfeld  | <= 50      |  -0.646624 |   2.30157   |   0.778749    |  86 | True        |                                                                                   |
| Grafenrheinfeld  | <= 75      |  -0.646624 |   2.30157   |   0.778749    |  86 | True        |                                                                                   |
| Gundremmingen B  | <= 10      | nan        | nan         | nan           |   8 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Gundremmingen B  | <= 25      | nan        | nan         | nan           |   8 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Gundremmingen B  | <= 50      | nan        | nan         | nan           |   8 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Gundremmingen B  | <= 75      | nan        | nan         | nan           |   8 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Gundremmingen C  | <= 10      | nan        | nan         | nan           |   6 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Gundremmingen C  | <= 25      | nan        | nan         | nan           |   6 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Gundremmingen C  | <= 50      | nan        | nan         | nan           |   6 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| Gundremmingen C  | <= 75      | nan        | nan         | nan           |   6 | False       | 2x2 DiD cannot be estimated because one required cell contains zero observations. |

## Per-Plant Notes

### Biblis A (shutdown 2011)

2x2 cells (temperature): upstream-pre=2, upstream-post=38, downstream-pre=3, downstream-post=8.

| outcome           | model      | estimable   |   coefficient |   standard_error |      p_value |   n_obs | message   |
|:------------------|:-----------|:------------|--------------:|-----------------:|-------------:|--------:|:----------|
| water_temperature | simple_did | True        |       2.11257 |         2.44021  | 0.386635     |      51 |           |
| water_temperature | twfe_did   | True        |       3.83468 |         0.115333 | 2.12055e-242 |      51 |           |
| dissolved_oxygen  | simple_did | True        |      -1.73813 |         2.2769   | 0.44524      |      46 |           |
| dissolved_oxygen  | twfe_did   | True        |       3.8001  |         0.126672 | 9.92886e-198 |      46 |           |

Figures:
- figures/plant_level_did/biblis_a_timeseries.png
- figures/plant_level_did/biblis_a_did_2x2.png
- figures/plant_level_did/biblis_a_coverage.png

### Biblis B (shutdown 2011)

2x2 cells (temperature): upstream-pre=2, upstream-post=38, downstream-pre=0, downstream-post=0.
2x2 DiD cannot be estimated because one required cell contains zero observations.

| outcome           | model      | estimable   |   coefficient |   standard_error |   p_value |   n_obs | message                                                                           |
|:------------------|:-----------|:------------|--------------:|-----------------:|----------:|--------:|:----------------------------------------------------------------------------------|
| water_temperature | simple_did | False       |           nan |              nan |       nan |      40 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| water_temperature | twfe_did   | False       |           nan |              nan |       nan |      40 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | simple_did | False       |           nan |              nan |       nan |      35 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | twfe_did   | False       |           nan |              nan |       nan |      35 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |

Figures:
- figures/plant_level_did/biblis_b_timeseries.png
- figures/plant_level_did/biblis_b_did_2x2.png
- figures/plant_level_did/biblis_b_coverage.png

### Unterweser (shutdown 2011)

2x2 cells (temperature): upstream-pre=5, upstream-post=49, downstream-pre=0, downstream-post=0.
2x2 DiD cannot be estimated because one required cell contains zero observations.

| outcome           | model      | estimable   |   coefficient |   standard_error |   p_value |   n_obs | message                                                                           |
|:------------------|:-----------|:------------|--------------:|-----------------:|----------:|--------:|:----------------------------------------------------------------------------------|
| water_temperature | simple_did | False       |           nan |              nan |       nan |      54 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| water_temperature | twfe_did   | False       |           nan |              nan |       nan |      54 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | simple_did | False       |           nan |              nan |       nan |      42 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | twfe_did   | False       |           nan |              nan |       nan |      42 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |

Figures:
- figures/plant_level_did/unterweser_timeseries.png
- figures/plant_level_did/unterweser_did_2x2.png
- figures/plant_level_did/unterweser_coverage.png

### Isar 1 (shutdown 2011)

2x2 cells (temperature): upstream-pre=0, upstream-post=14, downstream-pre=0, downstream-post=10.
2x2 DiD cannot be estimated because one required cell contains zero observations.

| outcome           | model      | estimable   |   coefficient |   standard_error |   p_value |   n_obs | message                                                                           |
|:------------------|:-----------|:------------|--------------:|-----------------:|----------:|--------:|:----------------------------------------------------------------------------------|
| water_temperature | simple_did | False       |           nan |              nan |       nan |      24 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| water_temperature | twfe_did   | False       |           nan |              nan |       nan |      24 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | simple_did | False       |           nan |              nan |       nan |      24 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | twfe_did   | False       |           nan |              nan |       nan |      24 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |

Figures:
- figures/plant_level_did/isar_1_timeseries.png
- figures/plant_level_did/isar_1_did_2x2.png
- figures/plant_level_did/isar_1_coverage.png

### Isar 2 (shutdown 2023)

2x2 cells (temperature): upstream-pre=11, upstream-post=1, downstream-pre=0, downstream-post=0.
2x2 DiD cannot be estimated because one required cell contains zero observations.

| outcome           | model      | estimable   |   coefficient |   standard_error |   p_value |   n_obs | message                                                                           |
|:------------------|:-----------|:------------|--------------:|-----------------:|----------:|--------:|:----------------------------------------------------------------------------------|
| water_temperature | simple_did | False       |           nan |              nan |       nan |      12 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| water_temperature | twfe_did   | False       |           nan |              nan |       nan |      12 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | simple_did | False       |           nan |              nan |       nan |      12 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | twfe_did   | False       |           nan |              nan |       nan |      12 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |

Figures:
- figures/plant_level_did/isar_2_timeseries.png
- figures/plant_level_did/isar_2_did_2x2.png
- figures/plant_level_did/isar_2_coverage.png

### Neckarwestheim 1 (shutdown 2011)

2x2 cells (temperature): upstream-pre=0, upstream-post=27, downstream-pre=0, downstream-post=32.
2x2 DiD cannot be estimated because one required cell contains zero observations.

| outcome           | model      | estimable   |   coefficient |   standard_error |   p_value |   n_obs | message                                                                           |
|:------------------|:-----------|:------------|--------------:|-----------------:|----------:|--------:|:----------------------------------------------------------------------------------|
| water_temperature | simple_did | False       |           nan |              nan |       nan |      59 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| water_temperature | twfe_did   | False       |           nan |              nan |       nan |      59 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | simple_did | False       |           nan |              nan |       nan |      59 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | twfe_did   | False       |           nan |              nan |       nan |      59 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |

Figures:
- figures/plant_level_did/neckarwestheim_1_timeseries.png
- figures/plant_level_did/neckarwestheim_1_did_2x2.png
- figures/plant_level_did/neckarwestheim_1_coverage.png

### Neckarwestheim 2 (shutdown 2023)

2x2 cells (temperature): upstream-pre=19, upstream-post=4, downstream-pre=0, downstream-post=0.
2x2 DiD cannot be estimated because one required cell contains zero observations.

| outcome           | model      | estimable   |   coefficient |   standard_error |   p_value |   n_obs | message                                                                           |
|:------------------|:-----------|:------------|--------------:|-----------------:|----------:|--------:|:----------------------------------------------------------------------------------|
| water_temperature | simple_did | False       |           nan |              nan |       nan |      23 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| water_temperature | twfe_did   | False       |           nan |              nan |       nan |      23 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | simple_did | False       |           nan |              nan |       nan |      23 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | twfe_did   | False       |           nan |              nan |       nan |      23 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |

Figures:
- figures/plant_level_did/neckarwestheim_2_timeseries.png
- figures/plant_level_did/neckarwestheim_2_did_2x2.png
- figures/plant_level_did/neckarwestheim_2_coverage.png

### Philippsburg 1 (shutdown 2011)

2x2 cells (temperature): upstream-pre=0, upstream-post=10, downstream-pre=2, downstream-post=28.
2x2 DiD cannot be estimated because one required cell contains zero observations.

| outcome           | model      | estimable   |   coefficient |   standard_error |   p_value |   n_obs | message                                                                           |
|:------------------|:-----------|:------------|--------------:|-----------------:|----------:|--------:|:----------------------------------------------------------------------------------|
| water_temperature | simple_did | False       |           nan |              nan |       nan |      40 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| water_temperature | twfe_did   | False       |           nan |              nan |       nan |      40 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | simple_did | False       |           nan |              nan |       nan |      35 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | twfe_did   | False       |           nan |              nan |       nan |      35 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |

Figures:
- figures/plant_level_did/philippsburg_1_timeseries.png
- figures/plant_level_did/philippsburg_1_did_2x2.png
- figures/plant_level_did/philippsburg_1_coverage.png

### Philippsburg 2 (shutdown 2019)

2x2 cells (temperature): upstream-pre=2, upstream-post=8, downstream-pre=0, downstream-post=0.
2x2 DiD cannot be estimated because one required cell contains zero observations.

| outcome           | model      | estimable   |   coefficient |   standard_error |   p_value |   n_obs | message                                                                           |
|:------------------|:-----------|:------------|--------------:|-----------------:|----------:|--------:|:----------------------------------------------------------------------------------|
| water_temperature | simple_did | False       |           nan |              nan |       nan |      10 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| water_temperature | twfe_did   | False       |           nan |              nan |       nan |      10 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | simple_did | False       |           nan |              nan |       nan |      10 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | twfe_did   | False       |           nan |              nan |       nan |      10 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |

Figures:
- figures/plant_level_did/philippsburg_2_timeseries.png
- figures/plant_level_did/philippsburg_2_did_2x2.png
- figures/plant_level_did/philippsburg_2_coverage.png

### Grohnde (shutdown 2021)

2x2 cells (temperature): upstream-pre=1, upstream-post=2, downstream-pre=28, downstream-post=17.

| outcome           | model      | estimable   |   coefficient |   standard_error |    p_value |   n_obs | message   |
|:------------------|:-----------|:------------|--------------:|-----------------:|-----------:|--------:|:----------|
| water_temperature | simple_did | True        |     3.95341   |         1.35597  | 0.00355045 |      48 |           |
| water_temperature | twfe_did   | True        |     0.0957093 |         0.909851 | 0.916223   |      48 |           |
| dissolved_oxygen  | simple_did | True        |     2.11508   |         1.23108  | 0.085784   |      36 |           |
| dissolved_oxygen  | twfe_did   | True        |    -1.09004   |         0.48829  | 0.025591   |      36 |           |

Figures:
- figures/plant_level_did/grohnde_timeseries.png
- figures/plant_level_did/grohnde_did_2x2.png
- figures/plant_level_did/grohnde_coverage.png

### Emsland (shutdown 2023)

2x2 cells (temperature): upstream-pre=15, upstream-post=2, downstream-pre=0, downstream-post=0.
2x2 DiD cannot be estimated because one required cell contains zero observations.

| outcome           | model      | estimable   |   coefficient |   standard_error |   p_value |   n_obs | message                                                                           |
|:------------------|:-----------|:------------|--------------:|-----------------:|----------:|--------:|:----------------------------------------------------------------------------------|
| water_temperature | simple_did | False       |           nan |              nan |       nan |      17 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| water_temperature | twfe_did   | False       |           nan |              nan |       nan |      17 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | simple_did | False       |           nan |              nan |       nan |      17 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | twfe_did   | False       |           nan |              nan |       nan |      17 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |

Figures:
- figures/plant_level_did/emsland_timeseries.png
- figures/plant_level_did/emsland_did_2x2.png
- figures/plant_level_did/emsland_coverage.png

### Brokdorf (shutdown 2021)

2x2 cells (temperature): upstream-pre=4, upstream-post=3, downstream-pre=0, downstream-post=0.
2x2 DiD cannot be estimated because one required cell contains zero observations.

| outcome           | model      | estimable   |   coefficient |   standard_error |   p_value |   n_obs | message                                                                           |
|:------------------|:-----------|:------------|--------------:|-----------------:|----------:|--------:|:----------------------------------------------------------------------------------|
| water_temperature | simple_did | False       |           nan |              nan |       nan |       7 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| water_temperature | twfe_did   | False       |           nan |              nan |       nan |       7 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | simple_did | False       |           nan |              nan |       nan |       7 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | twfe_did   | False       |           nan |              nan |       nan |       7 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |

Figures:
- figures/plant_level_did/brokdorf_timeseries.png
- figures/plant_level_did/brokdorf_did_2x2.png
- figures/plant_level_did/brokdorf_coverage.png

### Grafenrheinfeld (shutdown 2015)

2x2 cells (temperature): upstream-pre=13, upstream-post=27, downstream-pre=14, downstream-post=38.

| outcome           | model      | estimable   |   coefficient |   standard_error |   p_value |   n_obs | message   |
|:------------------|:-----------|:------------|--------------:|-----------------:|----------:|--------:|:----------|
| water_temperature | simple_did | True        |      0.583542 |         2.35924  |  0.804643 |      92 |           |
| water_temperature | twfe_did   | True        |      0.242056 |         0.249091 |  0.33117  |      92 |           |
| dissolved_oxygen  | simple_did | True        |     -0.702603 |         1.31612  |  0.593449 |      91 |           |
| dissolved_oxygen  | twfe_did   | True        |      1.09721  |         0.855337 |  0.199569 |      91 |           |

Figures:
- figures/plant_level_did/grafenrheinfeld_timeseries.png
- figures/plant_level_did/grafenrheinfeld_did_2x2.png
- figures/plant_level_did/grafenrheinfeld_coverage.png

### Gundremmingen B (shutdown 2017)

2x2 cells (temperature): upstream-pre=0, upstream-post=8, downstream-pre=11, downstream-post=23.
2x2 DiD cannot be estimated because one required cell contains zero observations.

| outcome           | model      | estimable   |   coefficient |   standard_error |   p_value |   n_obs | message                                                                           |
|:------------------|:-----------|:------------|--------------:|-----------------:|----------:|--------:|:----------------------------------------------------------------------------------|
| water_temperature | simple_did | False       |           nan |              nan |       nan |      42 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| water_temperature | twfe_did   | False       |           nan |              nan |       nan |      42 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | simple_did | False       |           nan |              nan |       nan |      42 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | twfe_did   | False       |           nan |              nan |       nan |      42 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |

Figures:
- figures/plant_level_did/gundremmingen_b_timeseries.png
- figures/plant_level_did/gundremmingen_b_did_2x2.png
- figures/plant_level_did/gundremmingen_b_coverage.png

### Gundremmingen C (shutdown 2021)

2x2 cells (temperature): upstream-pre=2, upstream-post=4, downstream-pre=0, downstream-post=0.
2x2 DiD cannot be estimated because one required cell contains zero observations.

| outcome           | model      | estimable   |   coefficient |   standard_error |   p_value |   n_obs | message                                                                           |
|:------------------|:-----------|:------------|--------------:|-----------------:|----------:|--------:|:----------------------------------------------------------------------------------|
| water_temperature | simple_did | False       |           nan |              nan |       nan |       6 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| water_temperature | twfe_did   | False       |           nan |              nan |       nan |       6 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | simple_did | False       |           nan |              nan |       nan |       6 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |
| dissolved_oxygen  | twfe_did   | False       |           nan |              nan |       nan |       6 | 2x2 DiD cannot be estimated because one required cell contains zero observations. |

Figures:
- figures/plant_level_did/gundremmingen_c_timeseries.png
- figures/plant_level_did/gundremmingen_c_did_2x2.png
- figures/plant_level_did/gundremmingen_c_coverage.png
