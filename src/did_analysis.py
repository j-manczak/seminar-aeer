"""Difference-in-Differences regression analysis.

Implements 2x2 DiD model with statistical inference.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional, Tuple

# Lazy import to avoid slow import time
smf = None

logger = logging.getLogger(__name__)


class DiDResult:
    """Container for DiD regression results."""
    
    def __init__(self, observation_id: int, plant: str, outcome: str, 
                 window_years: int, regression=None):
        self.observation_id = observation_id
        self.plant = plant
        self.outcome = outcome
        self.window_years = window_years
        self.regression = regression
        self.did_coefficient = None
        self.std_error = None
        self.p_value = None
        self.conf_int_lower = None
        self.conf_int_upper = None
        self.t_stat = None
        self.n_obs = None
        self.r_squared = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'observation_id': self.observation_id,
            'plant': self.plant,
            'outcome': self.outcome,
            'window_years': self.window_years,
            'did_coefficient': self.did_coefficient,
            'std_error': self.std_error,
            'p_value': self.p_value,
            'ci_lower': self.conf_int_lower,
            'ci_upper': self.conf_int_upper,
            't_stat': self.t_stat,
            'n_observations': self.n_obs,
            'r_squared': self.r_squared,
        }


def run_2x2_did_regression(did_data: pd.DataFrame, 
                          include_month_fe: bool = True) -> Optional[DiDResult]:
    """Run 2x2 DiD regression.
    
    Model: Y = β₀ + β₁(Post) + β₂(Downstream) + β₃(Post×Downstream) + ε
    
    where:
    - Post = 1 after shutdown, 0 before
    - Downstream = 1 for downstream station, 0 for upstream
    - Post×Downstream = the DiD coefficient (treatment effect)
    
    Args:
        did_data: Long-format data prepared by prepare_did_data()
        include_month_fe: Whether to include month fixed effects
        
    Returns:
        DiDResult object with regression results
    """
    global smf
    if smf is None:
        import statsmodels.formula.api as sm
        smf = sm
    
    if len(did_data) == 0:
        logger.warning("Empty data for DiD regression")
        return None
    
    # Remove any remaining NaNs
    did_data = did_data.dropna(subset=['outcome', 'post', 'downstream'])
    
    if len(did_data) < 4:
        logger.warning(f"Too few observations ({len(did_data)}) for regression")
        return None
    
    try:
        if include_month_fe:
            # Include month fixed effects to control for seasonality
            formula = 'outcome ~ C(month) + post + downstream + post:downstream'
        else:
            # Simple specification without controls
            formula = 'outcome ~ post + downstream + post:downstream'
        
        model = smf.ols(formula, data=did_data)
        result = model.fit()
        
        return result
    
    except Exception as e:
        logger.error(f"Error in DiD regression: {e}")
        return None


def extract_did_coefficient(regression_result) -> DiDResult:
    """Extract DiD coefficient and statistics from regression result.
    
    Args:
        regression_result: statsmodels regression result
        
    Returns:
        DiDResult object
    """
    did_result = DiDResult(
        observation_id=-1, 
        plant='', 
        outcome='',
        window_years=-1,
        regression=regression_result
    )
    
    try:
        # Get the post:downstream coefficient (the DiD)
        coef_name = 'post:downstream'
        
        if coef_name in regression_result.params.index:
            did_result.did_coefficient = regression_result.params[coef_name]
            did_result.std_error = regression_result.bse[coef_name]
            did_result.p_value = regression_result.pvalues[coef_name]
            did_result.t_stat = regression_result.tvalues[coef_name]
            
            # Confidence interval
            conf_int = regression_result.conf_int().loc[coef_name]
            did_result.conf_int_lower = conf_int[0]
            did_result.conf_int_upper = conf_int[1]
        else:
            logger.warning(f"DiD coefficient '{coef_name}' not found in results")
            return None
        
        did_result.n_obs = regression_result.nobs
        did_result.r_squared = regression_result.rsquared
        
    except Exception as e:
        logger.error(f"Error extracting DiD coefficient: {e}")
        return None
    
    return did_result


def run_observation_did(observation: Dict, monthly_data: pd.DataFrame,
                       outcome: str, window_years: int = 5,
                       include_month_fe: bool = True) -> Optional[DiDResult]:
    """Run DiD analysis for a single observation.
    
    Args:
        observation: Observation dict from config
        monthly_data: Monthly aggregated data
        outcome: 'temperature' or 'oxygen'
        window_years: Event window length
        include_month_fe: Include month fixed effects
        
    Returns:
        DiDResult object
    """
    from event_windows import create_event_window, prepare_did_data
    
    # Filter data for this observation's station pair
    obs_data = monthly_data[
        (monthly_data['upstream_station'] == observation['upstream_station']) &
        (monthly_data['downstream_station'] == observation['downstream_station'])
    ].copy()
    
    if len(obs_data) == 0:
        logger.warning(f"No data found for {observation['plant']}")
        return None
    
    # Create event window
    windowed, window_info = create_event_window(obs_data, observation['shutdown_date'], 
                                               window_years)
    
    if not window_info.get('has_complete_window', False):
        logger.warning(f"Incomplete window for {observation['plant']}")
        return None
    
    # Prepare for DiD regression
    if outcome == 'temperature':
        upstream_col = f"{observation['upstream_station']}_mean"
        downstream_col = f"{observation['downstream_station']}_mean"
    else:
        upstream_col = f"{observation['upstream_station']}_mean"
        downstream_col = f"{observation['downstream_station']}_mean"
    
    did_data = prepare_did_data(windowed, upstream_col, downstream_col)
    
    # Run regression
    regression_result = run_2x2_did_regression(did_data, include_month_fe)
    
    if regression_result is None:
        return None
    
    # Extract results
    did_result = extract_did_coefficient(regression_result)
    
    if did_result is None:
        return None
    
    # Fill in metadata
    did_result.observation_id = observation['obs_id']
    did_result.plant = observation['plant']
    did_result.outcome = outcome
    did_result.window_years = window_years
    
    return did_result


def print_regression_summary(did_result: DiDResult) -> None:
    """Print a summary of DiD results.
    
    Args:
        did_result: DiDResult object
    """
    if did_result.did_coefficient is None:
        logger.warning("No valid DiD results to print")
        return
    
    sig = "***" if did_result.p_value < 0.01 else ("**" if did_result.p_value < 0.05 
                                                   else ("*" if did_result.p_value < 0.10 else ""))
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Obs {did_result.observation_id}: {did_result.plant} ({did_result.outcome})")
    logger.info(f"Window: {did_result.window_years} years | N = {did_result.n_obs}")
    logger.info(f"-"*70)
    logger.info(f"DiD Coefficient: {did_result.did_coefficient:.4f} {sig}")
    logger.info(f"Std. Error:      {did_result.std_error:.4f}")
    logger.info(f"t-statistic:     {did_result.t_stat:.4f}")
    logger.info(f"p-value:         {did_result.p_value:.4f}")
    logger.info(f"95% CI:          [{did_result.conf_int_lower:.4f}, {did_result.conf_int_upper:.4f}]")
    logger.info(f"R-squared:       {did_result.r_squared:.4f}")
    logger.info(f"{'='*70}\n")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("DiD analysis module ready")
