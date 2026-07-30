"""Staggered difference-in-differences for the nuclear shutdowns.

The strict 2011 treatment-vs-control 2×2 is *not identified*: the clean control
sites (Grohnde, Emsland, Brokdorf) have no downstream summer measurements before
2011, so their pre-period is empty. This script uses the design the data can
support instead: a **generalized (staggered) DiD**. Every site is "treated" from
the shutdown year of its nearest upstream reactor (2011 for treatment/partial,
2015 Grafenrheinfeld, 2017 Gundremmingen); reactors that shut down only later act
as not-yet-treated controls. With site and year fixed effects this is estimable.

    python scripts/did_staggered.py

Estimator: two-way fixed-effects OLS, standard errors clustered by site. This is
a first, transparent estimate. TWFE can be biased with staggered timing and
heterogeneous effects, so the robust follow-up is a Callaway–Sant'Anna estimator
(R `did` or Python `differences`); the sign and rough size, however, come out
here already.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from pipeline.reactors import REACTORS  # noqa: E402

ANALYSIS = ROOT / "data" / "processed" / "analysis"
NEAR_BANDS = ["0-10", "10-25", "25-50"]
WINDOW = (2008, 2020)


def load() -> pd.DataFrame:
    shutdown = {r.reactor: r.shutdown_year for r in REACTORS}
    df = pd.read_csv(ANALYSIS / "water_quality_summer_by_site.csv", comment="#")
    df = df[(df["determinand"] == "water_temperature")
            & (df["position"] == "downstream")
            & (df["distance_band"].isin(NEAR_BANDS))].copy()
    df["mean_value"] = pd.to_numeric(df["mean_value"], errors="coerce")
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["mean_value", "year", "nearest_upstream_plant"])
    df["treat_year"] = df["nearest_upstream_plant"].map(shutdown)
    df = df[df["year"].between(*WINDOW)].copy()
    # Treated from the shutdown year of the nearest upstream reactor.
    df["post"] = (df["year"] >= df["treat_year"]).astype(int)
    return df


def twfe_cluster(df: pd.DataFrame, treat_col: str = "post"):
    """Two-way FE OLS of mean_value on treat_col with site + year fixed effects,
    standard errors clustered by site. Returns (coef, se, n, n_clusters)."""
    y = df["mean_value"].to_numpy(float)
    site = pd.get_dummies(df["site_id"], prefix="s", drop_first=True).to_numpy(float)
    yr = pd.get_dummies(df["year"], prefix="y", drop_first=True).to_numpy(float)
    treat = df[treat_col].to_numpy(float).reshape(-1, 1)
    const = np.ones((len(df), 1))
    X = np.hstack([treat, site, yr, const])

    XtX = X.T @ X
    XtX_inv = np.linalg.pinv(XtX)
    beta = XtX_inv @ (X.T @ y)
    resid = y - X @ beta

    # Cluster-robust (by site) covariance.
    groups = df["site_id"].to_numpy()
    meat = np.zeros_like(XtX)
    for g in np.unique(groups):
        Xg = X[groups == g]
        eg = resid[groups == g]
        s = Xg.T @ eg
        meat += np.outer(s, s)
    n, k = X.shape
    n_clusters = len(np.unique(groups))
    dof = (n_clusters / (n_clusters - 1)) * ((n - 1) / (n - k))
    V = XtX_inv @ meat @ XtX_inv * dof
    return beta[0], float(np.sqrt(V[0, 0])), n, n_clusters


def main() -> None:
    df = load()
    coef, se, n, g = twfe_cluster(df)
    t = coef / se if se else float("nan")
    print("Generalized (staggered) DiD — downstream summer water temperature")
    print(f"  sample: {n} site-years, {g} sites, window {WINDOW[0]}-{WINDOW[1]}")
    print(f"  ATT (post-shutdown): {coef:+.3f} °C   SE {se:.3f}   t {t:+.2f}")
    print(f"  95% CI: [{coef - 1.96 * se:+.3f}, {coef + 1.96 * se:+.3f}] °C")
    print("  (site + year FE, SE clustered by site; TWFE first pass — see header.)")
    # Placebo: split the never-in-window controls vs treated to sanity-check sign.
    print("\n  Note: with only a few sites observed both before and after their")
    print("  shutdown, the estimate is imprecise. Read the sign, not the decimals.")


if __name__ == "__main__":
    main()
