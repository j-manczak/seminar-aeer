"""2011 nuclear shutdown DiD analysis module.

This package implements a focused Difference-in-Differences analysis for the
2011 German nuclear moratorium, with fallback methods for data-limited scenarios.

The 2011 shutdowns present a unique data challenge: most temperature monitoring
stations started operations after 2011, limiting pre-shutdown observations. This
module provides:

1. Primary analysis: 2×2 DiD with strict pre/post coverage requirements
2. Fallback analysis: Trend comparison using available data windows
3. Sensitivity analysis: Multiple distance thresholds and specifications

Designed to be extensible for other shutdown years with better data coverage.
"""
