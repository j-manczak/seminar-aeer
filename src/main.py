"""Main analysis orchestration script.

Run with: python src/main.py

This script orchestrates the entire analysis pipeline:
1. Load and clean data
2. Aggregate to monthly
3. Create event windows
4. Run DiD analysis
5. Generate visualizations
6. Create tables
7. Generate final report
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# Add src to path
SRC_DIR = Path(__file__).parent
sys.path.insert(0, str(SRC_DIR.parent))

from src import config
from src.data_loading import load_temperature_file, load_oxygen_file, find_station_files
from src.data_cleaning import clean_temperature_data, clean_oxygen_data, get_coverage_summary
from src.monthly_aggregation import aggregate_station_pair, calculate_monthly_statistics
from src.event_windows import create_event_window, prepare_did_data, calculate_2x2_table, create_multiple_windows
from src.did_analysis import run_2x2_did_regression, extract_did_coefficient, run_observation_did, print_regression_summary
from src.visualization import (plot_time_series, plot_parallel_trends, plot_did_estimates, 
                              plot_sensitivity_windows, save_figure)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main analysis pipeline."""
    
    logger.info("="*80)
    logger.info("NUCLEAR POWER PLANT SHUTDOWN ANALYSIS - MAIN PIPELINE")
    logger.info("="*80)
    
    # Track results
    all_results = []
    quality_reports = []
    observations_processed = []
    
    # === STEP 1: DATA LOADING AND CLEANING ===
    logger.info("\nSTEP 1: DATA LOADING AND CLEANING")
    logger.info("-" * 80)
    
    # For each observation, load and process data
    temperature_data = {}  # observation_id -> {station -> dataframe}
    oxygen_data = {}
    monthly_combined = {}  # observation_id -> {outcome -> dataframe}
    
    for obs in config.OBSERVATIONS:
        obs_id = obs['obs_id']
        plant = obs['plant']
        upstream = obs['upstream_station']
        downstream = obs['downstream_station']
        
        logger.info(f"\nProcessing Observation {obs_id}: {plant}")
        logger.info(f"  Stations: {upstream} (upstream) -> {downstream} (downstream)")
        
        try:
            # Load temperature files (use specific pattern from config if available)
            temp_pattern = obs.get('temp_file_pattern')
            upstream_temp_files = find_station_files(config.DATA_DIR, upstream, 'temperature', file_pattern=temp_pattern)
            downstream_temp_files = find_station_files(config.DATA_DIR, downstream, 'temperature', file_pattern=temp_pattern)
            
            if len(upstream_temp_files) == 0 or len(downstream_temp_files) == 0:
                logger.warning(f"  Temperature data not found - skipping temperature analysis")
                continue
            
            # Load and clean temperature
            temp_up = load_temperature_file(upstream_temp_files[0])
            temp_down = load_temperature_file(downstream_temp_files[0])
            
            if temp_up is not None and temp_down is not None:
                clean_temp_up, report_up = clean_temperature_data(temp_up, upstream)
                clean_temp_down, report_down = clean_temperature_data(temp_down, downstream)
                
                quality_reports.extend([report_up, report_down])
                
                temperature_data[obs_id] = {
                    'upstream': clean_temp_up,
                    'downstream': clean_temp_down
                }
                
                logger.info(f"  ✓ Temperature: {len(clean_temp_up)} upstream, {len(clean_temp_down)} downstream")
            
            # Load oxygen files (use specific pattern from config if available)
            oxygen_pattern = obs.get('oxygen_file_pattern')
            upstream_oxygen_files = find_station_files(config.DATA_DIR, upstream, 'oxygen', file_pattern=oxygen_pattern)
            downstream_oxygen_files = find_station_files(config.DATA_DIR, downstream, 'oxygen', file_pattern=oxygen_pattern)
            
            if len(upstream_oxygen_files) > 0 and len(downstream_oxygen_files) > 0:
                oxygen_up = load_oxygen_file(upstream_oxygen_files[0])
                oxygen_down = load_oxygen_file(downstream_oxygen_files[0])
                
                if oxygen_up is not None and oxygen_down is not None:
                    clean_oxygen_up, report_oxygen_up = clean_oxygen_data(oxygen_up, upstream)
                    clean_oxygen_down, report_oxygen_down = clean_oxygen_data(oxygen_down, downstream)
                    
                    quality_reports.extend([report_oxygen_up, report_oxygen_down])
                    
                    oxygen_data[obs_id] = {
                        'upstream': clean_oxygen_up,
                        'downstream': clean_oxygen_down
                    }
                    
                    logger.info(f"  ✓ Oxygen: {len(clean_oxygen_up)} upstream, {len(clean_oxygen_down)} downstream")
            else:
                logger.warning(f"  Oxygen data not found")
        
        except Exception as e:
            logger.error(f"  ✗ Error processing observation {obs_id}: {e}")
            continue
    
    # === STEP 2: MONTHLY AGGREGATION ===
    logger.info("\n\nSTEP 2: MONTHLY AGGREGATION")
    logger.info("-" * 80)
    
    for obs in config.OBSERVATIONS:
        obs_id = obs['obs_id']
        plant = obs['plant']
        upstream = obs['upstream_station']
        downstream = obs['downstream_station']
        
        if obs_id not in temperature_data:
            continue
        
        logger.info(f"\nAggregating Observation {obs_id}: {plant}")
        
        try:
            # Aggregate temperature
            temp_up = temperature_data[obs_id]['upstream']
            temp_down = temperature_data[obs_id]['downstream']
            
            monthly_temp = aggregate_station_pair(
                temp_up, temp_down, 'temperature_mean',
                upstream, downstream
            )
            
            if len(monthly_temp) > 0:
                monthly_combined[obs_id] = {'temperature': monthly_temp}
                logger.info(f"  ✓ Monthly temperature: {len(monthly_temp)} months")
                
                # Aggregate oxygen if available
                if obs_id in oxygen_data:
                    oxygen_up = oxygen_data[obs_id]['upstream']
                    oxygen_down = oxygen_data[obs_id]['downstream']
                    
                    monthly_oxygen = aggregate_station_pair(
                        oxygen_up, oxygen_down, 'oxygen_mean',
                        upstream, downstream
                    )
                    
                    if len(monthly_oxygen) > 0:
                        monthly_combined[obs_id]['oxygen'] = monthly_oxygen
                        logger.info(f"  ✓ Monthly oxygen: {len(monthly_oxygen)} months")
            
        except Exception as e:
            logger.error(f"  ✗ Error aggregating observation {obs_id}: {e}")
            continue
    
    # === STEP 3: DiD ANALYSIS ===
    logger.info("\n\nSTEP 3: DIFFERENCE-IN-DIFFERENCES ANALYSIS")
    logger.info("-" * 80)
    
    for obs in config.OBSERVATIONS:
        obs_id = obs['obs_id']
        plant = obs['plant']
        upstream = obs['upstream_station']
        downstream = obs['downstream_station']
        shutdown_date = obs['shutdown_date']
        
        if obs_id not in monthly_combined:
            continue
        
        logger.info(f"\nAnalyzing Observation {obs_id}: {plant} (Shutdown: {shutdown_date.date()})")
        observations_processed.append(obs_id)
        
        try:
            # === TEMPERATURE ANALYSIS ===
            if 'temperature' in monthly_combined[obs_id]:
                monthly_temp = monthly_combined[obs_id]['temperature']
                upstream_col = f"{upstream}_mean"
                downstream_col = f"{downstream}_mean"
                
                logger.info(f"  Temperature analysis:")
                
                # Create event window and calculate 2x2
                windowed_temp, window_info = create_event_window(
                    monthly_temp, shutdown_date, config.MAIN_WINDOW_YEARS
                )
                
                if window_info.get('has_complete_window', False):
                    table_2x2 = calculate_2x2_table(windowed_temp, upstream_col, downstream_col)
                    
                    if table_2x2:
                        logger.info(f"    Pre:  upstream={table_2x2['upstream_pre']:.2f}, "
                                  f"downstream={table_2x2['downstream_pre']:.2f}")
                        logger.info(f"    Post: upstream={table_2x2['upstream_post']:.2f}, "
                                  f"downstream={table_2x2['downstream_post']:.2f}")
                        logger.info(f"    DiD (2×2): {table_2x2['did_estimate']:.4f}")
                    
                    # Prepare for regression
                    did_data = prepare_did_data(windowed_temp, upstream_col, downstream_col)
                    regression = run_2x2_did_regression(did_data, include_month_fe=True)
                    
                    if regression is not None:
                        did_result = extract_did_coefficient(regression)
                        if did_result is not None:
                            did_result.observation_id = obs_id
                            did_result.plant = plant
                            did_result.outcome = 'temperature'
                            did_result.window_years = config.MAIN_WINDOW_YEARS
                            
                            all_results.append(did_result.to_dict())
                            print_regression_summary(did_result)
                
                # Sensitivity analysis
                logger.info(f"    Sensitivity analysis:")
                sensitivity_windows = create_multiple_windows(
                    monthly_temp, shutdown_date, config.SENSITIVITY_WINDOWS
                )
                
                for window_years, (windowed, info) in sensitivity_windows.items():
                    if info.get('has_complete_window', False):
                        did_data = prepare_did_data(windowed, upstream_col, downstream_col)
                        regression = run_2x2_did_regression(did_data, include_month_fe=True)
                        
                        if regression is not None:
                            did_result = extract_did_coefficient(regression)
                            if did_result is not None:
                                did_result.observation_id = obs_id
                                did_result.plant = plant
                                did_result.outcome = 'temperature'
                                did_result.window_years = window_years
                                
                                all_results.append(did_result.to_dict())
                                logger.info(f"      {window_years}yr: DiD={did_result.did_coefficient:.4f}, p={did_result.p_value:.3f}")
            
            # === OXYGEN ANALYSIS ===
            if 'oxygen' in monthly_combined[obs_id]:
                monthly_oxygen = monthly_combined[obs_id]['oxygen']
                upstream_col = f"{upstream}_mean"
                downstream_col = f"{downstream}_mean"
                
                logger.info(f"  Oxygen analysis:")
                
                # Main analysis
                windowed_oxygen, window_info = create_event_window(
                    monthly_oxygen, shutdown_date, config.MAIN_WINDOW_YEARS
                )
                
                if window_info.get('has_complete_window', False):
                    table_2x2 = calculate_2x2_table(windowed_oxygen, upstream_col, downstream_col)
                    
                    if table_2x2:
                        logger.info(f"    Pre:  upstream={table_2x2['upstream_pre']:.2f}, "
                                  f"downstream={table_2x2['downstream_pre']:.2f}")
                        logger.info(f"    Post: upstream={table_2x2['upstream_post']:.2f}, "
                                  f"downstream={table_2x2['downstream_post']:.2f}")
                        logger.info(f"    DiD (2×2): {table_2x2['did_estimate']:.4f}")
                    
                    did_data = prepare_did_data(windowed_oxygen, upstream_col, downstream_col)
                    regression = run_2x2_did_regression(did_data, include_month_fe=True)
                    
                    if regression is not None:
                        did_result = extract_did_coefficient(regression)
                        if did_result is not None:
                            did_result.observation_id = obs_id
                            did_result.plant = plant
                            did_result.outcome = 'oxygen'
                            did_result.window_years = config.MAIN_WINDOW_YEARS
                            
                            all_results.append(did_result.to_dict())
                            print_regression_summary(did_result)
                
                # Sensitivity analysis
                logger.info(f"    Sensitivity analysis:")
                sensitivity_windows = create_multiple_windows(
                    monthly_oxygen, shutdown_date, config.SENSITIVITY_WINDOWS
                )
                
                for window_years, (windowed, info) in sensitivity_windows.items():
                    if info.get('has_complete_window', False):
                        did_data = prepare_did_data(windowed, upstream_col, downstream_col)
                        regression = run_2x2_did_regression(did_data, include_month_fe=True)
                        
                        if regression is not None:
                            did_result = extract_did_coefficient(regression)
                            if did_result is not None:
                                did_result.observation_id = obs_id
                                did_result.plant = plant
                                did_result.outcome = 'oxygen'
                                did_result.window_years = window_years
                                
                                all_results.append(did_result.to_dict())
                                logger.info(f"      {window_years}yr: DiD={did_result.did_coefficient:.4f}, p={did_result.p_value:.3f}")
        
        except Exception as e:
            logger.error(f"  ✗ Error in DiD analysis: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # === STEP 4: VISUALIZATION ===
    logger.info("\n\nSTEP 4: GENERATING VISUALIZATIONS")
    logger.info("-" * 80)
    
    for obs in config.OBSERVATIONS:
        obs_id = obs['obs_id']
        plant = obs['plant']
        upstream = obs['upstream_station']
        downstream = obs['downstream_station']
        shutdown_date = obs['shutdown_date']
        
        if obs_id not in monthly_combined:
            continue
        
        logger.info(f"\nGenerating figures for Observation {obs_id}: {plant}")
        
        # Temperature figures
        if 'temperature' in monthly_combined[obs_id]:
            monthly_temp = monthly_combined[obs_id]['temperature']
            upstream_col = f"{upstream}_mean"
            downstream_col = f"{downstream}_mean"
            
            # Time series
            fig = plot_time_series(monthly_temp, upstream_col, downstream_col,
                                  shutdown_date, plant, 'temperature',
                                  config.TEMPERATURE_UNIT)
            if fig:
                save_figure(fig, config.FIGURES_DIR / f"obs{obs_id:02d}_{plant.replace(' ', '_')}_temperature_timeseries.png")
                
            # Parallel trends
            fig = plot_parallel_trends(monthly_temp, upstream_col, downstream_col,
                                      shutdown_date, plant, 'temperature',
                                      config.TEMPERATURE_UNIT)
            if fig:
                save_figure(fig, config.FIGURES_DIR / f"obs{obs_id:02d}_{plant.replace(' ', '_')}_temperature_parallelt trends.png")
        
        # Oxygen figures
        if 'oxygen' in monthly_combined[obs_id]:
            monthly_oxygen = monthly_combined[obs_id]['oxygen']
            upstream_col = f"{upstream}_mean"
            downstream_col = f"{downstream}_mean"
            
            # Time series
            fig = plot_time_series(monthly_oxygen, upstream_col, downstream_col,
                                  shutdown_date, plant, 'oxygen',
                                  config.OXYGEN_UNIT)
            if fig:
                save_figure(fig, config.FIGURES_DIR / f"obs{obs_id:02d}_{plant.replace(' ', '_')}_oxygen_timeseries.png")
            
            # Parallel trends
            fig = plot_parallel_trends(monthly_oxygen, upstream_col, downstream_col,
                                      shutdown_date, plant, 'oxygen',
                                      config.OXYGEN_UNIT)
            if fig:
                save_figure(fig, config.FIGURES_DIR / f"obs{obs_id:02d}_{plant.replace(' ', '_')}_oxygen_parallel_trends.png")
    
    # Overall DiD comparison figures
    if all_results:
        logger.info("\nGenerating cross-observation summary figures")
        
        # Temperature DiD estimates
        fig = plot_did_estimates(all_results, 'temperature', config.MAIN_WINDOW_YEARS)
        if fig:
            save_figure(fig, config.FIGURES_DIR / "did_temperature_all_obs.png")
        
        # Oxygen DiD estimates
        fig = plot_did_estimates(all_results, 'oxygen', config.MAIN_WINDOW_YEARS)
        if fig:
            save_figure(fig, config.FIGURES_DIR / "did_oxygen_all_obs.png")
        
        # Sensitivity plots for each observation
        for obs in config.OBSERVATIONS:
            obs_id = obs['obs_id']
            if obs_id not in observations_processed:
                continue
            
            # Temperature sensitivity
            fig = plot_sensitivity_windows(all_results, obs_id, 'temperature')
            if fig:
                save_figure(fig, config.FIGURES_DIR / f"obs{obs_id:02d}_{obs['plant'].replace(' ', '_')}_sensitivity_temperature.png")
            
            # Oxygen sensitivity
            fig = plot_sensitivity_windows(all_results, obs_id, 'oxygen')
            if fig:
                save_figure(fig, config.FIGURES_DIR / f"obs{obs_id:02d}_{obs['plant'].replace(' ', '_')}_sensitivity_oxygen.png")
    
    # === STEP 5: GENERATE TABLES ===
    logger.info("\n\nSTEP 5: GENERATING RESULT TABLES")
    logger.info("-" * 80)
    
    # Convert results to DataFrame
    if all_results:
        results_df = pd.DataFrame(all_results)
        
        # Main results table (5-year window only)
        main_results = results_df[results_df['window_years'] == config.MAIN_WINDOW_YEARS].copy()
        main_results.to_csv(config.TABLES_DIR / "did_main_results.csv", index=False)
        logger.info(f"Saved main DiD results: {len(main_results)} entries")
        
        # All results (including sensitivity)
        results_df.to_csv(config.TABLES_DIR / "did_all_results.csv", index=False)
        logger.info(f"Saved all results: {len(results_df)} entries")
        
        # Sensitivity table (pivot by window)
        sensitivity_pivot = results_df.pivot_table(
            index=['observation_id', 'plant', 'outcome'],
            columns='window_years',
            values='did_coefficient'
        )
        sensitivity_pivot.to_csv(config.TABLES_DIR / "did_sensitivity_table.csv")
        logger.info(f"Saved sensitivity analysis table")
    
    # Data quality table
    if quality_reports:
        quality_data = [r.summary() for r in quality_reports]
        quality_df = pd.DataFrame(quality_data)
        quality_df.to_csv(config.DATA_QUALITY_DIR / "data_quality_report.csv", index=False)
        logger.info(f"Saved data quality report: {len(quality_df)} stations")
    
    # === STEP 6: FINAL SUMMARY ===
    logger.info("\n\n" + "="*80)
    logger.info("ANALYSIS COMPLETE")
    logger.info("="*80)
    
    logger.info(f"\nObservations analysed: {len(observations_processed)}")
    logger.info(f"Total results generated: {len(all_results)}")
    logger.info(f"\nResults saved to: {config.FINAL_RESULTS_DIR}")
    logger.info(f"  - Tables: {config.TABLES_DIR}")
    logger.info(f"  - Figures: {config.FIGURES_DIR}")
    logger.info(f"  - Data quality: {config.DATA_QUALITY_DIR}")
    
    if main_results is not None:
        logger.info(f"\nMain DiD Results (5-year window):")
        for _, row in main_results.iterrows():
            sig = "***" if row['p_value'] < 0.01 else ("**" if row['p_value'] < 0.05 else ("*" if row['p_value'] < 0.10 else ""))
            logger.info(f"  Obs {row['observation_id']}: {row['plant']:25s} ({row['outcome']:11s}) "
                       f"DiD={row['did_coefficient']:8.4f}{sig} (p={row['p_value']:.3f})")
    
    logger.info("\n" + "="*80)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
