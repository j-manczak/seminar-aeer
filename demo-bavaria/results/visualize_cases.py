"""
Generate individual visualization plots for each DiD case
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path

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
        )
        
        if 'Mittelwert' in df.columns:
            df = df[['Datum', 'Mittelwert']].rename(columns={'Mittelwert': 'temp'})
            df['Datum'] = pd.to_datetime(df['Datum'], format='%Y-%m-%d', errors='coerce')
        elif 'Tagesmittelwert' in df.columns:
            df = df[['Datum', 'Tagesmittelwert']].rename(columns={'Tagesmittelwert': 'temp'})
            df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y', errors='coerce')
            df['temp'] = pd.to_numeric(df['temp'], errors='coerce')
        
        df = df.dropna(subset=['temp', 'Datum'])
        df = df.sort_values('Datum')
        
        return df
    except FileNotFoundError:
        print(f"Warning: File {filename} not found")
        return pd.DataFrame()

def create_case_visualization(upstream_df, downstream_df, shutdown_date, case_name, filename):
    """Create a comprehensive visualization for a single case."""
    
    # Merge data
    merged = upstream_df.merge(downstream_df, on='Datum', suffixes=('_upstream', '_downstream'))
    merged = merged.sort_values('Datum')
    
    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Extract shutdown year for period calculation
    shutdown_year = shutdown_date.year
    
    # Subplot 1: Time series with pre/post periods
    ax1.plot(merged['Datum'], merged['temp_upstream'], label='Upstream (Control)', 
             linewidth=1.5, color='#1f77b4', alpha=0.7)
    ax1.plot(merged['Datum'], merged['temp_downstream'], label='Downstream (Treatment)', 
             linewidth=1.5, color='#ff7f0e', alpha=0.7)
    
    # Highlight pre/post shutdown periods
    pre_end = pd.Timestamp(year=shutdown_year, month=12, day=31)
    pre_mask = merged['Datum'] <= pre_end
    post_mask = merged['Datum'] > pre_end
    
    ax1.axvline(x=shutdown_date, color='red', linestyle='--', linewidth=2, label=f'Shutdown ({shutdown_date.date()})')
    ax1.axvspan(merged['Datum'].min(), pre_end, alpha=0.1, color='green', label='Pre-shutdown Period')
    ax1.axvspan(pre_end, merged['Datum'].max(), alpha=0.1, color='red', label='Post-shutdown Period')
    
    ax1.set_ylabel('Temperature (°C)', fontsize=11, fontweight='bold')
    ax1.set_title(f'{case_name}\nDaily Temperature Time Series', fontsize=12, fontweight='bold')
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Calculate statistics for subplot 2
    merged['year'] = merged['Datum'].dt.year
    merged['period'] = merged['year'].apply(lambda y: 'pre' if y < shutdown_year else 'post')
    
    pre_data = merged[merged['period'] == 'pre']
    post_data = merged[merged['period'] == 'post']
    
    upstream_pre = pre_data['temp_upstream'].mean()
    upstream_post = post_data['temp_upstream'].mean()
    downstream_pre = pre_data['temp_downstream'].mean()
    downstream_post = post_data['temp_downstream'].mean()
    
    upstream_diff = upstream_post - upstream_pre
    downstream_diff = downstream_post - downstream_pre
    did_estimate = downstream_diff - upstream_diff
    
    # Subplot 2: DiD decomposition
    periods = ['Pre-shutdown', 'Post-shutdown', 'Difference', 'DiD Estimate']
    upstream_vals = [upstream_pre, upstream_post, upstream_diff, did_estimate]
    downstream_vals = [downstream_pre, downstream_post, downstream_diff, 0]
    
    x = np.arange(len(periods))
    width = 0.35
    
    bars1 = ax2.bar(x - width/2, upstream_vals, width, label='Upstream (Control)', 
                    color='#1f77b4', edgecolor='black', linewidth=1)
    bars2 = ax2.bar(x + width/2, downstream_vals, width, label='Downstream (Treatment)', 
                    color='#ff7f0e', edgecolor='black', linewidth=1)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height != 0:
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.2f}', ha='center', va='bottom' if height > 0 else 'top',
                        fontsize=9, fontweight='bold')
    
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax2.set_ylabel('Temperature (°C)', fontsize=11, fontweight='bold')
    ax2.set_title('DiD Decomposition Analysis', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(periods)
    ax2.legend(loc='best', fontsize=10)
    ax2.grid(axis='y', alpha=0.3)
    
    # Add DiD interpretation
    interpretation = "Cooling effect" if did_estimate < 0 else "Warming effect" if did_estimate > 0 else "No effect"
    fig.text(0.5, 0.02, f'DiD Estimate: {did_estimate:.4f}°C ({interpretation})', 
             ha='center', fontsize=11, fontweight='bold', 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {filename}")
    plt.close()

# Generate visualizations for all 6 cases
print("\n" + "="*80)
print("GENERATING INDIVIDUAL CASE VISUALIZATIONS")
print("="*80 + "\n")

# Case 1: Isar 1
print("[1/6] Creating visualization for Isar 1...")
isar1_up = load_station_data("landshut-birket-2010.csv")
isar1_down = load_station_data("landau-2010.csv")
create_case_visualization(isar1_up, isar1_down, pd.Timestamp('2011-05-01'), 
                          "Isar 1 - Isar River", "case_01_isar1_2011.png")

# Case 2: Gundremmingen C
print("[2/6] Creating visualization for Gundremmingen C...")
gund_c_up = load_station_data("nue-ulm-2020.csv")
gund_c_down = load_station_data("donauworth-2020.csv")
create_case_visualization(gund_c_up, gund_c_down, pd.Timestamp('2021-12-31'), 
                          "Gundremmingen C - Donau River", "case_02_gundremmingen_c_2021.png")

# Case 3: Gundremmingen B
print("[3/6] Creating visualization for Gundremmingen B...")
gund_b_up_pre = load_station_data("neu-ulm-2016.csv")
gund_b_down_pre = load_station_data("Donauworth-2016.csv")
gund_b_up_post = load_station_data("nue-ulm-2020.csv")
gund_b_down_post = load_station_data("donauworth-2020.csv")
gund_b_up = pd.concat([gund_b_up_pre, gund_b_up_post], ignore_index=True).sort_values('Datum')
gund_b_down = pd.concat([gund_b_down_pre, gund_b_down_post], ignore_index=True).sort_values('Datum')
create_case_visualization(gund_b_up, gund_b_down, pd.Timestamp('2017-12-31'), 
                          "Gundremmingen B - Donau River", "case_03_gundremmingen_b_2017.png")

# Case 4: Isar 2
print("[4/6] Creating visualization for Isar 2...")
isar2_up = load_station_data("landshut-birket-2022.csv")
isar2_down = load_station_data("landau-2022.csv")
create_case_visualization(isar2_up, isar2_down, pd.Timestamp('2023-04-15'), 
                          "Isar 2 - Isar River", "case_04_isar2_2023.png")

# Case 5: Neckarwestheim 1
print("[5/6] Creating visualization for Neckarwestheim 1...")
nw1_up = load_station_data("besigheim-2011.csv")
nw1_down = load_station_data("Lauffen-2011.csv")
create_case_visualization(nw1_up, nw1_down, pd.Timestamp('2011-06-05'), 
                          "Neckarwestheim 1 - Neckar River", "case_05_neckarwestheim1_2011.png")

# Case 6: Neckarwestheim 2
print("[6/6] Creating visualization for Neckarwestheim 2...")
nw2_up = load_station_data("besigheim-2023.csv")
nw2_down = load_station_data("Lauffen-2023.csv")
create_case_visualization(nw2_up, nw2_down, pd.Timestamp('2023-04-15'), 
                          "Neckarwestheim 2 - Neckar River", "case_06_neckarwestheim2_2023.png")

# Case 7: Philippsburg 1
print("[7/7] Creating visualization for Philippsburg 1...")
phil_up = load_station_data("Karlsruhe-2011.csv")
phil_down = load_station_data("Mannheim-2011.csv")
create_case_visualization(phil_up, phil_down, pd.Timestamp('2011-03-22'), 
                          "Philippsburg 1 - Rhine River", "case_07_philippsburg1_2011.png")

# Case 8: Philippsburg 2
print("[8/8] Creating visualization for Philippsburg 2...")
phil2_up = load_station_data("Karlsruhe-2019.csv")
phil2_down = load_station_data("Mannheim-2019.csv")
create_case_visualization(phil2_up, phil2_down, pd.Timestamp('2019-12-31'), 
                          "Philippsburg 2 - Rhine River", "case_08_philippsburg2_2019.png")

print("\n" + "="*80)
print("✅ ALL VISUALIZATIONS GENERATED SUCCESSFULLY!")
print("="*80)
print("\nFiles created:")
print("  1. case_01_isar1_2011.png")
print("  2. case_02_gundremmingen_c_2021.png")
print("  3. case_03_gundremmingen_b_2017.png")
print("  4. case_04_isar2_2023.png")
print("  5. case_05_neckarwestheim1_2011.png")
print("  6. case_06_neckarwestheim2_2023.png")
print("  7. case_07_philippsburg1_2011.png")
print("  8. case_08_philippsburg2_2019.png\n")
