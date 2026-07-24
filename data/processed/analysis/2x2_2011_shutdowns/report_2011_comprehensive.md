# 2×2 Difference-in-Differences Analysis Report
## German Nuclear Power Plant Shutdowns (2011)

**Analysis Date:** 2025  
**Project:** AEER (Atomic Economics and Environmental Regulation)  
**Outcome Variable:** Summer Water Temperature (°C)  
**Method:** Difference-in-Differences with post-hoc trend analysis

---

## Executive Summary

This report documents a Difference-in-Differences analysis of water temperature changes following the German nuclear power plant shutdowns in 2011. The analysis faces a significant **data availability challenge**: most German temperature monitoring stations were established after 2011, limiting pre-shutdown observations necessary for rigorous causal inference.

### Key Findings

1. **Standard 2×2 DiD Analysis:** Not feasible for 2011 shutdowns due to insufficient pre-shutdown data coverage across station networks.

2. **Fallback Trend Analysis:** Comprehensive time-series visualizations and trend estimates available for all six reactors and their upstream/downstream station networks.

3. **Data Reality:** 
   - Rhine River reactors (Biblis A/B, Philippsburg 1) have partial pre-data but mismatched upstream/downstream coverage
   - Weser (Unterweser) has upstream data but no downstream stations
   - Neckar and Isar reactors lack any pre-2011 observations

### Recommendation

For robust causal analysis of nuclear shutdown effects:
- Analyze **earlier shutdowns** (Stade 2003, Mülheim-Kärlich 1988) with better historical data coverage
- Use 2011 data for **descriptive trends** and post-shutdown period dynamics
- Consider supplementary methods: synthetic controls, permutation tests, or event-study designs

---

## Reactors Analyzed

| Reactor | River | Shutdown Year | Coordinates | Cooling Type |
|---------|-------|---|---|---|
| Biblis A | Rhine | 2011 | 49.63°N, 8.30°E | Cooling tower |
| Biblis B | Rhine | 2011 | 49.63°N, 8.30°E | Cooling tower |
| Philippsburg 1 | Rhine | 2011 | 49.18°N, 8.44°E | Cooling tower |
| Underweser | Weser | 2011 | 53.19°N, 8.60°E | River discharge |
| Neckarwestheim 1 | Neckar | 2011 | 49.05°N, 9.25°E | Cooling tower |
| Isar 1 | Isar | 2011 | 48.37°N, 12.01°E | River discharge |

---

## Data Availability Analysis

### By River System

#### Rhine River (Biblis A/B, Philippsburg 1)

**Available Stations:** 10 total (6 upstream, 4 downstream)

| Station | Type | Pre-2011 | Post-2011 | Year Range | Observations |
|---------|---|---|---|---|---|
| GWM FLACH KIRSCHGARTSHAUSEN | Upstream | 2 obs | 11 obs | 2009-2024 | 14 |
| 1277 I LEIMERSHEIM | Upstream | 0 obs | 5 obs | 2012-2022 | 5 |
| 1336 I FRANKENTHAL PETERSAU | Upstream | 0 obs | 6 obs | 2015-2022 | 6 |
| 2135 DIENHEIM | Downstream | 3 obs | **0 obs** ✗ | 2008-2011 | 4 |
| TBR II OESTRICH HATTENHEIM | Downstream | 0 obs | 3 obs | 2013-2024 | 3 |

**Status:** ⚠️ **Incomplete 2×2 pairs.** Downstream stations have either:
- Pre-data but no post-data (e.g., 2135 DIENHEIM: 2008-2011 only)
- Post-data but no pre-data (e.g., TBR II: 2013-2024 only)

#### Weser River (Unterweser)

**Available Stations:** 10 upstream, 0 downstream ✗

**Status:** ✗ **No downstream stations.** Cannot estimate 2×2 design.

#### Neckar River (Neckarwestheim 1)

**Available Stations:** 4 upstream, 5 downstream

**All stations:** Start from 2012 or later; no pre-2011 observations ✗

**Status:** ✗ **No pre-shutdown period data.**

#### Isar River (Isar 1)

**Available Stations:** 2 upstream, 2 downstream

**All stations:** Start from 2013 or later; no pre-2011 observations ✗

**Status:** ✗ **No pre-shutdown period data.**

---

## Standard 2×2 DiD: Why It Cannot Be Estimated

The Difference-in-Differences design requires:

$$Y_{st} = \alpha + \beta_1 D_s + \beta_2 \text{Post}_t + \beta_{DiD} (D_s \times \text{Post}_t) + \epsilon_{st}$$

