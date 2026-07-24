# 2011 Nuclear Shutdowns Difference-in-Differences Analysis

## Overview

This analysis framework evaluates the thermal impacts of Germany's 2011 nuclear moratorium using Difference-in-Differences (DiD) methods on river water temperature data.

**Six reactors were shut down in 2011:**
- **Rhine River:** Biblis A, Biblis B, Philippsburg 1
- **Weser River:** Unterweser
- **Neckar River:** Neckarwestheim 1
- **Isar River:** Isar 1

## Key Challenge: Data Availability

A rigorous 2×2 DiD requires temperature stations with both **pre-shutdown (before 2011)** and **post-shutdown (after 2011)** observations. Unfortunately:

- Most German temperature monitoring started **after 2011**
- Few stations have the required pre/post coverage
- This limits our ability to estimate causal effects

**See `DATA_LIMITATIONS.md` for detailed analysis.**

## Analysis Approach

### 1. Primary Analysis: Standard 2×2 DiD

**Script:** `analyze_2011_shutdowns.py`

Implements strict Difference-in-Differences design:
- **Treatment:** Stations directly downstream of shutdown reactors
- **Control:** Stations directly upstream (not affected by shutdown)
- **Pre-period:** Years before 2011
- **Post-period:** Years after 2011
- **Effect:** Estimated difference-in-differences coefficient

**Requirements:**
- Upstream station: ≥1 observation before 2011, ≥1 after
- Downstream station: ≥1 observation before 2011, ≥1 after
- Same river system

**Status:** ⚠️ No station pairs meet these criteria for 2011 shutdowns

### 2. Fallback Analysis: Trend Comparison

**Script:** `2011_fallback_analysis.py`

When pre-shutdown data is unavailable, we document post-shutdown trends:

**Generates for each reactor:**
- Upstream vs downstream time series (2012 onwards)
- Linear trend slopes (per year) with standard errors
- Descriptive statistics (mean, std, year range, N observations)

**Outputs:**
- `trend_results_2011_fallback.csv`: Upstream/downstream station-level trends
- Visualizations: `*_trends_fallback.png` for each reactor

**Interpretation:** Descriptive patterns, not causal evidence

### 3. Distance Sensitivity Analysis

Both scripts implement distance-based filtering:

**Thresholds:** 5, 10, 20, 30, 50 km
- Filter observations by distance from reactor
- Assess robustness to exposure radius definition
- Useful when station pairs exist

## Running the Analysis

### Full Pipeline

```bash
# Primary 2×2 DiD analysis (strict, limited results)
python3 scripts/analyze_2011_shutdowns.py

# Supplementary trend analysis (comprehensive, descriptive)
python3 scripts/2011_fallback_analysis.py
```

### Individual Scripts

```bash
# Standalone 2×2 DiD
cd /path/to/project && python3 scripts/analyze_2011_shutdowns.py

# Standalone trend analysis
cd /path/to/project && python3 scripts/2011_fallback_analysis.py
```

## Output Files

### Primary Analysis (`analyze_2011_shutdowns.py`)

```
data/processed/analysis/2x2_2011_shutdowns/
├── did_results_2011.csv                  # 2×2 DiD results (if any pairs found)
├── station_pairs_2011.csv                # Upstream/downstream pairs identified
├── report_2011_shutdowns.md              # Summary report with tables
└── figures/2x2_2011_shutdowns/
    ├── *_timeseries.png                  # Time series plots
    └── *_did_2x2.png                     # 2×2 cell means plot
```

### Fallback Analysis (`2011_fallback_analysis.py`)

```
data/processed/analysis/2x2_2011_shutdowns/
├── trend_results_2011_fallback.csv       # Trend slopes by station
└── figures/2x2_2011_shutdowns/
    └── *_trends_fallback.png             # Upstream vs downstream trends
```

### Documentation

```
data/processed/analysis/2x2_2011_shutdowns/
├── DATA_LIMITATIONS.md                   # Detailed data constraints
└── README.md                             # This file
```

## Key Results

### Data Coverage Summary

