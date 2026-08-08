# Figure Insertion Guide for AEER.docx

## Strategy: 4-5 Key Figures in Text + Full Set in Appendix

### **Figures to Embed in Text (Main Document)**

After each subsection in Section 6, insert the following key figures:

#### **After 6.1 (Summer Water Temperature)**

**Figure 1A: Isar 1 Time Series**
- File: `final_results/figures/obs01_Isar_1_temperature_timeseries.png`
- Position: Right after the Isar 1 interpretation paragraph
- Caption: "Figure 1A: Daily Water Temperature – Isar 1 (Isar River). Solid line = downstream station; dashed = upstream control. Vertical dashed line indicates shutdown date (6 August 2011). Downstream temperatures drop sharply after shutdown."
- Purpose: Visually demonstrates the main finding

**Figure 1B: All Plants DiD Comparison**
- File: `final_results/figures/did_temperature_all_obs.png`
- Position: After Table 1 and key results paragraph
- Caption: "Figure 1B: Difference-in-Differences Coefficients for Water Temperature (5-Year Window). Error bars show 95% confidence intervals. Only Isar 1 (obs=1) is significant at p<0.001. Solid bars indicate 2011 shutdowns; striped bars indicate 2023 shutdowns."
- Purpose: Shows heterogeneity across plants at a glance

#### **After 6.2 (Sensitivity Analysis)**

**Figure 2: Isar 1 Sensitivity Across Event Windows**
- File: `final_results/figures/obs01_Isar_1_sensitivity_temperature.png`
- Position: After sensitivity analysis paragraph
- Caption: "Figure 2: Isar 1 Robustness to Event Window Length (3–7 Years). DiD coefficients remain large and significant across all specifications (all p<0.001). Effect ranges from −1.77°C to −2.14°C."
- Purpose: Demonstrates robustness

#### **After 6.3 (Dissolved Oxygen)**

**Figure 3: Parallel Trends – Isar 1**
- File: `final_results/figures/obs01_Isar_1_temperature_parallel_trends.png`
- Position: As appendix reference with note: "See Appendix Figure A1"
- Alternative: Embed one parallel trends figure to validate DiD assumption
- Caption: "Figure 3: Parallel Trends Test – Isar 1 (Pre-Shutdown Period). Pre-shutdown daily differences between upstream and downstream stations show no trend divergence, supporting the parallel trends assumption."
- Purpose: Validates key DiD identifying assumption

**Optional 5th Figure: Cross-Observation Oxygen Summary**
- File: `final_results/figures/did_oxygen_all_obs.png`
- Position: After Table 3 (Oxygen results)
- Caption: "Figure 4: Difference-in-Differences Coefficients for Dissolved Oxygen (5-Year Window). None of the oxygen estimates are statistically significant."
- Purpose: Shows null oxygen results visually

---

## **Figures for Appendix (Complete Set)**

Create a new appendix section with subsections for each observation:

### **Appendix A: Observation-Level Detailed Results**

**Appendix A.1: Isar 1 (2011)**
- `obs01_Isar_1_temperature_timeseries.png`
- `obs01_Isar_1_temperature_parallel_trends.png`
- `obs01_Isar_1_sensitivity_temperature.png`

**Appendix A.2: Neckarwestheim 1 (2011)**
- `obs02_Neckarwestheim_1_temperature_timeseries.png`
- `obs02_Neckarwestheim_1_temperature_parallel_trends.png`
- `obs02_Neckarwestheim_1_oxygen_timeseries.png`
- `obs02_Neckarwestheim_1_oxygen_parallel_trends.png`
- `obs02_Neckarwestheim_1_sensitivity_temperature.png`
- `obs02_Neckarwestheim_1_sensitivity_oxygen.png`

