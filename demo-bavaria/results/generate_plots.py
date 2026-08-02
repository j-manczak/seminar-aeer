"""
Generate visualization plots from DiD analysis results
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Load results
results_df = pd.read_csv("DiD_summary.csv")

# Shorten case names for better readability
results_df['case_short'] = results_df['case'].str.replace(r' \(.*\) - Shutdown.*', '', regex=True)

# Create Figure 1: DiD Estimates Comparison
fig, ax = plt.subplots(figsize=(12, 7))

colors = ['#d62728' if x < 0 else '#2ca02c' for x in results_df['did_estimate']]
bars = ax.bar(range(len(results_df)), results_df['did_estimate'], color=colors, edgecolor='black', linewidth=1.5)

# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars, results_df['did_estimate'])):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + (0.05 if height > 0 else -0.15),
            f'{val:.3f}°C', ha='center', va='bottom' if height > 0 else 'top', fontsize=11, fontweight='bold')

ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
ax.set_ylabel('DiD Estimate (°C)', fontsize=12, fontweight='bold')
ax.set_xlabel('Nuclear Power Plant Shutdown', fontsize=12, fontweight='bold')
ax.set_title('Difference-in-Differences Temperature Effects\nNuclear Power Plant Shutdowns in Bavaria', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(range(len(results_df)))
ax.set_xticklabels(results_df['case_short'], rotation=45, ha='right')
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_ylim(min(results_df['did_estimate']) - 0.3, max(results_df['did_estimate']) + 0.3)

plt.tight_layout()
plt.savefig('did_estimates_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Saved: did_estimates_comparison.png")
plt.close()

# Create Figure 2: Decomposition Analysis
fig, ax = plt.subplots(figsize=(14, 8))

x = np.arange(len(results_df))
width = 0.2

bars1 = ax.bar(x - 1.5*width, results_df['upstream_diff'], width, label='Upstream (Control)', 
               color='#1f77b4', edgecolor='black', linewidth=1)
bars2 = ax.bar(x - 0.5*width, results_df['downstream_diff'], width, label='Downstream (Treatment)', 
               color='#ff7f0e', edgecolor='black', linewidth=1)
bars3 = ax.bar(x + 0.5*width, results_df['did_estimate'], width, label='DiD Estimate', 
               color='#2ca02c', edgecolor='black', linewidth=1)

# Add value labels
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + (0.1 if height > 0 else -0.2),
                f'{height:.2f}', ha='center', va='bottom' if height > 0 else 'top', 
                fontsize=9, fontweight='bold')

ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
ax.set_ylabel('Temperature Change (°C)', fontsize=12, fontweight='bold')
ax.set_xlabel('Nuclear Power Plant Shutdown', fontsize=12, fontweight='bold')
ax.set_title('DiD Decomposition Analysis\nTemperature Changes by Station Group', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(results_df['case_short'], rotation=45, ha='right')
ax.legend(loc='upper left', fontsize=11, framealpha=0.95)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_ylim(min(results_df[['upstream_diff', 'downstream_diff', 'did_estimate']].min()) - 1, 
            max(results_df[['upstream_diff', 'downstream_diff', 'did_estimate']].max()) + 1)

plt.tight_layout()
plt.savefig('did_decomposition_analysis.png', dpi=300, bbox_inches='tight')
print("✓ Saved: did_decomposition_analysis.png")
plt.close()

print("\n✅ All plots generated successfully!")
print("\nFiles created:")
print("  1. did_estimates_comparison.png")
print("  2. did_decomposition_analysis.png")
