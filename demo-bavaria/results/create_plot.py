"""
Create visualizations of the DiD analysis results for all four nuclear plant cases.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import matplotlib.dates as mdates

# Define data paths
data_dir = Path("../data")

def load_station_data(filename):
    """Load temperature data from a GKD CSV file."""
    filepath = data_dir / filename
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        data_start = 0
        for i, line in enumerate(lines):
            if "Tageswerte Wassertemperatur" in line:
                data_start = i + 1
                break
        
        df = pd.read_csv(
            filepath,
            skiprows=data_start,
            sep=';',
            decimal=',',
            parse_dates=['Datum'],
            date_format='%Y-%m-%d'
        )
        
        df = df[['Datum', 'Mittelwert']].rename(columns={'Mittelwert': 'temp'})
        df = df.sort_values('Datum')
        
        return df
    except FileNotFoundError:
        print(f"Warning: File {filename} not found")
        return pd.DataFrame()

# ============================================================================
# Plot 1: Isar 1 (2011 shutdown)
# ============================================================================
print("Creating Isar 1 plot...")
isar_upstream = load_station_data("landshut-birket-2010.csv")
isar_downstream = load_station_data("landau-2010.csv")

merged = isar_upstream.merge(
    isar_downstream,
    on='Datum',
    suffixes=('_upstream', '_downstream')
)

fig, axes = plt.subplots(2, 1, figsize=(12, 8))

ax1 = axes[0]
ax1.plot(merged['Datum'], merged['temp_upstream'], 'b-', alpha=0.6, label='Upstream (Landshut-Birket)', linewidth=1)
ax1.plot(merged['Datum'], merged['temp_downstream'], 'r-', alpha=0.6, label='Downstream (Landau)', linewidth=1)

shutdown_date = pd.Timestamp('2011-01-01')
ax1.axvline(shutdown_date, color='black', linestyle='--', linewidth=2, label='Isar 1 Shutdown (2011)')
ax1.axvspan(merged['Datum'].min(), shutdown_date, alpha=0.1, color='green', label='Pre-period')
ax1.axvspan(shutdown_date, merged['Datum'].max(), alpha=0.1, color='red', label='Post-period')

ax1.set_xlabel('Date', fontsize=11)
ax1.set_ylabel('Water Temperature (°C)', fontsize=11)
ax1.set_title('Isar River (Isar 1): Daily Water Temperature (2010-2012)', fontsize=12, fontweight='bold')
ax1.legend(loc='best')
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

ax2 = axes[1]
merged['year'] = merged['Datum'].dt.year
merged['period'] = merged['year'].apply(lambda y: 'Pre-2011' if y < 2011 else 'Post-2011')

periods = ['Pre-2011', 'Post-2011']
upstream_means = [merged[merged['period'] == p]['temp_upstream'].mean() for p in periods]
downstream_means = [merged[merged['period'] == p]['temp_downstream'].mean() for p in periods]

x_pos = np.arange(len(periods))
width = 0.35

bars1 = ax2.bar(x_pos - width/2, upstream_means, width, label='Upstream (Control)', color='skyblue', alpha=0.8)
bars2 = ax2.bar(x_pos + width/2, downstream_means, width, label='Downstream (Treatment)', color='salmon', alpha=0.8)

for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height, f'{height:.2f}°C',
                ha='center', va='bottom', fontsize=10)

ax2.set_ylabel('Average Water Temperature (°C)', fontsize=11)
ax2.set_title('Isar River (Isar 1): DiD Decomposition\nDiD = -1.27°C', fontsize=12, fontweight='bold')
ax2.set_xticks(x_pos)
ax2.set_xticklabels(periods)
ax2.legend(loc='best')
ax2.grid(True, alpha=0.3, axis='y')
ax2.set_ylim(10, 13)

plt.tight_layout()
plt.savefig('isar_did_analysis.png', dpi=150, bbox_inches='tight')
print("✓ Saved: isar_did_analysis.png")
plt.close()

# ============================================================================
# Plot 2: Gundremmingen C (2021 shutdown)
# ============================================================================
print("Creating Gundremmingen C plot...")
donau_upstream = load_station_data("nue-ulm-2020.csv")
donau_downstream = load_station_data("donauworth-2020.csv")

merged_donau = donau_upstream.merge(
    donau_downstream,
    on='Datum',
    suffixes=('_upstream', '_downstream')
)

fig, axes = plt.subplots(2, 1, figsize=(12, 8))

ax1 = axes[0]
ax1.plot(merged_donau['Datum'], merged_donau['temp_upstream'], 'b-', alpha=0.6, label='Upstream (Neu-Ulm)', linewidth=1)
ax1.plot(merged_donau['Datum'], merged_donau['temp_downstream'], 'r-', alpha=0.6, label='Downstream (Donauwörth)', linewidth=1)

shutdown_date = pd.Timestamp('2021-12-31')
ax1.axvline(shutdown_date, color='black', linestyle='--', linewidth=2, label='Gundremmingen C Shutdown (Dec 31, 2021)')
ax1.axvspan(merged_donau['Datum'].min(), shutdown_date, alpha=0.1, color='green', label='Pre-period')
ax1.axvspan(shutdown_date, merged_donau['Datum'].max(), alpha=0.1, color='red', label='Post-period')

ax1.set_xlabel('Date', fontsize=11)
ax1.set_ylabel('Water Temperature (°C)', fontsize=11)
ax1.set_title('Donau River (Gundremmingen C): Daily Water Temperature (2020-2022)', fontsize=12, fontweight='bold')
ax1.legend(loc='best')
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

ax2 = axes[1]
merged_donau['year'] = merged_donau['Datum'].dt.year
merged_donau['period'] = merged_donau['year'].apply(lambda y: 'Pre-2021' if y < 2021 else 'Post-2021')

periods = ['Pre-2021', 'Post-2021']
upstream_means = [merged_donau[merged_donau['period'] == p]['temp_upstream'].mean() for p in periods]
downstream_means = [merged_donau[merged_donau['period'] == p]['temp_downstream'].mean() for p in periods]

x_pos = np.arange(len(periods))
width = 0.35

bars1 = ax2.bar(x_pos - width/2, upstream_means, width, label='Upstream (Control)', color='skyblue', alpha=0.8)
bars2 = ax2.bar(x_pos + width/2, downstream_means, width, label='Downstream (Treatment)', color='salmon', alpha=0.8)

for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height, f'{height:.2f}°C',
                ha='center', va='bottom', fontsize=10)

ax2.set_ylabel('Average Water Temperature (°C)', fontsize=11)
ax2.set_title('Donau River (Gundremmingen C): DiD Decomposition\nDiD = +0.10°C', fontsize=12, fontweight='bold')
ax2.set_xticks(x_pos)
ax2.set_xticklabels(periods)
ax2.legend(loc='best')
ax2.grid(True, alpha=0.3, axis='y')
ax2.set_ylim(10, 12.5)

plt.tight_layout()
plt.savefig('gundremmingen_did_analysis.png', dpi=150, bbox_inches='tight')
print("✓ Saved: gundremmingen_did_analysis.png")
plt.close()

# ============================================================================
# Plot 3: Gundremmingen B (2017 shutdown)
# ============================================================================
print("Creating Gundremmingen B plot...")
donau_upstream_b_2016 = load_station_data("neu-ulm-2016.csv")
donau_upstream_b_2020 = load_station_data("nue-ulm-2020.csv")
donau_upstream_b_combined = pd.concat([donau_upstream_b_2016, donau_upstream_b_2020], ignore_index=True).sort_values('Datum')

donau_downstream_b_2016 = load_station_data("Donauworth-2016.csv")
donau_downstream_b_2020 = load_station_data("donauworth-2020.csv")
donau_downstream_b_combined = pd.concat([donau_downstream_b_2016, donau_downstream_b_2020], ignore_index=True).sort_values('Datum')

merged_donau_b = donau_upstream_b_combined.merge(
    donau_downstream_b_combined,
    on='Datum',
    suffixes=('_upstream', '_downstream')
)

fig, axes = plt.subplots(2, 1, figsize=(12, 8))

ax1 = axes[0]
ax1.plot(merged_donau_b['Datum'], merged_donau_b['temp_upstream'], 'b-', alpha=0.6, label='Upstream (Neu-Ulm)', linewidth=1)
ax1.plot(merged_donau_b['Datum'], merged_donau_b['temp_downstream'], 'r-', alpha=0.6, label='Downstream (Donauwörth)', linewidth=1)

shutdown_date_b = pd.Timestamp('2017-12-31')
ax1.axvline(shutdown_date_b, color='black', linestyle='--', linewidth=2, label='Gundremmingen B Shutdown (Dec 31, 2017)')
ax1.axvspan(merged_donau_b['Datum'].min(), shutdown_date_b, alpha=0.1, color='green', label='Pre-period (2016)')
ax1.axvspan(shutdown_date_b, merged_donau_b['Datum'].max(), alpha=0.1, color='red', label='Post-period (2020)')

ax1.set_xlabel('Date', fontsize=11)
ax1.set_ylabel('Water Temperature (°C)', fontsize=11)
ax1.set_title('Donau River (Gundremmingen B): Daily Water Temperature (2016 + 2020)', fontsize=12, fontweight='bold')
ax1.legend(loc='best')
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=12))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

ax2 = axes[1]
merged_donau_b['year'] = merged_donau_b['Datum'].dt.year
merged_donau_b['period'] = merged_donau_b['year'].apply(lambda y: 'Pre-2017' if y < 2017 else 'Post-2017')

periods = ['Pre-2017', 'Post-2017']
upstream_means = [merged_donau_b[merged_donau_b['period'] == p]['temp_upstream'].mean() for p in periods]
downstream_means = [merged_donau_b[merged_donau_b['period'] == p]['temp_downstream'].mean() for p in periods]

upstream_diff = upstream_means[1] - upstream_means[0]
downstream_diff = downstream_means[1] - downstream_means[0]
did_estimate = downstream_diff - upstream_diff

x_pos = np.arange(len(periods))
width = 0.35

bars1 = ax2.bar(x_pos - width/2, upstream_means, width, label='Upstream (Control)', color='skyblue', alpha=0.8)
bars2 = ax2.bar(x_pos + width/2, downstream_means, width, label='Downstream (Treatment)', color='salmon', alpha=0.8)

for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height, f'{height:.2f}°C',
                ha='center', va='bottom', fontsize=10)

ax2.set_ylabel('Average Water Temperature (°C)', fontsize=11)
ax2.set_title(f'Donau River (Gundremmingen B): DiD Decomposition\nDiD = {did_estimate:.2f}°C', fontsize=12, fontweight='bold')
ax2.set_xticks(x_pos)
ax2.set_xticklabels(periods)
ax2.legend(loc='best')
ax2.grid(True, alpha=0.3, axis='y')
ax2.set_ylim(9, 13)

plt.tight_layout()
plt.savefig('gundremmingen_b_did_analysis.png', dpi=150, bbox_inches='tight')
print("✓ Saved: gundremmingen_b_did_analysis.png")
plt.close()

# ============================================================================
# Plot 4: Isar 2 (2023 shutdown)
# ============================================================================
print("Creating Isar 2 plot...")
isar2_upstream = load_station_data("landshut-birket-2022.csv")
isar2_downstream = load_station_data("landau-2022.csv")

merged_isar2 = isar2_upstream.merge(
    isar2_downstream,
    on='Datum',
    suffixes=('_upstream', '_downstream')
)

fig, axes = plt.subplots(2, 1, figsize=(12, 8))

ax1 = axes[0]
ax1.plot(merged_isar2['Datum'], merged_isar2['temp_upstream'], 'b-', alpha=0.6, label='Upstream (Landshut-Birket)', linewidth=1)
ax1.plot(merged_isar2['Datum'], merged_isar2['temp_downstream'], 'r-', alpha=0.6, label='Downstream (Landau)', linewidth=1)

shutdown_date_isar2 = pd.Timestamp('2023-04-15')
ax1.axvline(shutdown_date_isar2, color='black', linestyle='--', linewidth=2, label='Isar 2 Shutdown (Apr 15, 2023)')
ax1.axvspan(merged_isar2['Datum'].min(), shutdown_date_isar2, alpha=0.1, color='green', label='Pre-period')
ax1.axvspan(shutdown_date_isar2, merged_isar2['Datum'].max(), alpha=0.1, color='red', label='Post-period')

ax1.set_xlabel('Date', fontsize=11)
ax1.set_ylabel('Water Temperature (°C)', fontsize=11)
ax1.set_title('Isar River (Isar 2): Daily Water Temperature (2022-2024)', fontsize=12, fontweight='bold')
ax1.legend(loc='best')
ax1.grid(True, alpha=0.3)
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

ax2 = axes[1]
merged_isar2['year'] = merged_isar2['Datum'].dt.year
merged_isar2['period'] = merged_isar2['year'].apply(lambda y: 'Pre-2023' if y < 2023 else 'Post-2023')

periods = ['Pre-2023', 'Post-2023']
upstream_means = [merged_isar2[merged_isar2['period'] == p]['temp_upstream'].mean() for p in periods]
downstream_means = [merged_isar2[merged_isar2['period'] == p]['temp_downstream'].mean() for p in periods]

upstream_diff = upstream_means[1] - upstream_means[0]
downstream_diff = downstream_means[1] - downstream_means[0]
did_estimate = downstream_diff - upstream_diff

x_pos = np.arange(len(periods))
width = 0.35

bars1 = ax2.bar(x_pos - width/2, upstream_means, width, label='Upstream (Control)', color='skyblue', alpha=0.8)
bars2 = ax2.bar(x_pos + width/2, downstream_means, width, label='Downstream (Treatment)', color='salmon', alpha=0.8)

for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height, f'{height:.2f}°C',
                ha='center', va='bottom', fontsize=10)

ax2.set_ylabel('Average Water Temperature (°C)', fontsize=11)
ax2.set_title(f'Isar River (Isar 2): DiD Decomposition\nDiD = {did_estimate:.2f}°C', fontsize=12, fontweight='bold')
ax2.set_xticks(x_pos)
ax2.set_xticklabels(periods)
ax2.legend(loc='best')
ax2.grid(True, alpha=0.3, axis='y')
ax2.set_ylim(12, 14)

plt.tight_layout()
plt.savefig('isar2_did_analysis.png', dpi=150, bbox_inches='tight')
print("✓ Saved: isar2_did_analysis.png")
plt.close()

print("\n✓ All four plots created successfully!")