**Appendix A.3: Philippsburg 1 (2011)**
- `obs03_Philippsburg_1_temperature_timeseries.png`
- `obs03_Philippsburg_1_temperature_parallel_trends.png`
- `obs03_Philippsburg_1_oxygen_timeseries.png`
- `obs03_Philippsburg_1_oxygen_parallel_trends.png`
- `obs03_Philippsburg_1_sensitivity_temperature.png`
- `obs03_Philippsburg_1_sensitivity_oxygen.png`

**Appendix A.4: Gundremmingen B (2011)**
- `obs04_Gundremmingen_B_temperature_timeseries.png`
- `obs04_Gundremmingen_B_temperature_parallel_trends.png`
- `obs04_Gundremmingen_B_sensitivity_temperature.png`

**Appendix A.5: Philippsburg 2 (2015)**
- `obs05_Philippsburg_2_temperature_timeseries.png`
- `obs05_Philippsburg_2_temperature_parallel_trends.png`
- `obs05_Philippsburg_2_oxygen_timeseries.png`
- `obs05_Philippsburg_2_oxygen_parallel_trends.png`
- `obs05_Philippsburg_2_sensitivity_temperature.png`
- `obs05_Philippsburg_2_sensitivity_oxygen.png`

**Appendix A.6: Gundremmingen C (2019)**
- `obs06_Gundremmingen_C_temperature_timeseries.png`
- `obs06_Gundremmingen_C_temperature_parallel_trends.png`
- `obs06_Gundremmingen_C_sensitivity_temperature.png`

**Appendix A.7: Isar 2 (2023)**
- `obs07_Isar_2_temperature_timeseries.png`
- `obs07_Isar_2_temperature_parallel_trends.png`
- `obs07_Isar_2_sensitivity_temperature.png`

**Appendix A.8: Neckarwestheim 2 (2023)**
- `obs08_Neckarwestheim_2_temperature_timeseries.png`
- `obs08_Neckarwestheim_2_temperature_parallel_trends.png`
- `obs08_Neckarwestheim_2_oxygen_timeseries.png`
- `obs08_Neckarwestheim_2_oxygen_parallel_trends.png`
- `obs08_Neckarwestheim_2_sensitivity_temperature.png`
- `obs08_Neckarwestheim_2_sensitivity_oxygen.png`

**Appendix A.9: Cross-Observation Summaries**
- `did_temperature_all_obs.png` (already mentioned in text)
- `did_oxygen_all_obs.png` (already mentioned in text)

---

## **Implementation Notes**

### **For Figures in Text:**
1. Insert as **Inline with Text** or **In Line with Text** to avoid layout breaks
2. Set width to ~4.5–5 inches for single-column documents
3. Add captions using Word's Caption feature (Insert > Caption) for cross-referencing
4. Number as **Figure 1A, 1B, 2, 3, 4** corresponding to sections

### **For Appendix:**
1. Create new section: **"APPENDIX A: Detailed Results Figures"**
2. Organize by observation (A.1, A.2, etc.)
3. All observations on equal footing (even null results)
4. Include brief captions describing what each figure shows

### **Figure Density:**
- **Text**: 4–5 figures (≈2 KB PDF equivalent)
- **Appendix**: 38 additional figures (full set)
- Total: ~8–10 MB in the .docx file (manageable)

---

## **Recommended Manual Steps**

Since python-docx doesn't embed images cleanly, you'll need to:

1. Open AEER.docx in Microsoft Word
2. Position cursor after each section
3. Use **Insert > Pictures** to add figures from `final_results/figures/`
4. Use **Insert > Caption** to add numbered captions
5. Cross-reference in text (e.g., "See Figure 1A")

**Or** send the .docx + figures folder to whoever is writing Sections 1–3 and 7–8 for final assembly.

---

## **Master's Seminar Paper Convention**

For a seminar paper (vs. research paper):
- ✓ 4–5 key figures in main text shows rigor without overwhelming
- ✓ Full appendix shows thoroughness
- ✓ Keep tables in text (readers expect tabular results in seminar papers)
- ✓ Figures in text should advance the narrative, not just illustrate

