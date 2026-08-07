"""Data cleaning and quality control module.

Implements transparent preprocessing with full documentation of removed observations.
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DataQualityReport:
    """Track data quality metrics and removal reasons."""
    
    def __init__(self, station: str, outcome: str):
        self.station = station
        self.outcome = outcome
        self.original_count = 0
        self.removals = []
        self.final_count = 0
    
    def log_removal(self, count: int, reason: str):
        """Log a removal event."""
        self.removals.append({"count": count, "reason": reason})
        logger.info(f"{self.station} ({self.outcome}): Removed {count} observations - {reason}")
    
    def summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        total_removed = sum(r["count"] for r in self.removals)
        return {
            "station": self.station,
            "outcome": self.outcome,
            "original": self.original_count,
            "total_removed": total_removed,
            "final": self.final_count,
            "retention_rate": (self.final_count / self.original_count * 100) if self.original_count > 0 else 0,
            "removals": self.removals
        }


def clean_temperature_data(df: pd.DataFrame, station: str) -> Tuple[pd.DataFrame, DataQualityReport]:
    """Clean temperature data with validation.
    
    Checks:
    - Date format and parsing
    - Missing values
    - Impossible values (typically -10 to 35°C for river water)
    - Extreme outliers (>30°C or <-5°C for most German rivers)
    
    Args:
        df: Raw temperature DataFrame
        station: Station name for reporting
        
    Returns:
        Tuple of (cleaned DataFrame, quality report)
    """
    report = DataQualityReport(station, "temperature")
    report.original_count = len(df)
    
    df = df.copy()
    
    # Ensure date is datetime
    if df['date'].dtype != 'datetime64[ns]':
        df['date'] = pd.to_datetime(df['date'])
    
    # Remove duplicates by date (keep first)
    before = len(df)
    df = df.drop_duplicates(subset=['date'], keep='first')
    if len(df) < before:
        report.log_removal(before - len(df), "Duplicate dates removed")
    
    # Remove rows with missing temperature values
    before = len(df)
    df = df.dropna(subset=['temperature_mean'])
    if len(df) < before:
        report.log_removal(before - len(df), "Missing temperature values")
    
    # Check for impossible values (outside -10 to 35°C range)
    before = len(df)
    df = df[(df['temperature_mean'] >= -10) & (df['temperature_mean'] <= 35)]
    if len(df) < before:
        report.log_removal(before - len(df), "Impossible values (< -10°C or > 35°C)")
    
    # Flag extreme values for inspection (>25°C or <0°C)
    extreme_high = (df['temperature_mean'] > 25).sum()
    extreme_low = (df['temperature_mean'] < 0).sum()
    
    if extreme_high > 0 or extreme_low > 0:
        logger.warning(f"{station}: {extreme_high} observations > 25°C, {extreme_low} observations < 0°C")
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    report.final_count = len(df)
    return df, report


def clean_oxygen_data(df: pd.DataFrame, station: str) -> Tuple[pd.DataFrame, DataQualityReport]:
    """Clean oxygen data with validation.
    
    Checks:
    - Date format and parsing
    - Missing values
    - Unit consistency
    - Reasonable ranges (typically 0-15 mg/L for river water)
    - Extreme values (>20 mg/L or negative)
    
    Args:
        df: Raw oxygen DataFrame
        station: Station name for reporting
        
    Returns:
        Tuple of (cleaned DataFrame, quality report)
    """
    report = DataQualityReport(station, "oxygen")
    report.original_count = len(df)
    
    df = df.copy()
    
    # Ensure date is datetime
    if df['date'].dtype != 'datetime64[ns]':
        df['date'] = pd.to_datetime(df['date'])
    
    # Check unit consistency
    if 'unit' in df.columns:
        units = df['unit'].unique()
        if len(units) > 1:
            logger.warning(f"{station}: Multiple units found: {units}. Keeping only mg/L")
            df = df[df['unit'] == 'mg/l']
    
    # Remove duplicates by date (keep first)
    before = len(df)
    df = df.drop_duplicates(subset=['date'], keep='first')
    if len(df) < before:
        report.log_removal(before - len(df), "Duplicate dates removed")
    
    # Remove rows with missing oxygen values
    before = len(df)
    df = df.dropna(subset=['oxygen_mean'])
    if len(df) < before:
        report.log_removal(before - len(df), "Missing oxygen values")
    
    # Remove negative or impossible values (oxygen shouldn't be negative)
    before = len(df)
    df = df[df['oxygen_mean'] >= 0]
    if len(df) < before:
        report.log_removal(before - len(df), "Negative oxygen values")
    
    # Flag extreme high values (>20 mg/L is unusual)
    extreme_high = (df['oxygen_mean'] > 20).sum()
    if extreme_high > 0:
        logger.warning(f"{station}: {extreme_high} observations > 20 mg/L")
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    report.final_count = len(df)
    return df, report


def detect_temporal_gaps(df: pd.DataFrame, station: str, outcome: str, 
                        max_gap_days: int = 365) -> None:
    """Detect and log temporal gaps in the data.
    
    Args:
        df: Cleaned data with 'date' column
        station: Station name
        outcome: Outcome type
        max_gap_days: Threshold for flagging a gap
    """
    if len(df) < 2:
        return
    
    df = df.sort_values('date')
    gaps = df['date'].diff().dt.days
    
    large_gaps = gaps[gaps > max_gap_days]
    if len(large_gaps) > 0:
        logger.warning(f"{station} ({outcome}): Found {len(large_gaps)} gaps > {max_gap_days} days")
        for idx, gap in large_gaps.items():
            logger.warning(f"  Gap on {df.loc[idx, 'date']}: {gap} days")


def get_coverage_summary(df: pd.DataFrame, station: str, outcome: str) -> Dict[str, Any]:
    """Get data coverage summary.
    
    Args:
        df: Cleaned data
        station: Station name
        outcome: Outcome type
        
    Returns:
        Dictionary with coverage statistics
    """
    if len(df) == 0:
        return {
            "station": station,
            "outcome": outcome,
            "total_obs": 0,
            "date_range": None,
            "years_covered": 0,
            "coverage_pct": 0
        }
    
    date_range = (df['date'].min(), df['date'].max())
    span_days = (date_range[1] - date_range[0]).days
    span_years = span_days / 365.25
    
    # Calculate daily coverage percentage
    date_range_full = pd.date_range(date_range[0], date_range[1], freq='D')
    coverage_pct = len(df) / len(date_range_full) * 100
    
    return {
        "station": station,
        "outcome": outcome,
        "total_obs": len(df),
        "date_range_start": date_range[0],
        "date_range_end": date_range[1],
        "span_years": round(span_years, 2),
        "daily_coverage_pct": round(coverage_pct, 1),
    }


if __name__ == "__main__":
    from data_loading import load_temperature_file, load_oxygen_file
    from config import DATA_DIR
    
    logging.basicConfig(level=logging.INFO, 
                       format='%(levelname)s: %(message)s')
    
    # Test cleaning
    print("Testing data cleaning...")
    
    test_temp = DATA_DIR / "Landshut_Birket_2011-5_C.csv"
    temp_df = load_temperature_file(test_temp)
    if temp_df is not None:
        clean_df, report = clean_temperature_data(temp_df, "Landshut-Birket")
        print(f"Temperature: {report.summary()}")
        coverage = get_coverage_summary(clean_df, "Landshut-Birket", "temperature")
        print(f"Coverage: {coverage}")
