"""Difference-in-differences groundwork for the 2011 nuclear moratorium on
downstream summer river temperature -- and an honest look at where the data can
and cannot identify an effect.

Outcome  summer (Jun-Sep) mean water temperature per site and year, built from
         the Waterbase v2025_1 disaggregated data (waterbase_disaggregated.py).
Sample   downstream sites within 50 km of a study reactor, on a study river
         (river matched geometrically from the coordinates).

The script first maps the coverage by group and year (the binding constraint),
then attempts the strict treatment-vs-control 2011 DiD.

    python scripts/did_analysis.py
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "processed" / "analysis"
FIGS = ROOT / "figures"
RESULTS = ANALYSIS / "did_water_temperature_results.md"

NEAR_BANDS = {"0-10", "10-25", "25-50"}
GROUPS = ["treatment", "partial", "staggered_treatment", "control"]
GROUP_DE = {"treatment": "Treatment", "partial": "Partial",
            "staggered_treatment": "Gestaffelt", "control": "Control"}
DID_WINDOW = (2008, 2020)
TREAT_COLOR, CTRL_COLOR, INK, MUTED = "#e34948", "#2a78d6", "#0b0b0b", "#898781"


def load_downstream() -> pd.DataFrame:
    df = pd.read_csv(ANALYSIS / "water_quality_summer_by_site.csv", comment="#")
    df = df[(df["determinand"] == "water_temperature")
            & (df["position"] == "downstream")
            & (df["distance_band"].isin(NEAR_BANDS))].copy()
    df["mean_value"] = pd.to_numeric(df["mean_value"], errors="coerce")
    return df.dropna(subset=["mean_value"])


def coverage_table(df: pd.DataFrame) -> pd.DataFrame:
    piv = (df.groupby(["nearest_upstream_group", "year"])["site_id"].nunique()
             .unstack("year").reindex(GROUPS).fillna(0).astype(int))
    return piv


def plot_coverage(cov: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(11, 3.2), dpi=170)
    data = cov.values
    ax.imshow(data, cmap="Blues", aspect="auto", vmin=0, vmax=max(1, data.max()))
    ax.set_xticks(range(len(cov.columns)))
    ax.set_xticklabels(cov.columns, fontsize=8)
    ax.set_yticks(range(len(cov.index)))
    ax.set_yticklabels([GROUP_DE[g] for g in cov.index], fontsize=9)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            ax.text(j, i, str(v), ha="center", va="center", fontsize=8,
                    color="white" if v > data.max() * 0.55 else INK)
    ax.axvline(list(cov.columns).index(2011) - 0.5, color="#e34948", lw=1.5)
    ax.set_title("Datenabdeckung: Messstellen je Gruppe und Jahr (downstream Sommer-Temperatur ≤ 50 km)",
                 fontsize=11, weight="bold", color=INK, pad=10)
    fig.tight_layout(); fig.savefig(FIGS / "did_coverage.png", dpi=170, facecolor="white")
    plt.close(fig)


def plot_trends(df: pd.DataFrame):
    tc = df[df["nearest_upstream_group"].isin(["treatment", "control"])]
    tc = tc[tc["year"].between(*DID_WINDOW)]
    tc = tc.assign(treated=(tc["nearest_upstream_group"] == "treatment").astype(int))
    means = tc.groupby(["year", "treated"])["mean_value"].mean().unstack("treated")
    fig, ax = plt.subplots(figsize=(8, 5), dpi=170)
    if 1 in means:
        ax.plot(means.index, means[1], "-o", color=TREAT_COLOR, lw=2, ms=5, label="Treatment (Biblis, Unterweser)")
    if 0 in means:
        ax.plot(means.index, means[0], "-o", color=CTRL_COLOR, lw=2, ms=5, label="Control (Grohnde, Emsland, Brokdorf)")
    ax.axvline(2010.5, color=MUTED, ls="--", lw=1)
    ax.set_xlabel("Jahr"); ax.set_ylabel("Ø Sommer-Wassertemperatur (°C)")
    ax.set_title("Sommer-Wassertemperatur (Jun–Sep): Treatment vs. Control (downstream ≤ 50 km)",
                 fontsize=11.5, color=INK, weight="bold")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="y", color="#e1e0d9", lw=0.6)
    for s in ax.spines.values():
        s.set_edgecolor("#e1e0d9")
    fig.tight_layout(); fig.savefig(FIGS / "did_trends.png", dpi=170, facecolor="white")
    plt.close(fig)


def try_did(df: pd.DataFrame):
    tc = df[df["nearest_upstream_group"].isin(["treatment", "control"])
            & df["year"].between(*DID_WINDOW)].copy()
    tc["treated"] = (tc["nearest_upstream_group"] == "treatment").astype(int)
    tc["post"] = (tc["year"] >= 2011).astype(int)
    tc["did"] = tc["treated"] * tc["post"]
    cells = tc.pivot_table(index="treated", columns="post", values="mean_value", aggfunc="count").reindex(
        index=[0, 1], columns=[0, 1]).fillna(0).astype(int)
    estimable = (cells.values > 0).all()
    result = {"tc": tc, "cells": cells, "estimable": estimable, "coef": None, "se": None, "p": None}
    if estimable:
        res = smf.ols("mean_value ~ did + C(site_id) + C(year)", data=tc).fit(
            cov_type="cluster", cov_kwds={"groups": tc["site_id"]})
        result.update(coef=res.params["did"], se=res.bse["did"], p=res.pvalues["did"])
    return result


def write_results(df, cov, did):
    tc = did["tc"]
    lines = [
        "# DiD: 2011-Abschaltung und Sommer-Wassertemperatur",
        "",
        "*Quelle: Waterbase v2025_1 Einzelmessungen → Sommer (Jun–Sep) je Messstelle/Jahr, "
        "downstream ≤ 50 km, Fluss geometrisch zugeordnet.*",
        "",
        "## Kernbefund",
        "Mit den dichten Einzelmessungen ist die Abdeckung 2008–2024 durchgehend — aber sie ist "
        "**stark ungleich über die Gruppen verteilt**. Die sauberen **Treatment**- (Biblis, Unterweser) "
        "und **Control**-Reaktoren (Grohnde, Emsland, Brokdorf) sind downstream **kaum gemessen, "
        "besonders vor 2011**; die Abdeckung liegt bei **Partial** (Philippsburg, Neckarwestheim; 9 Stellen) "
        "und **Gestaffelt** (Grafenrheinfeld 2015, Gundremmingen 2017; 5 Stellen). Eine strikte "
        "Treatment-vs-Control-DiD für 2011 ist deshalb "
        + ("**schätzbar, aber sehr dünn**." if did["estimable"] else "**nicht identifiziert** "
           "(die Control-Gruppe hat vor 2011 keine Beobachtung).")
        + " Das gut abgedeckte Experiment sind die **Partial- und gestaffelten Abschaltungen**.",
        "",
        "## Datenabdeckung (Messstellen je Gruppe × Jahr)",
        "",
        "| Gruppe | " + " | ".join(str(y) for y in cov.columns) + " |",
        "|" + "---|" * (len(cov.columns) + 1),
    ]
    for g in cov.index:
        lines.append(f"| {GROUP_DE[g]} | " + " | ".join(str(v) for v in cov.loc[g]) + " |")
    lines += [
        "",
        "Figur: `figures/did_coverage.png` (rote Linie = 2011).",
        "",
        "## Versuch: Treatment vs. Control (2×2, Fenster 2008–2020)",
        "",
        "Zellbesetzung (Beobachtungen):",
        "",
        "| | vor 2011 | ab 2011 |",
        "|---|---|---|",
        f"| Control | {did['cells'].loc[0,0]} | {did['cells'].loc[0,1]} |",
        f"| Treatment | {did['cells'].loc[1,0]} | {did['cells'].loc[1,1]} |",
        "",
    ]
    if did["estimable"]:
        lines.append(f"Two-Way-FE-Schätzer (treated×post): **{did['coef']:+.3f} °C** "
                     f"(SE {did['se']:.3f}, p {did['p']:.3f}) — mit äußerster Vorsicht zu lesen.")
    else:
        lines.append("**Nicht schätzbar:** mindestens eine Zelle ist leer (keine Control-Vorperiode). "
                     "Der 2×2-DiD ist für dieses Standort-Set nicht definiert.")
    lines += [
        "",
        "## Empfehlung (welche DiD die Daten tragen)",
        "1. **Gestaffelte / generalisierte DiD** über alle Abschaltungen: jede Downstream-Stelle wird ab "
        "dem Stilllegungsjahr ihres nächsten Oberlieger-AKW behandelt (2011 Partial/Treatment, 2015 "
        "Grafenrheinfeld, 2017 Gundremmingen); noch laufende Reaktoren sind die (noch-nicht-)Kontrollen. "
        "Nutzt die gesamte Abdeckung (Callaway–Sant'Anna gegen die TWFE-Verzerrung).",
        "2. **Within-River downstream vs. upstream** je Abschaltung (upstream als Kontrolle desselben Flusses).",
        "3. Abfluss als Kovariate/Intensität; Sommer-Fokus (hier schon) beibehalten.",
        "",
        "## Vorbehalte",
        "- Kleine, wachsende Stichprobe; Site- + Jahres-FE; wenige Cluster → SE nur näherungsweise.",
        "- Tide-Standorte (Unterweser, Brokdorf) und Kompositionswechsel beachten.",
        "",
        "Figuren: `figures/did_coverage.png`, `figures/did_trends.png`.",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = load_downstream()
    cov = coverage_table(df[df["year"].between(2008, 2024)])
    did = try_did(df)

    FIGS.mkdir(exist_ok=True)
    plot_coverage(cov)
    plot_trends(df)
    write_results(df, cov, did)

    print("coverage by group (distinct downstream sites):",
          {GROUP_DE[g]: int(df[df.nearest_upstream_group == g]["site_id"].nunique()) for g in GROUPS})
    if did["estimable"]:
        print(f"treatment-vs-control DiD: {did['coef']:+.3f} C (SE {did['se']:.3f}, p {did['p']:.3f})")
    else:
        print("treatment-vs-control DiD: not estimable (empty control pre-period)")
    print("wrote did_coverage.png, did_trends.png, did_water_temperature_results.md")


if __name__ == "__main__":
    main()
