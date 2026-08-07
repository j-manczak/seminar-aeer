"""Monthly aggregation module.

Aggregates daily observations into monthly means with completeness tracking.
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


def aggregate_to_monthly(df: pd.DataFrame, value_col: str, 
                        min_observations: int = 5) -> pd.DataFrame:
    """Aggregate daily data to monthly means.
    
    Args:
        df: DataFrame with 'date' column and a value column
        value_col: Name of the column to aggregate (e.g., 'temperature_mean')
        min_observations: Minimum daily observations required for a monthly mean
        
    Returns:
        DataFrame with columns: year, month, year_month, monthly_mean, n_observations
    """
    if len(df) == 0:
        return pd.DataFrame(columns=['year', 'month', 'year_month', 'monthly_mean', 'n_observations'])
    
    df = df.copy()
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['year_month'] = df['date'].dt.to_period('M')
    
    # Group by year and month
    grouped = df.groupby(['year', 'month']).agg(
        monthly_mean=(value_col, 'mean'),
        n_observations=(value_col, 'count'),
        date=('date', 'min')  # Keep the first date of the month for reference
    ).reset_index()
    
    # Create year_month as string for easier handling
    grouped['year_month'] = grouped['date'].dt.to_period('M').astype(str)
    
    # Flag months with very few observations
    flagged = grouped[grouped['n_observations'] < min_observations]
    if len(flagged) > 0:
        logger.warning(f"Flagged {len(flagged)} months with < {min_observations} observations")
        for _, row in flagged.iterrows():
            logger.warning(f"  {row['year_month']}: {row['n_observations']} observations")
    
    return grouped[['year', 'month', 'year_month', 'monthly_mean', 'n_observations', 'date']]


def aggregate_station_pair(upstream_df: pd.DataFrame, downstream_df: pd.DataFrame,
                           value_col: str, upstream_name: str, 
                           downstream_name: str) -> pd.DataFrame:
    """Aggregate upstream and downstream station data to monthly means.
    
    Args:
        upstream_df: Daily upstream observations
        downstream_df: Daily downstream observations
        value_col: Column to aggregate
        upstream_name: Name of upstream station
        downstream_name: Name of downstream station
        
    Returns:
        Combined DataFrame with columns for both stations
    """
    if len(upstream_df) == 0 or len(downstream_df) == 0:
        logger.warning(f"Empty data for {upstream_name} or {downstream_name}")
        return pd.DataFrame()
    
    # Aggregate both
    up_agg = aggregate_to_monthly(upstream_df, value_col)
    down_agg = aggregate_to_monthly(downstream_df, value_col)
    
    if len(up_agg) == 0 or len(down_agg) == 0:
        logger.warning(f"No monthly data for {upstream_name} or {downstream_name}")
        return pd.DataFrame()
    
    # Merge on year and month
    merged = up_agg.merge(down_agg, on=['year', 'month', 'year_month'], 
                         how='inner', suffixes=('_up', '_down'))
    
    # Rename for clarity
    merged = merged.rename(columns={
        'monthly_mean_up': f'{upstream_name}_mean',
        'monthly_mean_down': f'{downstream_name}_mean',
        'n_observations_up': f'{upstream_name}_n',
        'n_observations_down': f'{downstream_name}_n',
    })
    
    # Add station-pair identifier
    merged['upstream_station'] = upstream_name
    merged['downstream_station'] = downstream_name
    
    logger.info(f"Monthly data: {len(merged)} months with both stations")
    
    return merged[['year', 'month', 'year_month', 
                   f'{upstream_name}_mean', f'{downstream_name}_mean',
                   f'{upstream_name}_n', f'{downstream_name}_n',
                   'upstream_station', 'downstream_station']]


def calculate_monthly_statistics(monthly_df: pd.DataFrame, 
                                upstream_col: str, 
                                downstream_col: str) -> Dict:
    """Calculate descriptive statistics for monthly aggregates.
    
    Args:
        monthly_df: Monthly aggregated data
        upstream_col: Name of upstream column
        downstream_col: Name of downstream column
        
    Returns:
        Dictionary with statistics
    """
    if len(monthly_df) == 0:
        return {}
    
    return {
        'n_months': len(monthly_df),
        'upstream_mean': monthly_df[upstream_col].mean(),
        'upstream_std': monthly_df[upstream_col].std(),
        'downstream_mean': monthly_df[downstream_col].mean(),
        'downstream_std': monthly_df[downstream_col].std(),
        'mean_difference': monthly_df[downstream_col].mean() - monthly_df[upstream_col].mean(),
        'date_range_start': monthly_df['year_month'].min(),
        'date_range_end': monthly_df['year_month'].max(),
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))
    
    from data_loading import load_temperature_file
    from data_cleaning import clean_temperature_data
    from config import DATA_DIR
    
    logging.basicConfig(level=logging.INFO)
    
    # Test aggregation
    print("Testing monthly aggregation...")
    
    test_temp = DATA_DIR / "Landshut_Birket_2011-5_C.csv"
    temp_df = load_temperature_file(test_temp)
    if temp_df is not None:
        clean_df, _ = clean_temperature_data(temp_df, "Landshut-Birket")
        monthly = aggregate_to_monthly(clean_df, 'temperature_mean')
        print(f"Created {len(monthly)} monthly observations")
        print(monthly.head(10))
        
        stats = calculate_monthly_statistics(monthly, 'monthly_mean', 'monthly_mean')
        print(f"\nStatistics: {stats}")
