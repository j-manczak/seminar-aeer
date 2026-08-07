"""Visualization module for figures and plots."""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# Set style
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['lines.linewidth'] = 1.5
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')


def plot_time_series(monthly_data: pd.DataFrame, 
                    upstream_col: str,
                    downstream_col: str,
                    shutdown_date: datetime,
                    plant_name: str,
                    outcome: str,
                    outcome_unit: str,
                    title: Optional[str] = None,
                    figsize: Tuple = (12, 5)) -> plt.Figure:
    """Plot time series of outcome with shutdown marked.
    
    Args:
        monthly_data: DataFrame with year_month, upstream_col, downstream_col
        upstream_col: Column name for upstream station
        downstream_col: Column name for downstream station
        shutdown_date: Date of shutdown
        plant_name: Plant name for legend/title
        outcome: 'temperature' or 'oxygen'
        outcome_unit: Unit string (e.g., '°C' or 'mg/L')
        title: Optional custom title
        figsize: Figure size
        
    Returns:
        matplotlib Figure object
    """
    if len(monthly_data) == 0:
        logger.warning(f"No data to plot for {plant_name}")
        return None
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Convert year_month to datetime for x-axis
    x = pd.to_datetime(monthly_data['year_month'].astype(str))
    
    # Plot lines
    ax.plot(x, monthly_data[upstream_col], 'o-', label='Upstream', 
           color='#2E86AB', linewidth=1.5, markersize=4, alpha=0.8)
    ax.plot(x, monthly_data[downstream_col], 's-', label='Downstream', 
           color='#A23B72', linewidth=1.5, markersize=4, alpha=0.8)
    
    # Mark shutdown
    ax.axvline(shutdown_date, color='red', linestyle='--', linewidth=2, 
              label=f'Shutdown: {shutdown_date.date()}', alpha=0.7)
    
    # Format x-axis
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    # Labels and title
    ax.set_xlabel('Month-Year')
    ax.set_ylabel(f'{outcome.capitalize()} ({outcome_unit})')
    
    if title is None:
        title = f'{plant_name} - {outcome.capitalize()} Time Series'
    ax.set_title(title)
    
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_parallel_trends(monthly_data: pd.DataFrame,
                         upstream_col: str,
                         downstream_col: str,
                         shutdown_date: datetime,
                         plant_name: str,
                         outcome: str,
                         outcome_unit: str,
                         figsize: Tuple = (10, 6)) -> plt.Figure:
    """Plot pre-treatment trends to assess parallel trends assumption.
    
    Args:
        monthly_data: Full time series data
        upstream_col: Upstream column
        downstream_col: Downstream column
        shutdown_date: Shutdown date
        plant_name: Plant name
        outcome: Outcome type
        outcome_unit: Unit
        figsize: Figure size
        
    Returns:
        matplotlib Figure
    """
    if len(monthly_data) == 0:
        return None
    
    # Filter to pre-treatment
    pre_data = monthly_data[
        pd.to_datetime(monthly_data['year_month'].astype(str)) < shutdown_date
    ].copy()
    
    if len(pre_data) < 2:
        logger.warning(f"Not enough pre-treatment data for {plant_name}")
        return None
    
    fig, ax = plt.subplots(figsize=figsize)
    
    x = pd.to_datetime(pre_data['year_month'].astype(str))
    
    # Plot with trend lines
    ax.plot(x, pre_data[upstream_col], 'o-', label='Upstream', 
           color='#2E86AB', alpha=0.6)
    ax.plot(x, pre_data[downstream_col], 's-', label='Downstream',
           color='#A23B72', alpha=0.6)
    
    # Fit linear trends
    x_numeric = np.arange(len(pre_data))
    z_up = np.polyfit(x_numeric, pre_data[upstream_col].values, 1)
    z_down = np.polyfit(x_numeric, pre_data[downstream_col].values, 1)
    
    p_up = np.poly1d(z_up)
    p_down = np.poly1d(z_down)
    
    ax.plot(x, p_up(x_numeric), '--', color='#2E86AB', linewidth=2, label='Upstream trend')
    ax.plot(x, p_down(x_numeric), '--', color='#A23B72', linewidth=2, label='Downstream trend')
    
    # Format
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
    
    ax.set_xlabel('Month-Year (Pre-treatment)')
    ax.set_ylabel(f'{outcome.capitalize()} ({outcome_unit})')
    ax.set_title(f'{plant_name} - Parallel Trends (Pre-treatment)')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_did_estimates(results_list: List[Dict], outcome: str,
                      window_years: int = 5, figsize: Tuple = (10, 6)) -> plt.Figure:
    """Plot DiD estimates across multiple observations.
    
    Args:
        results_list: List of result dictionaries
        outcome: Outcome type
        window_years: Window length
        figsize: Figure size
        
    Returns:
        matplotlib Figure
    """
    if len(results_list) == 0:
        logger.warning("No results to plot")
        return None
    
    # Filter to specified window
    results = [r for r in results_list if r['window_years'] == window_years and 
               r['outcome'] == outcome]
    
    if len(results) == 0:
        logger.warning(f"No results for {outcome}, window={window_years}")
        return None
    
    # Sort by plant
    results = sorted(results, key=lambda x: x['plant'])
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Extract data
    plants = [r['plant'] for r in results]
    coefs = [r['did_coefficient'] for r in results]
    cis_lower = [r['ci_lower'] for r in results]
    cis_upper = [r['ci_upper'] for r in results]
    
    # Calculate error bars
    errors = [
        [coefs[i] - cis_lower[i] for i in range(len(coefs))],
        [cis_upper[i] - coefs[i] for i in range(len(coefs))]
    ]
    
    # Colors for significance
    colors = []
    for r in results:
        if r['p_value'] < 0.05:
            colors.append('#E63946')  # Significant: red
        else:
            colors.append('#A8DADC')  # Not significant: light
    
    # Plot
    x = np.arange(len(plants))
    ax.bar(x, coefs, color=colors, alpha=0.7, edgecolor='black')
    ax.errorbar(x, coefs, yerr=errors, fmt='none', color='black', 
               capsize=5, capthick=1.5)
    
    # Reference line at zero
    ax.axhline(0, color='black', linestyle='-', linewidth=0.8)
    
    # Labels
    ax.set_xlabel('Plant')
    ax.set_ylabel(f'DiD Estimate ({outcome})')
    ax.set_title(f'DiD Estimates Across Observations ({window_years}-year window)')
    ax.set_xticks(x)
    ax.set_xticklabels(plants, rotation=45, ha='right')
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    return fig


