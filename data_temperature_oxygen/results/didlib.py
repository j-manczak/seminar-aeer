"""Loaders and estimators for the 2011 shutdown 2x2 on `data_temperature_oxygen/`.

File naming
-----------
The letters in the file name say which parameters the file carries:

``C``  Wassertemperatur (deg C)
``P``  Pegel / Wasserstand (cm)
``O``  Sauerstoff (mg/l)

So ``*_C.csv`` is temperature only, ``*_CO.csv`` carries temperature and oxygen,
and a file with all three would be ``*_CPO.csv``. Two raw formats occur:

``*_C.csv`` / ``*_P.csv``   GKD Bayern, one station and one parameter per file,
                            header block terminated by a ``Datum;Mittelwert;...``
                            line.
``*_CO.csv``                LUBW Baden-Wuerttemberg, long format, one row per
                            station-parameter-day, ``Parameter`` in
                            {Temperatur, Sauerstoff}.

Nothing outside this folder is read. Where the folder has no data for a
parameter, the corresponding case is simply not estimated.

Design
------
Both gauges of a pair sit on the same river and are read on the same day, so the
2x2 is written as the paired daily difference

    gap_t = y_downstream,t - y_upstream,t
    gap_t = a + b * post_t + month fixed effects + e_t

``b`` is numerically the difference-in-differences estimate but takes out
weather, season and river-wide trend before estimation. Standard errors are
Newey-West (HAC) with a 30-day bandwidth, matching `scripts/plant_2x2_did.py`.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

DATA_DIR = Path(__file__).resolve().parent.parent
HAC_LAG = 30
SUMMER_MONTHS = (6, 7, 8, 9)


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=None)
def _read_raw(path: Path, kind: str) -> pd.DataFrame:
    """Read one raw file once. Several cases reuse the same gauge and file."""
    if kind == "gkd":
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith("Datum;"))
        return pd.read_csv(path, sep=";", skiprows=start, encoding="utf-8-sig", decimal=",")
    return pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)


def load_gkd(filename: str, value: str = "Mittelwert") -> pd.DataFrame:
    """Read a GKD Bayern daily file (``*_C.csv`` / ``*_P.csv``).

    Returns a frame with ``date`` and ``value``. The header block above the data
    varies in length between files, so the data start is found by the first line
    beginning with ``Datum;``.
    """
    df = _read_raw(DATA_DIR / filename, "gkd").copy()
    df["date"] = pd.to_datetime(df["Datum"], format="%Y-%m-%d", errors="coerce")
    df["value"] = pd.to_numeric(df[value], errors="coerce")
    return df.loc[df["date"].notna(), ["date", "value"]].sort_values("date").reset_index(drop=True)


def load_lubw(filename: str, parameter: str) -> pd.DataFrame:
    """Read one parameter out of a LUBW long-format file (``*_CO.csv``).

    ``parameter`` is ``Temperatur`` (deg C) or ``Sauerstoff`` (mg/l). Missing
    days are written as ``-`` and become NaN.
    """
    df = _read_raw(DATA_DIR / filename, "lubw").copy()
    df.columns = [c.strip() for c in df.columns]
    df = df[df["Parameter"].str.strip() == parameter]
    df = df.assign(
        date=pd.to_datetime(df["Datum"], format="%d.%m.%Y", errors="coerce"),
        value=pd.to_numeric(df["Tagesmittelwert"].str.replace(",", ".", regex=False), errors="coerce"),
    )
    return df.loc[df["date"].notna(), ["date", "value"]].sort_values("date").reset_index(drop=True)


def oxygen_saturation_mgl(temp_c: pd.Series) -> pd.Series:
    """Equilibrium O2 concentration of fresh water at 1 atm (Benson-Krause/APHA).

    Used to convert measured mg/l into percent of saturation. Station altitude
    would scale this by a constant factor of one to two percent; because that
    factor is constant per station it drops out of the pre/post difference, so
    it is deliberately not applied.
    """
    t_k = temp_c + 273.15
    ln_c = (
        -139.34411
        + 1.575701e5 / t_k
        - 6.642308e7 / t_k**2
        + 1.243800e10 / t_k**3
        - 8.621949e11 / t_k**4
    )
    return np.exp(ln_c)


def station_series(spec: dict, outcome: str) -> pd.DataFrame:
    """Build one station's daily series for one outcome.

    ``spec`` maps outcome keys to a file name (GKD) or a (file, parameter) pair
    (LUBW). ``o2_saturation`` is derived from the station's own oxygen and
    temperature series and therefore only exists where the file carries both.
    """
    if outcome == "o2_saturation":
        o2 = station_series(spec, "oxygen")
        temp = station_series(spec, "temperature")
        if o2.empty or temp.empty:
            return pd.DataFrame(columns=["date", "value"])
        both = o2.merge(temp, on="date", suffixes=("_o2", "_t"))
        both["value"] = 100.0 * both["value_o2"] / oxygen_saturation_mgl(both["value_t"])
        return both[["date", "value"]]

    source = spec.get(outcome)
    if source is None:
        return pd.DataFrame(columns=["date", "value"])
    if isinstance(source, tuple):
        return load_lubw(*source)
    return load_gkd(source, value="Mittelwert")


# --------------------------------------------------------------------------- #
# estimation
# --------------------------------------------------------------------------- #
def build_panel(up: pd.DataFrame, down: pd.DataFrame, start, end) -> pd.DataFrame:
    """Inner-join the two gauges on the day and cut to the study window."""
    panel = up.merge(down, on="date", suffixes=("_up", "_down"))
    panel = panel[(panel["date"] >= start) & (panel["date"] <= end)].copy()
    panel = panel.dropna(subset=["value_up", "value_down"])
    panel["gap"] = panel["value_down"] - panel["value_up"]
    panel["month"] = panel["date"].dt.month
    return panel.sort_values("date").reset_index(drop=True)


def _design(panel: pd.DataFrame, cut, month_fe: bool, controls=None) -> tuple[pd.DataFrame, pd.Series]:
    x = pd.DataFrame(index=panel.index)
    x["post"] = (panel["date"] >= cut).astype(float)
    if month_fe:
        dummies = pd.get_dummies(panel["month"], prefix="m", drop_first=True, dtype=float)
        x = x.join(dummies)
    for name in controls or []:
        x[name] = panel[name].astype(float)
    return sm.add_constant(x, has_constant="add"), panel["gap"]


def paired_did(
    panel: pd.DataFrame,
    cut,
    month_fe: bool = True,
    controls=None,
    hac_lag: int = HAC_LAG,
    min_cell: int = 30,
) -> dict:
    """Estimate ``gap_t = a + b*post_t + month FE`` with Newey-West errors.

    Also returns the raw 2x2 cell means on the same balanced sample, so the
    regression estimate and the textbook 2x2 can be read side by side.
    """
    panel = panel.dropna(subset=(["gap"] + list(controls or [])))
    pre, post = panel[panel["date"] < cut], panel[panel["date"] >= cut]
    out = {
        "n": len(panel),
        "n_pre": len(pre),
        "n_post": len(post),
        "first_day": panel["date"].min(),
        "last_day": panel["date"].max(),
        "up_pre": pre["value_up"].mean(),
        "up_post": post["value_up"].mean(),
        "down_pre": pre["value_down"].mean(),
        "down_post": post["value_down"].mean(),
        "gap_pre": pre["gap"].mean(),
        "gap_post": post["gap"].mean(),
    }
    out["up_change"] = out["up_post"] - out["up_pre"]
    out["down_change"] = out["down_post"] - out["down_pre"]
    out["did_raw"] = out["gap_post"] - out["gap_pre"]

    if len(pre) < min_cell or len(post) < min_cell:
        out.update(did=np.nan, se=np.nan, t=np.nan, p=np.nan, ci_lo=np.nan, ci_hi=np.nan)
        return out

    x, y = _design(panel, cut, month_fe, controls)
    fit = sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lag})
    ci = fit.conf_int().loc["post"]
    out.update(
        did=fit.params["post"],
        se=fit.bse["post"],
        t=fit.tvalues["post"],
        p=fit.pvalues["post"],
        ci_lo=ci[0],
        ci_hi=ci[1],
        r2=fit.rsquared,
    )
    return out


def event_study(panel: pd.DataFrame, cut, hac_lag: int = HAC_LAG, min_obs: int = 60) -> pd.DataFrame:
    """Year-bin event study around ``cut``, reference bin -1 (last pre year).

    Bin ``k`` collects the days ``[cut + 365.25*k, cut + 365.25*(k+1))``, so bin
    0 is the first year after the shutdown and bin -1 the last year before it.
    ``gap_mean`` is the raw bin mean, which is what the figures plot — the
    coefficients are only readable against a reference year, the levels are not.
    """
    panel = panel.copy()
    panel["rel"] = np.floor((panel["date"] - cut).dt.days / 365.25).astype(int)
    counts = panel["rel"].value_counts()
    keep = sorted(k for k in counts.index if counts[k] >= min_obs)
    panel = panel[panel["rel"].isin(keep)]
    if -1 not in keep or len(keep) < 3:
        return pd.DataFrame()
    bin_mean = panel.groupby("rel")["gap"].mean()

    dummies = pd.get_dummies(panel["rel"], prefix="k", dtype=float).drop(columns=["k_-1"])
    months = pd.get_dummies(panel["month"], prefix="m", drop_first=True, dtype=float)
    x = sm.add_constant(dummies.join(months), has_constant="add")
    fit = sm.OLS(panel["gap"], x).fit(cov_type="HAC", cov_kwds={"maxlags": hac_lag})

    rows = [{"rel_year": -1, "coef": 0.0, "se": 0.0, "ci_lo": 0.0, "ci_hi": 0.0,
             "gap_mean": bin_mean[-1], "n": int((panel["rel"] == -1).sum()), "reference": True}]
    for k in keep:
        if k == -1:
            continue
        name = f"k_{k}"
        ci = fit.conf_int().loc[name]
        rows.append({"rel_year": k, "coef": fit.params[name], "se": fit.bse[name],
                     "ci_lo": ci[0], "ci_hi": ci[1], "gap_mean": bin_mean[k],
                     "n": int((panel["rel"] == k).sum()), "reference": False})
    return pd.DataFrame(rows).sort_values("rel_year").reset_index(drop=True)
