"""
Detailed breakdown of each DiD analysis case
"""

import pandas as pd
import numpy as np
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
            parse_dates=['Datum'],
            date_format='%Y-%m-%d'
        )
        
        df = df[['Datum', 'Mittelwert']].rename(columns={'Mittelwert': 'temp'})
        df = df.sort_values('Datum')
        
        return df
    except FileNotFoundError:
        print(f"Warning: File {filename} not found")
        return pd.DataFrame()

def load_station_data_from_combined(filename, station_name):
    """Load temperature data for a specific station from a combined file."""
    filepath = data_dir / filename
    
    try:
        df = pd.read_csv(
            filepath,
            sep=';',
            decimal=',',
        )
        
        df = df[df['Messstation'].str.contains(station_name, case=False, na=False)]
        
        df = df[['Datum', 'Tagesmittelwert']].rename(columns={'Tagesmittelwert': 'temp'})
        
        df['temp'] = pd.to_numeric(df['temp'], errors='coerce')
        df = df.dropna(subset=['temp'])
        
        df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y', errors='coerce')
        df = df.dropna(subset=['Datum'])
        
        df = df.sort_values('Datum')
        
        return df
    except FileNotFoundError:
        print(f"Warning: File {filename} not found")
        return pd.DataFrame()

def detailed_analysis(upstream_df, downstream_df, shutdown_year, case_name):
    """Print detailed breakdown of DiD analysis."""
    
    print(f"\n{'='*80}")
    print(f"CASE: {case_name}")
    print(f"{'='*80}")
    
    merged = upstream_df.merge(
        downstream_df,
        on='Datum',
        suffixes=('_upstream', '_downstream')
    )
    
    merged['year'] = merged['Datum'].dt.year
    merged['period'] = merged['year'].apply(lambda y: 'pre' if y < shutdown_year else 'post')
    
    print(f"\nShutdown year: {shutdown_year}")
    print(f"Date range: {merged['Datum'].min().date()} to {merged['Datum'].max().date()}")
    print(f"Total observations: {len(merged)}")
    
    # Group by year
    print(f"\nObservations by year:")
    year_counts = merged.groupby('year').size()
    for year in sorted(year_counts.index):
        period = 'PRE' if year < shutdown_year else 'POST'
        print(f"  {year}: {year_counts[year]:4d} observations ({period})")
    
    # Pre vs Post split
    pre_data = merged[merged['period'] == 'pre']
    post_data = merged[merged['period'] == 'post']
    
    print(f"\nData split:")
    print(f"  Pre-shutdown:  {len(pre_data)} observations")
    print(f"  Post-shutdown: {len(post_data)} observations")
    
    if len(pre_data) == 0 or len(post_data) == 0:
        print("\n⚠️  INSUFFICIENT DATA: Cannot perform analysis")
        return
    
    # Upstream analysis
    upstream_pre = pre_data['temp_upstream'].mean()
    upstream_post = post_data['temp_upstream'].mean()
    upstream_diff = upstream_post - upstream_pre
    upstream_std_pre = pre_data['temp_upstream'].std()
    upstream_std_post = post_data['temp_upstream'].std()
    
    print(f"\n{'UPSTREAM STATION (Control)':^80}")
    print(f"{'-'*80}")
    print(f"  Pre-period:  Mean = {upstream_pre:7.2f}°C  (n={len(pre_data)}, SD={upstream_std_pre:6.2f})")
    print(f"  Post-period: Mean = {upstream_post:7.2f}°C  (n={len(post_data)}, SD={upstream_std_post:6.2f})")
    print(f"  Difference:  {upstream_diff:7.2f}°C")
    
    # Downstream analysis
    downstream_pre = pre_data['temp_downstream'].mean()
    downstream_post = post_data['temp_downstream'].mean()
    downstream_diff = downstream_post - downstream_pre
    downstream_std_pre = pre_data['temp_downstream'].std()
    downstream_std_post = post_data['temp_downstream'].std()
    
    print(f"\n{'DOWNSTREAM STATION (Treatment)':^80}")
    print(f"{'-'*80}")
    print(f"  Pre-period:  Mean = {downstream_pre:7.2f}°C  (n={len(pre_data)}, SD={downstream_std_pre:6.2f})")
    print(f"  Post-period: Mean = {downstream_post:7.2f}°C  (n={len(post_data)}, SD={downstream_std_post:6.2f})")
    print(f"  Difference:  {downstream_diff:7.2f}°C")
    
    # DiD calculation
    did_estimate = downstream_diff - upstream_diff
    
    print(f"\n{'DiD ESTIMATE':^80}")
    print(f"{'-'*80}")
    print(f"  DiD = (Down_post - Down_pre) - (Up_post - Up_pre)")
    print(f"  DiD = ({downstream_post:.2f} - {downstream_pre:.2f}) - ({upstream_post:.2f} - {upstream_pre:.2f})")
    print(f"  DiD = {downstream_diff:.2f} - {upstream_diff:.2f}")
    print(f"  DiD = {did_estimate:.4f}°C")
    
    interpretation = "Cooling effect" if did_estimate < 0 else "Warming effect" if did_estimate > 0 else "No effect"
    print(f"\n  Interpretation: {interpretation}")