def plot_sensitivity_windows(results_list: List[Dict], observation_id: int,
                             outcome: str, figsize: Tuple = (10, 6)) -> plt.Figure:
    """Plot DiD sensitivity to event window length.
    
    Args:
        results_list: List of result dictionaries
        observation_id: Which observation to plot
        outcome: Outcome type
        figsize: Figure size
        
    Returns:
        matplotlib Figure
    """
    # Filter to this observation and outcome
    results = [r for r in results_list 
              if r['observation_id'] == observation_id and r['outcome'] == outcome]
    
    if len(results) < 2:
        logger.warning(f"Insufficient results for sensitivity plot (obs={observation_id}, outcome={outcome})")
        return None
    
    # Sort by window length
    results = sorted(results, key=lambda x: x['window_years'])
    
    fig, ax = plt.subplots(figsize=figsize)
    
    windows = [r['window_years'] for r in results]
    coefs = [r['did_coefficient'] for r in results]
    cis_lower = [r['ci_lower'] for r in results]
    cis_upper = [r['ci_upper'] for r in results]
    
    # Plot with error bars
    ax.errorbar(windows, coefs, 
               yerr=[np.array(coefs) - np.array(cis_lower),
                    np.array(cis_upper) - np.array(coefs)],
               fmt='o-', markersize=8, linewidth=2, capsize=5, capthick=1.5,
               color='#2E86AB', ecolor='#A23B72')
    
    # Reference line
    ax.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.5)
    
    ax.set_xlabel('Event Window (years)')
    ax.set_ylabel(f'DiD Estimate ({outcome})')
    ax.set_title(f'Sensitivity to Event Window Length - Observation {observation_id}')
    ax.set_xticks(windows)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def save_figure(fig: plt.Figure, filepath, dpi: int = 300):
    """Save figure with high quality.
    
    Args:
        fig: matplotlib Figure
        filepath: Output path
        dpi: Resolution
    """
    if fig is None:
        logger.warning(f"Cannot save None figure to {filepath}")
        return
    
    try:
        fig.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor='white')
        logger.info(f"Saved figure to {filepath}")
    except Exception as e:
        logger.error(f"Error saving figure to {filepath}: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Visualization module ready")
