"""Event window construction for DiD analysis.

Creates pre/post windows around shutdown events with flexible window lengths.
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def create_event_window(df: pd.DataFrame, shutdown_date: datetime, 
                       window_years: int = 5,
                       year_col: str = 'year',
                       month_col: str = 'month') -> Tuple[pd.DataFrame, Dict]:
    """Create pre/post event window around a shutdown.
    
    Args:
        df: Monthly aggregated data with year, month columns
        shutdown_date: Exact shutdown date
        window_years: Number of years before/after shutdown
        year_col: Name of year column
        month_col: Name of month column
        
    Returns:
        Tuple of (windowed data, window info dict)
    """
    if len(df) == 0:
        logger.warning("Empty input data for event window")
        return pd.DataFrame(), {}
    
    df = df.copy()
    
    # Shutdown year and month
    shutdown_year = shutdown_date.year
    shutdown_month = shutdown_date.month
    
    # Calculate pre/post cutoffs
    pre_year_start = shutdown_year - window_years
    post_year_end = shutdown_year + window_years
    
    # Create pre and post dummy variable
    # Pre: before shutdown date
    # Post: at/after shutdown date (treating shutdown year as post)
    df['time_period'] = df.apply(
        lambda row: 'pre' if (row[year_col] < shutdown_year) or 
                           (row[year_col] == shutdown_year and row[month_col] < shutdown_month)
                    else 'post',
        axis=1
    )
    
    # Filter to window
    mask = (df[year_col] >= pre_year_start) & (df[year_col] <= post_year_end)
    windowed = df[mask].copy()
    
    # Count pre and post observations
    pre_obs = len(windowed[windowed['time_period'] == 'pre'])
    post_obs = len(windowed[windowed['time_period'] == 'post'])
    
    window_info = {
        'shutdown_date': shutdown_date,
        'shutdown_year': shutdown_year,
        'window_years': window_years,
        'year_range': (pre_year_start, post_year_end),
        'pre_year_range': (pre_year_start, shutdown_year - 1),
        'post_year_range': (shutdown_year, post_year_end),
        'n_months_pre': pre_obs,
        'n_months_post': post_obs,
        'n_months_total': len(windowed),
        'has_complete_window': (pre_obs > 0) and (post_obs > 0)
    }
    
    if len(windowed) > 0:
        logger.info(f"Event window: {pre_obs} pre-months, {post_obs} post-months "
                   f"({window_years}-year window around {shutdown_date.date()})")
    else:
        logger.warning(f"No data in event window for {shutdown_date}")
    
    return windowed, window_info


def create_multiple_windows(df: pd.DataFrame, shutdown_date: datetime,
                           window_lengths: list) -> Dict[int, Tuple[pd.DataFrame, Dict]]:
    """Create multiple event windows for sensitivity analysis.
    
    Args:
        df: Monthly aggregated data
        shutdown_date: Shutdown date
        window_lengths: List of window lengths in years
        
    Returns:
        Dictionary mapping window length to (windowed_data, window_info)
    """
    windows = {}
    
    for window_years in sorted(window_lengths):
        windowed, info = create_event_window(df, shutdown_date, window_years)
        windows[window_years] = (windowed, info)
    
    return windows


def prepare_did_data(windowed_df: pd.DataFrame, 
                    upstream_col: str,
                    downstream_col: str) -> pd.DataFrame:
    """Prepare data for 2x2 DiD regression.
    
    Creates binary variables:
    - post: 1 if after shutdown, 0 if before
    - downstream: 1 if downstream station, 0 if upstream
    - post_x_downstream: interaction
    
    Args:
        windowed_df: Event window data
        upstream_col: Column name with upstream values
        downstream_col: Column name with downstream values
        
    Returns:
        Long-format DataFrame ready for regression
    """
    # Create two rows per month: one for upstream, one for downstream
    records = []
    
    for _, row in windowed_df.iterrows():
        # Upstream station
        records.append({
            'year': row['year'],
            'month': row['month'],
            'year_month': row['year_month'],
            'time_period': row['time_period'],
            'post': 1 if row['time_period'] == 'post' else 0,
            'downstream': 0,  # Upstream
            'outcome': row[upstream_col],
            'station': row.get('upstream_station', 'upstream'),
        })
        
        # Downstream station
        records.append({
            'year': row['year'],
            'month': row['month'],
            'year_month': row['year_month'],
            'time_period': row['time_period'],
            'post': 1 if row['time_period'] == 'post' else 0,
            'downstream': 1,  # Downstream
            'outcome': row[downstream_col],
            'station': row.get('downstream_station', 'downstream'),
        })
    
    did_df = pd.DataFrame(records)
    
    # Add interaction term
    did_df['post_x_downstream'] = did_df['post'] * did_df['downstream']
    
    # Remove any rows with missing outcome
    did_df = did_df.dropna(subset=['outcome'])
    
    return did_df


def calculate_2x2_table(windowed_df: pd.DataFrame,
                       upstream_col: str,
                       downstream_col: str) -> Dict:
    """Calculate the 2x2 comparison table.
    
    Returns means for:
              PRE        POST
    UPSTREAM  A          B
    DOWNSTREAM C         D
    
    DiD = (D - C) - (B - A)
    
    Args:
        windowed_df: Event window data with pre/post indicator
        upstream_col: Upstream column name
        downstream_col: Downstream column name
        
    Returns:
        Dictionary with 2x2 table values and DiD estimate
    """
    pre_data = windowed_df[windowed_df['time_period'] == 'pre']
    post_data = windowed_df[windowed_df['time_period'] == 'post']
    
    if len(pre_data) == 0 or len(post_data) == 0:
        return {}
    
    # 2x2 means
    upstream_pre = pre_data[upstream_col].mean()  # A
    upstream_post = post_data[upstream_col].mean()  # B
    downstream_pre = pre_data[downstream_col].mean()  # C
    downstream_post = post_data[downstream_col].mean()  # D
    
    # DiD calculation
    upstream_change = upstream_post - upstream_pre
    downstream_change = downstream_post - downstream_pre
    did_estimate = downstream_change - upstream_change
    
    return {
        'upstream_pre': upstream_pre,
        'upstream_post': upstream_post,
        'downstream_pre': downstream_pre,
        'downstream_post': downstream_post,
        'upstream_change': upstream_change,
        'downstream_change': downstream_change,
        'did_estimate': did_estimate,
        'n_pre': len(pre_data),
        'n_post': len(post_data),
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))
    
    logging.basicConfig(level=logging.INFO)
    
    print("Event window module ready for testing")
