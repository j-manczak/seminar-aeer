# DiD: 2011 shutdown and summer water temperature

*Source: Waterbase v2025_1 individual measurements → summer (Jun-Sep) by site/year, downstream ≤ 50 km, river matched geometrically.*

## Core finding
With dense individual measurements, coverage is continuous from 2008-2024, but it is **highly uneven across groups**. The clean **Treatment** plants (Biblis, Unterweser) and **Control** reactors (Grohnde, Emsland, Brokdorf) are downstream **barely measured, especially before 2011**; coverage is concentrated in **Partial** (Philippsburg, Neckarwestheim; 9 sites) and **Staggered** (Grafenrheinfeld 2015, Gundremmingen 2017; 5 sites). A strict treatment-vs-control DiD for 2011 is therefore **not identified** (the control group has no pre-2011 observations). The better-covered experiment is the **partial and staggered shutdowns**.

## Data coverage (sites by group × year)

| Group | 2008 | 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Treatment | 1 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 2 | 2 |
| Partial | 0 | 1 | 1 | 1 | 2 | 2 | 1 | 3 | 2 | 2 | 3 | 3 | 7 | 8 | 9 | 6 | 5 |
| Staggered | 2 | 2 | 0 | 0 | 3 | 4 | 3 | 4 | 3 | 3 | 3 | 4 | 4 | 4 | 4 | 4 | 3 |
| Control | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1 | 1 | 2 | 3 | 4 | 4 | 3 | 3 |

Figure: `figures/did_coverage.png` (red line = 2011).

## Attempt: Treatment vs. Control (2×2, window 2008-2020)

Cell counts (observations):

| | pre-2011 | from 2011 |
|---|---|---|
| Control | 0 | 9 |
| Treatment | 3 | 3 |

**Not estimable:** at least one cell is empty (no control pre-period). The 2×2 DiD is not defined for this site set.

## Recommendation (which DiD designs the data support)
1. **Staggered / generalized DiD** across all shutdowns: each downstream site is treated from the shutdown year of its nearest upstream reactor (2011 partial/treatment, 2015 Grafenrheinfeld, 2017 Gundremmingen); still-running reactors are the not-yet-treated controls. This uses full coverage (Callaway-Sant'Anna to avoid TWFE bias).
2. **Within-river downstream vs. upstream** for each shutdown (upstream as control on the same river).
3. Include discharge as covariate/intensity; keep the summer focus (already done here).

## Caveats
- Small but growing sample; site + year FE; few clusters → SEs are only approximate.
- Watch tidal locations (Unterweser, Brokdorf) and composition changes.

Figures: `figures/did_coverage.png`, `figures/did_trends.png`.