# Run detailed analysis for each case
print("\n" + "="*80)
print("DETAILED OBSERVATION-BY-OBSERVATION BREAKDOWN")
print("="*80)

# Case 1: Isar 1
print("\n[1/6] ISAR 1")
isar1_up = load_station_data("landshut-birket-2010.csv")
isar1_down = load_station_data("landau-2010.csv")
detailed_analysis(isar1_up, isar1_down, 2011, "Isar 1 (Isar River) - Shutdown May 2011")

# Case 2: Gundremmingen C
print("\n[2/6] GUNDREMMINGEN C")
gund_c_up = load_station_data("nue-ulm-2020.csv")
gund_c_down = load_station_data("donauworth-2020.csv")
detailed_analysis(gund_c_up, gund_c_down, 2021, "Gundremmingen C (Donau River) - Shutdown Dec 31, 2021")

# Case 3: Gundremmingen B
print("\n[3/6] GUNDREMMINGEN B")
gund_b_up_pre = load_station_data("neu-ulm-2016.csv")
gund_b_down_pre = load_station_data("Donauworth-2016.csv")
gund_b_up_post = load_station_data("nue-ulm-2020.csv")
gund_b_down_post = load_station_data("donauworth-2020.csv")
gund_b_up = pd.concat([gund_b_up_pre, gund_b_up_post], ignore_index=True).sort_values('Datum')
gund_b_down = pd.concat([gund_b_down_pre, gund_b_down_post], ignore_index=True).sort_values('Datum')
detailed_analysis(gund_b_up, gund_b_down, 2017, "Gundremmingen B (Donau River) - Shutdown Dec 31, 2017")

# Case 4: Isar 2
print("\n[4/6] ISAR 2")
isar2_up = load_station_data("landshut-birket-2022.csv")
isar2_down = load_station_data("landau-2022.csv")
detailed_analysis(isar2_up, isar2_down, 2023, "Isar 2 (Isar River) - Shutdown Apr 15, 2023")

# Case 5: Neckarwestheim 1
print("\n[5/6] NECKARWESTHEIM 1")
nw1_up = load_station_data_from_combined("Laufen-Besigheim-2011.csv", "Besigheim")
nw1_down = load_station_data_from_combined("Laufen-Besigheim-2011.csv", "Lauffen")
detailed_analysis(nw1_up, nw1_down, 2011, "Neckarwestheim 1 (Neckar River) - Shutdown Jun 5, 2011")

# Case 6: Neckarwestheim 2
print("\n[6/6] NECKARWESTHEIM 2")
nw2_up = load_station_data_from_combined("Laufen-Besigheim-2023.csv", "Besigheim")
nw2_down = load_station_data_from_combined("Laufen-Besigheim-2023.csv", "Lauffen")
detailed_analysis(nw2_up, nw2_down, 2023, "Neckarwestheim 2 (Neckar River) - Shutdown Apr 15, 2023")

print("\n" + "="*80)
print("END OF DETAILED BREAKDOWN")
print("="*80 + "\n")