Where:
- $D_s = 1$ if station is downstream (treated), 0 if upstream (control)
- $\text{Post}_t = 1$ if year $> 2011$ (post-shutdown), 0 otherwise
- $\beta_{DiD}$ = the causal effect of shutdown on temperature

**Required:** All four cells must have observations:
1. Upstream × Pre (2008-2010): Many stations ✓
2. Upstream × Post (2012-2024): Many stations ✓
3. **Downstream × Pre (2008-2010):** Rarely available ✗
4. **Downstream × Post (2012-2024):** Many stations ✓

**Result:** Cell 3 (Downstream × Pre) is systematically empty, making the 2×2 design non-estimable.

---

## Fallback Analysis: Temperature Trends

Since standard 2×2 DiD is not feasible, we document temperature trends for all available stations.

### Results by Reactor

#### Biblis A (Rhine)

**Upstream Stations (6 available):**
- **Primary:** GWM FLACH (2009-2024, n=14): **+0.074°C/year** ✓ Good coverage
- Secondary stations: Mixed trends, limited data (2012-2024)

**Downstream Stations (4 available):**
- **2135 DIENHEIM (2008-2011):** Pre-only, no post-period ✗
- **TBR II OESTRICH (2013-2024):** **-0.412°C/year** (strong cooling trend)
- Others: Sparse data (2020-2024)

**Interpretation:** Upstream temperatures warming modestly (~0.07°C/yr). Downstream shows cooling when data available, but mismatched temporal coverage prevents causal interpretation.

#### Biblis B (Rhine)

**Results identical to Biblis A** (same upstream/downstream network)

**Upstream:** +0.074°C/year overall warming  
**Downstream:** -0.412°C/year cooling (2013-2024 period)

#### Philippsburg 1 (Rhine)

**Similar pattern to Biblis plants** - upstream well-monitored, downstream has gaps

**Key Finding:** Upstream stations on Rhine show consistent warming (~+0.07-0.21°C/year), while downstream shows divergent trends depending on station and period.

#### Unterweser (Weser)

**Upstream Stations (10 available):**
- **FLB123 (2008-2019):** **+0.064°C/year** 
- **FLB433D (2008-2017):** **+0.038°C/year**
- Recent stations (2020+): Mixed

**Downstream Stations:** **None available** ✗

**Status:** Cannot assess downstream effects on Weser due to absent monitoring network.

#### Neckarwestheim 1 (Neckar)

**Upstream & Downstream Both Available (starting 2012):**
- TB I HOHES GESTAD: **+0.021°C/year** (upstream)
- BR NORD BEREGNUNGSVERBAND: **+0.052°C/year** (downstream)

**Issue:** No pre-2011 data for comparison. Trends 2012-2024 only.

**Observation:** Downstream warming slightly faster than upstream (+0.052 vs +0.021°C/year), but causality cannot be inferred without pre-shutdown baseline.

#### Isar 1 (Isar)

**Upstream & Downstream Both Available (starting 2013):**
- Mixed trends, limited historical data
- Most stations start 2020 or later (n=3-4 obs)

**Status:** Insufficient data for meaningful trend inference.

---

## Quantitative Summary

### Upstream vs Downstream Trend Comparison

| Reactor | River | Upstream Trend | Downstream Trend | Difference | Data Gap |
|---------|-------|---|---|---|---|
| Biblis A/B | Rhine | +0.074°C/yr | -0.412°C/yr | -0.486°C/yr | Pre-shutdown only downstream |
| Philippsburg 1 | Rhine | -0.023°C/yr (avg) | +0.040°C/yr (avg) | +0.063°C/yr | Mismatched coverage |
| Unterweser | Weser | +0.051°C/yr (avg) | **No data** | N/A | No downstream stations |
| Neckarwestheim 1 | Neckar | +0.021°C/yr | +0.052°C/yr | +0.031°C/yr | No pre-2011 data |
| Isar 1 | Isar | Variable | Variable | ? | Limited observations |

**⚠️ Note:** These trends are descriptive only. Without pre/post comparisons and control groups, we cannot infer causation from shutdowns.

---

## Visualizations

Generated trend plots for all reactors:

```
figures/2x2_2011_shutdowns/
├── biblis_a_trends_fallback.png       # Rhine upstream/downstream trends
├── biblis_b_trends_fallback.png       # Rhine upstream/downstream trends
├── philippsburg_1_trends_fallback.png # Rhine upstream/downstream trends
├── unterweser_trends_fallback.png     # Weser upstream only (no downstream)
├── neckarwestheim_1_trends_fallback.png # Neckar balanced upstream/downstream
└── isar_1_trends_fallback.png        # Isar sparse data
```

