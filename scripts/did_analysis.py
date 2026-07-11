"""First difference-in-differences analysis of the 2011 nuclear moratorium on
downstream river water temperature: treatment vs control only.

Design
------
Outcome  annual mean water temperature at a monitoring site (EEA Waterbase).
Sample   downstream sites within 50 km of a study reactor, on a study river,
         whose nearest upstream reactor is a treatment or a control plant
         (partial and staggered reactors are left out of this first pass).
Treated  nearest upstream reactor was fully shut down in 2011 (Biblis, Unterweser)
         -> its cooling load was removed.
Post     year >= 2011.
Model    two-way fixed effects: temp ~ treated*post + site FE + year FE,
         standard errors clustered by site. An event study replaces post with
         year dummies interacted with treated (reference year 2010).

The sample is small, so the results are exploratory; see the caveats block.

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
REFERENCE_YEAR = 2010
TREAT_COLOR, CTRL_COLOR = "#e34948", "#2a78d6"
INK, MUTED = "#0b0b0b", "#898781"


def load_panel() -> pd.DataFrame:
    df = pd.read_csv(ANALYSIS / "water_temperature_2006_2018.csv", comment="#")
    df = df[(df["position"] == "downstream")
            & (df["distance_band"].isin(NEAR_BANDS))
            & (df["nearest_upstream_group"].isin(["treatment", "control"]))].copy()
    df["treated"] = (df["nearest_upstream_group"] == "treatment").astype(int)
    df["post"] = (df["year"] >= 2011).astype(int)
    df["did"] = df["treated"] * df["post"]
    df["mean_value"] = pd.to_numeric(df["mean_value"], errors="coerce")
    return df.dropna(subset=["mean_value"])


def two_by_two(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot_table(index="treated", columns="post", values="mean_value", aggfunc="mean")


def fit_did(df: pd.DataFrame):
    model = smf.ols("mean_value ~ did + C(site_id) + C(year)", data=df)
    return model.fit(cov_type="cluster", cov_kwds={"groups": df["site_id"]})


def fit_event_study(df: pd.DataFrame):
    df = df.copy()
    years = sorted(y for y in df["year"].unique() if y != REFERENCE_YEAR)
    terms = []
    for y in years:
        col = f"tx_{y}"
        df[col] = df["treated"] * (df["year"] == y).astype(int)
        terms.append(col)
    formula = "mean_value ~ " + " + ".join(terms) + " + C(site_id) + C(year)"
    res = smf.ols(formula, data=df).fit(cov_type="cluster", cov_kwds={"groups": df["site_id"]})
    rows = [{"year": REFERENCE_YEAR, "coef": 0.0, "se": 0.0}]
    for y in years:
        rows.append({"year": y, "coef": res.params[f"tx_{y}"], "se": res.bse[f"tx_{y}"]})
    return pd.DataFrame(rows).sort_values("year"), res


def plot_trends(df: pd.DataFrame):
    means = df.groupby(["year", "treated"])["mean_value"].mean().unstack("treated")
    fig, ax = plt.subplots(figsize=(8, 5), dpi=170)
    ax.plot(means.index, means[1], "-o", color=TREAT_COLOR, lw=2, ms=5, label="Treatment (Biblis, Unterweser)")
    ax.plot(means.index, means[0], "-o", color=CTRL_COLOR, lw=2, ms=5, label="Control (Grohnde, Emsland, Brokdorf)")
    ax.axvline(2010.5, color=MUTED, ls="--", lw=1)
    ax.text(2010.6, ax.get_ylim()[1], "Abschaltung 2011", color=MUTED, fontsize=8, va="top")
    ax.set_xlabel("Jahr"); ax.set_ylabel("Ø Wassertemperatur (°C)")
    ax.set_title("Jahresmittel der Wassertemperatur: Treatment vs. Control (downstream ≤ 50 km)",
                 fontsize=11.5, color=INK, weight="bold")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="y", color="#e1e0d9", lw=0.6)
    for s in ax.spines.values():
        s.set_edgecolor("#e1e0d9")
    fig.tight_layout(); fig.savefig(FIGS / "did_trends.png", dpi=170, facecolor="white")
    plt.close(fig)


def plot_event_study(es: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 5), dpi=170)
    ax.axhline(0, color=MUTED, lw=1)
    ax.axvline(2010.5, color=MUTED, ls="--", lw=1)
    ax.errorbar(es["year"], es["coef"], yerr=1.96 * es["se"], fmt="o", color=INK,
                ecolor="#b4b3ac", elinewidth=1.4, capsize=3, ms=5)
    ax.set_xlabel("Jahr"); ax.set_ylabel("Treatment-Effekt auf Ø Temp. (°C)")
    ax.set_title("Event-Study: Temperatur-Differenz Treatment−Control (Referenz 2010)",
                 fontsize=11.5, color=INK, weight="bold")
    ax.grid(axis="y", color="#e1e0d9", lw=0.6)
    for s in ax.spines.values():
        s.set_edgecolor("#e1e0d9")
    fig.tight_layout(); fig.savefig(FIGS / "did_event_study.png", dpi=170, facecolor="white")
    plt.close(fig)


def write_results(df, tbl, did, es):
    n_sites = df.groupby("nearest_upstream_group")["site_id"].nunique()
    b, se, p = did.params["did"], did.bse["did"], did.pvalues["did"]
    coverage = df.pivot_table(index="year", columns="treated", values="mean_value",
                              aggfunc="count").fillna(0).astype(int)
    treated_post_years = sorted(int(y) for y in df[(df.treated == 1) & (df.post == 1)]["year"].unique())
    lines = [
        "# DiD: 2011-Abschaltung und Wassertemperatur (Treatment vs. Control)",
        "",
        "*Erster, explorativer Durchgang.*",
        "",
        "## Kernbefund (ehrlich)",
        "Mit den **jährlichen** Waterbase-Daten ist die Analyse **nicht belastbar**: Die "
        f"Treatment-Gruppe hat nach 2011 praktisch nur die Jahre {treated_post_years} — "
        "eine echte Nachher-Periode fehlt, und der 2×2-/Event-Study-Schätzer wird von "
        "Kompositionswechseln (unterschiedliche Messstellen je Jahr) getrieben, nicht von einem "
        "Effekt. Für eine belastbare DiD brauchen wir **Waterbase Part 1 (Disaggregated)** — "
        "Einzelmessungen für ein dichtes, balanciertes Monats-/Saison-Panel.",
        "",
        "## Datenabdeckung (Messstellen × Jahr, Anzahl Beobachtungen)",
        "",
        "| Jahr | Control | Treatment |",
        "|---|---|---|",
    ] + [f"| {y} | {coverage.loc[y].get(0,0)} | {coverage.loc[y].get(1,0)} |" for y in coverage.index] + [
        "",
        "## Stichprobe",
        f"- Treatment-Standorte (downstream ≤ 50 km): {int(n_sites.get('treatment', 0))} Messstellen",
        f"- Control-Standorte (downstream ≤ 50 km): {int(n_sites.get('control', 0))} Messstellen",
        f"- Beobachtungen (Messstelle × Jahr): {len(df)}",
        f"- Jahre: {df['year'].min()}–{df['year'].max()} (ohne 2006/2007/2015)",
        f"- Cluster (Messstellen): {df['site_id'].nunique()}",
        "",
        "## 2×2-Mittelwerte (°C)",
        "",
        "| | vor 2011 | ab 2011 |",
        "|---|---|---|",
        f"| Control | {tbl.loc[0,0]:.2f} | {tbl.loc[0,1]:.2f} |",
        f"| Treatment | {tbl.loc[1,0]:.2f} | {tbl.loc[1,1]:.2f} |",
        "",
        f"Roher 2×2-DiD: **{(tbl.loc[1,1]-tbl.loc[1,0])-(tbl.loc[0,1]-tbl.loc[0,0]):+.3f} °C**",
        "",
        "## Two-Way-Fixed-Effects (Messstellen- + Jahres-FE, SE geclustert je Messstelle)",
        "",
        f"- Treatment-Effekt (treated×post): **{b:+.3f} °C**  (SE {se:.3f}, p = {p:.3f})",
        f"- 95%-KI: [{b-1.96*se:+.3f}, {b+1.96*se:+.3f}] °C",
        "",
        "## Event-Study (Referenz 2010)",
        "",
        "| Jahr | Effekt (°C) | SE |",
        "|---|---|---|",
    ]
    for _, r in es.iterrows():
        lines.append(f"| {int(r['year'])} | {r['coef']:+.3f} | {r['se']:.3f} |")
    lines += [
        "",
        "## Vorbehalte",
        "- Sehr kleine Stichprobe und wenige Cluster → Standardfehler nur näherungsweise; "
        "p-Werte vorsichtig interpretieren (idealerweise Wild-Cluster-Bootstrap).",
        "- Nur wenige Vorjahre (2008–2010) → Parallel-Trend-Annahme kaum testbar.",
        "- Jahresmittel; der thermische Effekt ist im Sommer/Niedrigwasser am größten "
        "(Waterbase Part 1 nötig).",
        "- Unterweser/Brokdorf sind tidebeeinflusst; Abfluss noch nicht als Kovariate drin.",
        "",
        "Figuren: `figures/did_trends.png`, `figures/did_event_study.png`.",
    ]
    RESULTS.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    df = load_panel()
    tbl = two_by_two(df)
    did = fit_did(df)
    es, _ = fit_event_study(df)

    FIGS.mkdir(exist_ok=True)
    plot_trends(df)
    plot_event_study(es)
    write_results(df, tbl, did, es)

    print(f"obs {len(df)} | sites {df['site_id'].nunique()} "
          f"(treat {df[df.treated==1]['site_id'].nunique()}, ctrl {df[df.treated==0]['site_id'].nunique()})")
    print(f"DiD treated x post: {did.params['did']:+.3f} C "
          f"(SE {did.bse['did']:.3f}, p {did.pvalues['did']:.3f})")
    print(f"wrote {RESULTS.name}, did_trends.png, did_event_study.png")


if __name__ == "__main__":
    main()