| Reactor | River | Pre-2011 Obs? | Post-2011 Obs? | 2×2 Feasible? |
|---------|-------|---|---|---|
| Biblis A | Rhine | ✓ Limited | ✓ Good | ⚠️ Incomplete pairs |
| Biblis B | Rhine | ✓ Limited | ✓ Good | ⚠️ Incomplete pairs |
| Philippsburg 1 | Rhine | ✓ Limited | ✓ Good | ⚠️ Incomplete pairs |
| Unterweser | Weser | ✓ Limited | ✓ Good | ✗ No downstream |
| Neckarwestheim 1 | Neckar | ✗ None | ✓ Good (2012+) | ✗ No pre-data |
| Isar 1 | Isar | ✗ None | ✓ Good (2013+) | ✗ No pre-data |

### Trend Analysis Results

See `trend_results_2011_fallback.csv` for detailed results. Sample:

- **Biblis A (Rhine upstream):** +0.074°C/year trend (2009-2024)
- **Biblis A (Rhine downstream):** -0.412°C/year trend (2013-2024)
- **Unterweser:** No downstream stations available

## Methodological Notes

### Standard 2×2 DiD Specification

$$Y_{st} = \alpha + \beta_1 D_s + \beta_2 \text{Post}_t + \beta_{DiD} (D_s \times \text{Post}_t) + \epsilon_{st}$$

Where:
- $Y_{st}$ = mean water temperature at station $s$ in year $t$
- $D_s$ = 1 if downstream, 0 if upstream
- $\text{Post}_t$ = 1 if $t > 2011$, 0 otherwise
- $\beta_{DiD}$ = estimated thermal effect of shutdown
- Errors clustered at station level (if multiple stations) or HC1-robust

### Fallback Trend Specification

$$\text{Temperature}_{st} = \alpha_s + \beta_s \cdot t + \epsilon_{st}$$

- Fitted per-station to quantify long-term trends
- No causal interpretation (no control group)
- Useful for detecting shifts or divergence between upstream/downstream

## Extensibility

The framework is designed for other shutdowns with better data:

### For Earlier Shutdowns (e.g., Stade 2003)

1. Modify `SHUTDOWN_YEAR` and `get_2011_reactors()` to filter desired year
2. Adjust `DISTANCE_THRESHOLDS_KM` if needed
3. Rerun `analyze_2011_shutdowns.py` with new parameters

### For Different Outcomes

Replace `OUTCOME = "water_temperature"` with:
- `"dissolved_oxygen"`
- `"ph"`
- etc. (if available in water_quality panel)

### For Different Comparisons

Modify the treatment/control definition in `build_2x2_dataset()` to:
- Use distance rings (e.g., 0-10 km = treatment, 10-30 km = control)
- Use river sections instead of individual stations
- Implement event-study approach over time

## Interpreting Results

### When 2×2 DiD is Estimable

- **Coefficient (β_DiD):** Change in temperature (°C) in downstream minus upstream stations after shutdown vs before
- **p-value < 0.05:** Statistically significant evidence of thermal effect
- **Confidence Interval:** Range of plausible effect sizes

### When Only Trends Available

- **Trend slope:** Average temperature change per year
- **Post-2011 level:** Absolute mean temperature in recent years
- **Upstream vs downstream difference:** Whether stations diverged
- **Caution:** Descriptive only; cannot infer causation without control group

## Future Work

1. **Robust shutdowns:** Apply to Stade (2003), Mülheim-Kärlich (1998), other earlier closures with better pre/post data
2. **Event study:** Implement leads/lags around shutdown date
3. **Permutation tests:** Assess whether 2011 effects exceed placebo treatments
4. **Synthetic control:** If matching on station characteristics improves inference
5. **Other outcomes:** Dissolved oxygen, pH, discharge using same framework

## References

- **DiD Design:** Angrist & Pischke (2009), Mostly Harmless Econometrics
- **River Temperature:** Poff & Zimmerman (2010), Ecological Applications
- **Nuclear Effects:** Shrader-Frechette (2011), Science & Environmental Ethics

## Authors & Dates

Generated by: `analyze_2011_shutdowns.py` and `2011_fallback_analysis.py`  
Date: 2025  
Project: AEER (Atomic Economics and Environmental Regulation)

---

**Questions?** Check `DATA_LIMITATIONS.md` for constraints and alternative approaches.