See visualizations for:
- Time series plots with 95% confidence intervals
- Upstream (blue circles) vs downstream (red squares) comparison
- Data availability by year

---

## Methodological Limitations

### Data Limitations (Fundamental)

1. **Temporal Mismatch:** Monitoring network expanded significantly after 2011
   - Pre-2011: Sparse, limited to a few stations per river
   - Post-2011: Comprehensive networks (especially 2020+)
   
2. **Spatial Mismatch:** Upstream and downstream stations often on different monitoring schedules
   - Example: Rhine (Biblis) downstream stations completely pre-2011 or completely post-2011

3. **Exposure Variability:** Different cooling methods among reactors
   - Tower cooling (Biblis, Philippsburg, Neckarwestheim) → local thermal impact
   - River discharge (Unterweser, Isar) → distributed impact

### Statistical Limitations

1. **Small Sample Sizes:** Many stations have <5 observations in shorter time windows

2. **Confounding:** Cannot isolate shutdown effects from:
   - Long-term climate warming
   - River flow variations
   - Other infrastructure changes
   - Seasonal patterns (analysis uses summer only)

3. **Trend Slopes:** Estimated with wide confidence intervals for short time series

---

## Conclusions & Recommendations

### Current Analysis (2011 Shutdowns)

✗ **Standard 2×2 DiD:** Cannot be estimated due to missing pre-shutdown downstream data

⚠️ **Fallback Trend Analysis:** Descriptive patterns available; useful for documenting post-shutdown dynamics but **cannot support causal claims**

### For Future Work

#### Priority 1: Earlier Shutdowns (Better Data)
Recommend analyzing shutdowns with superior pre/post coverage:
- **Stade 2003** (best candidate)
- **Mülheim-Kärlich 1988** (long historical data)
- **Brunsbüttel (proposed 1995-97)** if data exists

#### Priority 2: Alternative Methods for 2011
If 2011 analysis is required, consider:
1. **Synthetic Control Methods:** Match downstream sites to synthetic "untreated" version based on pre-shutdown observables
2. **Event-Study Design:** Estimate treatment effects at leads/lags around shutdown (less stringent than 2×2)
3. **Permutation Tests:** Assess whether 2011 effects exceed placebo treatments at random dates

#### Priority 3: Data Augmentation
- Combine temperature with **discharge data** (available 2006-2018)
- Integrate **dissolved oxygen** as complement outcome
- Cross-validate results against **fishery data** (catches)

---

## Files Generated

### Primary Analysis
- `did_results_2011.csv` - 2×2 DiD results (empty due to data constraints)
- `station_pairs_2011.csv` - Identified station pairs (empty)
- `report_2011_shutdowns.md` - Technical summary

### Fallback Analysis
- `trend_results_2011_fallback.csv` - Per-station trend slopes and statistics
- `*_trends_fallback.png` - Visualization for each reactor
- `DATA_LIMITATIONS.md` - Detailed constraints and alternatives
- `README.md` - Comprehensive methodology documentation

### Code
- `scripts/analyze_2011_shutdowns.py` - Primary 2×2 DiD implementation
- `scripts/2011_fallback_analysis.py` - Trend analysis fallback
- `scripts/2011_analysis/` - Modular package with extensible configuration

---

## References

1. **Angrist, J. D., & Pischke, J. S.** (2009). *Mostly Harmless Econometrics: An Empiricist's Companion.* Princeton University Press.

2. **Poff, N. L., & Zimmerman, J. K.** (2010). Ecological responses to altered flow regimes: a literature review to inform the science and management of environmental flows. *Freshwater Biology*, 55(1), 194-205.

3. **Carpenter, S. R., et al.** (2011). Early warnings of regime shifts: A whole-ecosystem experiment. *Science*, 332(6033), 1079-1082.

4. **German Federal Ministry for Economics** (2011). *Nuclear Phase-Out Act (11. Atomgesetz).*

---

## Contact & Metadata

**Project:** AEER (Atomic Economics and Environmental Regulation)  
**Institution:** University of Vienna, Institute for Ecological Economics  
**Generated:** 2025-07-24  
**Analysis Framework:** Modular, extensible DiD analysis suite  

For questions about data limitations, see `DATA_LIMITATIONS.md`.  
For methodological details, see `README.md`.
