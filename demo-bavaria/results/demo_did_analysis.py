"""
Simple 2x2 Difference-in-Differences analysis for nuclear power plant shutdowns in Bavaria.
Proof-of-concept demo using available data in demo-bavaria/data/
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Define data paths
data_dir = Path("../data")

def load_station_data(filename):
    """Load temperature data from a GKD CSV file."""
    filepath = data_dir / filename
    
    # Read file and find the data header
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find line with "Tageswerte Wassertemperatur"
        data_start = 0
        for i, line in enumerate(lines):
            if "Tageswerte Wassertemperatur" in line:
                data_start = i + 1
                break
        
        # Read the data
        df = pd.read_csv(
            filepath,
            skiprows=data_start,
            sep=';',
            decimal=',',  # German decimal format
        )
        
        # Handle both 'Mittelwert' and 'Tagesmittelwert' column names
        if 'Mittelwert' in df.columns:
            df = df[['Datum', 'Mittelwert']].rename(columns={'Mittelwert': 'temp'})
            # Parse dates (format: YYYY-MM-DD)
            df['Datum'] = pd.to_datetime(df['Datum'], format='%Y-%m-%d', errors='coerce')
        elif 'Tagesmittelwert' in df.columns:
            df = df[['Datum', 'Tagesmittelwert']].rename(columns={'Tagesmittelwert': 'temp'})
            # Parse dates (format: DD.MM.YYYY)
            df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y', errors='coerce')
            # Convert German decimal format
            df['temp'] = pd.to_numeric(df['temp'], errors='coerce')
        else:
            print(f"Warning: Neither 'Mittelwert' nor 'Tagesmittelwert' found in {filename}")
            return pd.DataFrame()
        
        df = df.dropna(subset=['temp', 'Datum'])
        df = df.sort_values('Datum')
        
        return df
    except FileNotFoundError:
        print(f"Warning: File {filename} not found")
        return pd.DataFrame()

def load_station_data_from_combined(filename, station_name):
    """Load temperature data for a specific station from a combined Laufen-Besigheim file."""
    filepath = data_dir / filename
    
    try:
        # Read the raw CSV with all columns to identify stations
        df = pd.read_csv(
            filepath,
            sep=';',
            decimal=',',
        )
        
        # Filter by station name
        df = df[df['Messstation'].str.contains(station_name, case=False, na=False)]
        
        # Select relevant columns
        df = df[['Datum', 'Tagesmittelwert']].rename(columns={'Tagesmittelwert': 'temp'})
        
        # Handle missing values (marked as '-')
        df['temp'] = pd.to_numeric(df['temp'], errors='coerce')
        df = df.dropna(subset=['temp'])
        
        # Parse dates properly (format: DD.MM.YYYY)
        df['Datum'] = pd.to_datetime(df['Datum'], format='%d.%m.%Y', errors='coerce')
        df = df.dropna(subset=['Datum'])
        
        df = df.sort_values('Datum')
        
        return df
    except FileNotFoundError:
        print(f"Warning: File {filename} not found")
        return pd.DataFrame()

def extract_year(date):
    """Extract year from date."""
    return date.year

def did_analysis(upstream_df, downstream_df, shutdown_year, case_name):
    """
    Perform 2x2 Difference-in-Differences analysis.
    
    Parameters:
    -----------
    upstream_df : DataFrame
        Data from upstream station (control)
    downstream_df : DataFrame
        Data from downstream station (treatment)
    shutdown_year : int
        Year of shutdown
    case_name : str
        Name of the case for output
    
    Returns:
    --------
    dict : Results dictionary
    """
    
    # Merge data on date
    merged = upstream_df.merge(
        downstream_df,
        on='Datum',
        suffixes=('_upstream', '_downstream')
    )
    
    # Extract year
    merged['year'] = merged['Datum'].apply(extract_year)
    
    # Define period (pre = before shutdown, post = after shutdown)
    merged['period'] = merged['year'].apply(lambda y: 'pre' if y < shutdown_year else 'post')
    
    # Get date range
    min_date = merged['Datum'].min()
    max_date = merged['Datum'].max()
    
    print(f"\n{'='*70}")
    print(f"CASE: {case_name}")
    print(f"{'='*70}")
    print(f"Shutdown year: {shutdown_year}")
    print(f"Data period: {min_date.date()} to {max_date.date()}")
    print(f"Pre-period years: {[y for y in sorted(merged['year'].unique()) if y < shutdown_year]}")
    print(f"Post-period years: {[y for y in sorted(merged['year'].unique()) if y >= shutdown_year]}")
    
    # Check if we have sufficient data
    pre_years = [y for y in merged['year'].unique() if y < shutdown_year]
    post_years = [y for y in merged['year'].unique() if y >= shutdown_year]
    
    if len(pre_years) == 0 or len(post_years) == 0:
        print(f"\nDATA LIMITATION: No pre-shutdown data available" if len(pre_years) == 0 
              else f"\nDATA LIMITATION: No post-shutdown data available")
        return {
            'case': case_name,
            'shutdown_year': shutdown_year,
            'min_date': min_date.date(),
            'max_date': max_date.date(),
            'status': 'insufficient_data',
            'did_estimate': np.nan,
            'upstream_pre': np.nan,
            'upstream_post': np.nan,
            'downstream_pre': np.nan,
            'downstream_post': np.nan,
            'upstream_diff': np.nan,
            'downstream_diff': np.nan,
        }
    
    # Calculate means by group and period
    upstream_pre = merged[merged['period'] == 'pre']['temp_upstream'].mean()
    upstream_post = merged[merged['period'] == 'post']['temp_upstream'].mean()
    downstream_pre = merged[merged['period'] == 'pre']['temp_downstream'].mean()
    downstream_post = merged[merged['period'] == 'post']['temp_downstream'].mean()
    
    # Calculate differences
    upstream_diff = upstream_post - upstream_pre
    downstream_diff = downstream_post - downstream_pre
    
    # Calculate DiD estimate
    did_estimate = downstream_diff - upstream_diff
    
    # Display results
    print(f"\nUPSTREAM STATION (Control):")
    print(f"  Pre-period avg temp:  {upstream_pre:7.2f}°C")
    print(f"  Post-period avg temp: {upstream_post:7.2f}°C")
    print(f"  Difference:           {upstream_diff:7.2f}°C")
    
    print(f"\nDOWNSTREAM STATION (Treatment):")
    print(f"  Pre-period avg temp:  {downstream_pre:7.2f}°C")
    print(f"  Post-period avg temp: {downstream_post:7.2f}°C")
    print(f"  Difference:           {downstream_diff:7.2f}°C")
    
    print(f"\nDiD ESTIMATE (Temperature Effect):")
    print(f"  DiD = (Down_post - Down_pre) - (Up_post - Up_pre)")
    print(f"  DiD = ({downstream_post:.2f} - {downstream_pre:.2f}) - ({upstream_post:.2f} - {upstream_pre:.2f})")
    print(f"  DiD = {downstream_diff:.2f} - {upstream_diff:.2f}")
    print(f"  DiD = {did_estimate:7.2f}°C")
    
    interpretation = "Negative effect (cooling)" if did_estimate < 0 else "Positive effect (warming)"
    print(f"\nInterpretation: {interpretation}")
    
    return {
        'case': case_name,
        'shutdown_year': shutdown_year,
        'min_date': min_date.date(),
        'max_date': max_date.date(),
        'status': 'success',
        'did_estimate': did_estimate,
        'upstream_pre': upstream_pre,
        'upstream_post': upstream_post,
        'downstream_pre': downstream_pre,
        'downstream_post': downstream_post,
        'upstream_diff': upstream_diff,
        'downstream_diff': downstream_diff,
    }

# Main analysis
def main():
    print("\n" + "="*70)
    print("PROOF-OF-CONCEPT DiD ANALYSIS: Nuclear Power Plant Shutdowns in Bavaria")
    print("="*70)
    
    results = []
    
    # Case 1: Isar 1 (2011 shutdown)
    print("Loading data for Case 1: Isar 1...")
    isar_upstream = load_station_data("landshut-birket-2010.csv")
    isar_downstream = load_station_data("landau-2010.csv")
    
    if isar_upstream.empty or isar_downstream.empty:
        print("Cannot load Isar 1 data (files not found)")
        result_isar = None
    else:
        result_isar = did_analysis(
            isar_upstream, isar_downstream,
            shutdown_year=2011,
            case_name="Isar 1 (Isar River) - Shutdown May 2011"
        )
        results.append(result_isar)
    
    # Case 2: Gundremmingen C (2021 shutdown)
    print("\n\nLoading data for Case 2: Gundremmingen C...")
    donau_upstream = load_station_data("nue-ulm-2020.csv")
    donau_downstream = load_station_data("donauworth-2020.csv")
    
    result_gundremmingen = did_analysis(
        donau_upstream, donau_downstream,
        shutdown_year=2021,
        case_name="Gundremmingen C (Donau River) - Shutdown Dec 31, 2021"
    )
    results.append(result_gundremmingen)
    
    # Case 3: Gundremmingen B (2017 shutdown with 2016 pre-period data)
    print("\n\nLoading data for Case 3: Gundremmingen B...")
    # Pre-shutdown (2016)
    donau_upstream_b_pre = load_station_data("neu-ulm-2016.csv")
    donau_downstream_b_pre = load_station_data("Donauworth-2016.csv")
    
    # Post-shutdown (2020)
    donau_upstream_b_post = load_station_data("nue-ulm-2020.csv")
    donau_downstream_b_post = load_station_data("donauworth-2020.csv")
    
    # Combine pre and post data
    donau_upstream_b_combined = pd.concat([donau_upstream_b_pre, donau_upstream_b_post], ignore_index=True)
    donau_downstream_b_combined = pd.concat([donau_downstream_b_pre, donau_downstream_b_post], ignore_index=True)
    
    result_gundremmingen_b = did_analysis(
        donau_upstream_b_combined, donau_downstream_b_combined,
        shutdown_year=2017,
        case_name="Gundremmingen B (Donau River) - Shutdown Dec 31, 2017"
    )
    results.append(result_gundremmingen_b)
    
    # Case 4: Isar 2 (2023 shutdown)
    print("\n\nLoading data for Case 4: Isar 2...")
    isar2_upstream = load_station_data("landshut-birket-2022.csv")
    isar2_downstream = load_station_data("landau-2022.csv")
    
    result_isar2 = did_analysis(
        isar2_upstream, isar2_downstream,
        shutdown_year=2023,
        case_name="Isar 2 (Isar River) - Shutdown Apr 15, 2023"
    )
    results.append(result_isar2)
    
    # Case 5: Neckarwestheim 1 (2011 shutdown)
    print("\n\nLoading data for Case 5: Neckarwestheim 1...")
    neckar_w1_upstream = load_station_data("besigheim-2011.csv")
    neckar_w1_downstream = load_station_data("Lauffen-2011.csv")
    
    if neckar_w1_upstream.empty or neckar_w1_downstream.empty:
        print("Cannot load Neckarwestheim 1 data (files not found)")
        result_neckar_w1 = None
    else:
        result_neckar_w1 = did_analysis(
            neckar_w1_upstream, neckar_w1_downstream,
            shutdown_year=2011,
            case_name="Neckarwestheim 1 (Neckar River) - Shutdown Jun 5, 2011"
        )
        results.append(result_neckar_w1)
    
    # Case 6: Neckarwestheim 2 (2023 shutdown)
    print("\n\nLoading data for Case 6: Neckarwestheim 2...")
    neckar_w2_upstream = load_station_data("besigheim-2023.csv")
    neckar_w2_downstream = load_station_data("Lauffen-2023.csv")
    
    if neckar_w2_upstream.empty or neckar_w2_downstream.empty:
        print("Cannot load Neckarwestheim 2 data (files not found)")
        result_neckar_w2 = None
    else:
        result_neckar_w2 = did_analysis(
            neckar_w2_upstream, neckar_w2_downstream,
            shutdown_year=2023,
            case_name="Neckarwestheim 2 (Neckar River) - Shutdown Apr 15, 2023"
        )
        results.append(result_neckar_w2)
    
    # Case 7: Philippsburg 1 (2011 shutdown)
    print("\n\nLoading data for Case 7: Philippsburg 1...")
    philippsburg_upstream = load_station_data("Karlsruhe-2011.csv")
    philippsburg_downstream = load_station_data("Mannheim-2011.csv")
    
    if philippsburg_upstream.empty or philippsburg_downstream.empty:
        print("Cannot load Philippsburg 1 data (files not found)")
        result_philippsburg = None
    else:
        result_philippsburg = did_analysis(
            philippsburg_upstream, philippsburg_downstream,
            shutdown_year=2011,
            case_name="Philippsburg 1 (Rhine River) - Shutdown Mar 22, 2011"
        )
        results.append(result_philippsburg)
    
    # Save results to CSV
    results_df = pd.DataFrame([r for r in results if r is not None])
    output_path = Path("DiD_summary.csv")
    results_df.to_csv(output_path, index=False)
    print(f"\n\n{'='*70}")
    print(f"Results saved to: {output_path}")
    print(f"{'='*70}\n")
    print(results_df.to_string(index=False))
    
    return results_df

if __name__ == "__main__":
    results_df = main()
