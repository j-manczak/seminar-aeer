"""Figures for the 2011 shutdown 2x2 on `data_temperature_oxygen/`.

One sheet per power station, named after the station, not after a case code.
Each sheet puts the two outcomes side by side — **temperature left, dissolved
oxygen right** — and carries the DiD result for both:

  row 1  the two gauges compared, monthly means
  row 2  the paired gap downstream minus upstream, with the pre and post level
         and the DiD estimate
  row 3  the year-bin event study, plotted as gap *levels* so the panel is
         readable without holding a reference year in your head

Where the folder has no oxygen for a river, the right column says so instead of
being filled from another source.

All figure text is English, because the figures go into the paper. The figures
carry labels and numbers only - every interpreting sentence lives in
`FIGURE_NOTES.md` next to this script, so a caption can be edited without
re-rendering a PNG.

Plus one cross-plant overview of every DiD estimate, and the Isar stage check.

Run after `did_analysis.py`:
    python data_temperature_oxygen/results/make_figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import did_analysis as A
from didlib import event_study

OUT_DIR = Path(__file__).resolve().parent
FIG_DIR = OUT_DIR / "figures"

# Validated categorical slots (dataviz reference palette, light mode).
C_CONTROL = "#2a78d6"   # slot 1 blue   - upstream / control
C_TREAT = "#eb6834"     # slot 2 orange - downstream / treatment
C_INK = "#0b0b0b"
C_INK2 = "#52514e"
C_MUTED = "#b8b6ae"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": C_MUTED, "axes.linewidth": 0.8, "axes.labelcolor": C_INK2,
    "axes.grid": True, "grid.color": "#e8e6e0", "grid.linewidth": 0.7, "grid.linestyle": "-",
    "xtick.color": C_INK2, "ytick.color": C_INK2, "text.color": C_INK,
    "font.size": 9, "axes.titlesize": 10, "legend.frameon": False,
})

# One sheet per station. ``temperature``/``oxygen`` name the case that supplies
# each column; ``None`` means the folder has no such series for this river.
SHEETS = [
    dict(
        file="Isar-1.png",
        title="Isar 1 — shutdown 6 August 2011",
        subtitle="Once-through cooling, high heat load to the river · Isar · "
                 "Landshut-Birket (15 km upstream) → Landau (30 km downstream)",
        temperature="A1", oxygen=None,
        oxygen_note="No dissolved-oxygen series\nfor the Isar in this dataset",
    ),
    dict(
        file="Neckarwestheim-1.png",
        title="Neckarwestheim 1 — shutdown 6 August 2011",
        subtitle="Wet cooling tower, little heat to the river · Neckar · "
                 "Besigheim (5 km upstream) → Lauffen (4 km downstream)",
        temperature="B1", oxygen="B1",
    ),
    dict(
        file="Philippsburg-1.png",
        title="Philippsburg 1 — shutdown 6 August 2011 · NOT IDENTIFIED",
        subtitle="Hybrid cooling · Karlsruhe (Rhine, upstream) → Mannheim (NECKAR) · "
                 "not an upstream/downstream pair",
        temperature="C1", oxygen="C1",
    ),
    dict(
        file="Placebo-Gundremmingen-Danube.png",
        title="Placebo Danube — Gundremmingen kept operating",
        subtitle="Unit B until end-2017, unit C until end-2021 · no shutdown in the "
                 "2006–2016 window · Neu-Ulm → Donauwörth",
        temperature="P1", oxygen=None,
        oxygen_note="No dissolved-oxygen series\nfor the Danube in this dataset",
    ),
    dict(
        file="Placebo-Control-Karlsruhe-Besigheim.png",
        title="Placebo control ↔ control",
        subtitle="Both stations lie upstream of their plant and are therefore untreated · "
                 "Karlsruhe (Rhine) → Besigheim (Neckar)",
        temperature="P2", oxygen="P2",
    ),
]


def _tidy(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_axisbelow(True)


def _stars(p: float) -> str:
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else "n.s."


def _river(station: str) -> str:
    return A.STATIONS[station]["river"]


def _labels(case: dict) -> tuple[str, str, str]:
    """Gauge labels and the word for their difference, honest per case role.

    Only the treatment pairs really are control/treatment; the Donau placebo is
    a genuine upstream/downstream pair that simply was not treated, and the
    cross-river pairs are neither, so they get no positional wording at all.
    """
    up, down = case["up"], case["down"]
    if case["role"] in ("treatment", "treatment_far"):
        return f"{up} (upstream, control)", f"{down} (downstream, treated)", "Gap"
    if _river(up) == _river(down):
        return f"{up} (upstream, untreated)", f"{down} (downstream, untreated)", "Gap"
    return f"{up}, {_river(up)}", f"{down}, {_river(down)}", "Difference"


# --------------------------------------------------------------------------- #
# one outcome column of a station sheet
# --------------------------------------------------------------------------- #
def _column(axes, case: dict, outcome: str, panel: pd.DataFrame, row: pd.Series) -> None:
    unit = A.UNITS[outcome]
    ax_series, ax_gap, ax_event = axes
    up_label, down_label, gap_word = _labels(case)

    # --- the two gauges compared ------------------------------------------- #
    m = panel.set_index("date")[["value_up", "value_down"]].resample("MS").mean()
    ax_series.plot(m.index, m["value_up"], color=C_CONTROL, lw=1.5,
                   label=up_label)
    ax_series.plot(m.index, m["value_down"], color=C_TREAT, lw=1.5,
                   label=down_label)
    ax_series.axvline(A.CUT, color=C_INK, lw=1.2)
    ax_series.set_ylabel(f"Monthly mean [{unit}]")
    ax_series.set_title("Both monitoring stations", loc="left", fontsize=9)
    # Headroom reserved inside the panel so the legend never sits on the data
    # and never has to be pushed above the axes, where the header lives.
    lo, hi = ax_series.get_ylim()
    ax_series.set_ylim(lo, hi + 0.42 * (hi - lo))
    ax_series.legend(loc="upper center", ncol=1, fontsize=8)
    _tidy(ax_series)

    # --- the gap, which is what the DiD estimates --------------------------- #
    gap = panel.set_index("date")["gap"]
    ax_gap.plot(gap.index, gap.values, color=C_CONTROL, lw=0.5, alpha=0.25)
    ax_gap.plot(gap.index, gap.rolling(31, min_periods=2, center=True).mean(),
                color=C_CONTROL, lw=1.8,
                label=f"{gap_word} {case['down']} − {case['up']} (31-day mean)")
    ax_gap.axhline(0, color=C_MUTED, lw=0.9)
    ax_gap.axvline(A.CUT, color=C_INK, lw=1.2)
    for lo, hi, level, tag, dy, va in (
        (panel["date"].min(), A.CUT, row["gap_pre"], "before", 9, "bottom"),
        (A.CUT, panel["date"].max(), row["gap_post"], "after", -11, "top"),
    ):
        ax_gap.hlines(level, lo, hi, color=C_INK, lw=2.4, zorder=5)
        ax_gap.annotate(f"{tag} {level:+.2f}", xy=(lo + (hi - lo) / 2, level),
                        xytext=(0, dy), textcoords="offset points", ha="center", va=va,
                        fontsize=8.5, fontweight="bold", color=C_INK)
    ax_gap.set_ylabel(f"{gap_word} [{unit}]")
    ax_gap.set_title(f"{gap_word} downstream − upstream (the DiD outcome)", loc="left", fontsize=9)
    lo, hi = ax_gap.get_ylim()
    ax_gap.set_ylim(lo, hi + 0.28 * (hi - lo))
    ax_gap.legend(loc="upper center", fontsize=8)
    _tidy(ax_gap)

    # --- event study, in levels --------------------------------------------- #
    es = event_study(panel, A.CUT)
    if es.empty:
        ax_event.text(0.5, 0.5, "Too few yearly bins for an event study",
                      ha="center", va="center", transform=ax_event.transAxes, color=C_INK2)
    else:
        base = es.loc[es["reference"], "gap_mean"].iloc[0]
        level = es["coef"] + base
        err = np.vstack([level - (es["ci_lo"] + base), (es["ci_hi"] + base) - level])
        pre = (es["rel_year"] < 0) & ~es["reference"]
        post = es["rel_year"] >= 0
        ref = es["reference"]
        ax_event.errorbar(es.loc[pre, "rel_year"], level[pre], yerr=err[:, pre.values],
                          fmt="o", ms=6, lw=1.3, capsize=3, color=C_CONTROL, label="before shutdown")
        ax_event.errorbar(es.loc[post, "rel_year"], level[post], yerr=err[:, post.values],
                          fmt="o", ms=6, lw=1.3, capsize=3, color=C_TREAT, label="after shutdown")
        # The reference year has no interval by construction - draw it hollow so
        # it is not misread as a precisely estimated point.
        ax_event.plot(es.loc[ref, "rel_year"], level[ref], "o", ms=6, mfc=SURFACE,
                      mec=C_CONTROL, mew=1.8, label="reference year (no CI)")
        ax_event.axvline(-0.5, color=C_INK, lw=1.2)
        ax_event.axhline(0, color=C_MUTED, lw=0.9)
        ax_event.set_xticks(es["rel_year"])
        lo, hi = ax_event.get_ylim()
        ax_event.set_ylim(lo, hi + 0.3 * (hi - lo))
        ax_event.legend(loc="upper center", fontsize=8, ncol=3)
    ax_event.set_xlabel("Year relative to 6 Aug 2011")
    ax_event.set_ylabel(f"{gap_word} [{unit}]")
    ax_event.set_title(f"Event study: yearly {gap_word.lower()} with 95% CI", loc="left", fontsize=9)
    _tidy(ax_event)


def _missing_column(fig, gs, note: str) -> None:
    """One merged axis saying which file would be needed and why it matters."""
    ax = fig.add_subplot(gs[:, 1])
    ax.text(0.5, 0.6, note, ha="center", va="center", fontsize=11, color=C_INK2,
            linespacing=1.8, transform=ax.transAxes)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    for side in ("top", "right", "bottom", "left"):
        ax.spines[side].set_visible(side == "left")
    ax.spines["left"].set_color(C_MUTED)


def _column_header(fig, x: float, heading: str, result: str, extra: str = "") -> None:
    """Column title and DiD result, drawn on the figure so both columns align."""
    fig.text(x, 0.905, heading, fontsize=11.5, fontweight="bold", color=C_INK, va="top")
    fig.text(x, 0.884, result, fontsize=11, fontweight="bold", color=C_INK, va="top")
    if extra:
        fig.text(x, 0.864, extra, fontsize=8.8, color=C_INK2, va="top", linespacing=1.5)


def station_sheet(sheet: dict, summary: pd.DataFrame, path: Path) -> None:
    cases = {c["case"]: c for c in A.CASES}
    x_left, x_right = 0.062, 0.545

    fig = plt.figure(figsize=(14, 12.5))
    gs = fig.add_gridspec(3, 2, hspace=0.62, wspace=0.22,
                          height_ratios=[1.0, 1.0, 0.85],
                          top=0.798, bottom=0.075, left=0.062, right=0.975)

    # left column: temperature
    case = cases[sheet["temperature"]]
    panel = A.panel_for(case, "temperature")
    row = summary[(summary["case"] == case["case"]) & (summary["outcome"] == "temperature")].iloc[0]
    _column([fig.add_subplot(gs[i, 0]) for i in range(3)], case, "temperature", panel, row)
    _column_header(fig, x_left, "WATER TEMPERATURE",
                   f"DiD = {row['did']:+.2f} °C   (SE {row['se']:.2f}, p {row['p']:.3g}) "
                   f"{_stars(row['p'])}",
                   f"{_labels(case)[2]} before {row['gap_pre']:+.2f} °C  →  "
                   f"after {row['gap_post']:+.2f} °C")

    # right column: oxygen, or the reason there is none
    if sheet["oxygen"] is None:
        _missing_column(fig, gs, sheet["oxygen_note"])
        _column_header(fig, x_right, "DISSOLVED OXYGEN", "DiD not estimable")
    else:
        case_o = cases[sheet["oxygen"]]
        panel_o = A.panel_for(case_o, "oxygen")
        row_o = summary[(summary["case"] == case_o["case"]) & (summary["outcome"] == "oxygen")].iloc[0]
        _column([fig.add_subplot(gs[i, 1]) for i in range(3)], case_o, "oxygen", panel_o, row_o)
        extra = (f"{_labels(case_o)[2]} before {row_o['gap_pre']:+.2f} mg/l  →  "
                 f"after {row_o['gap_post']:+.2f} mg/l")
        sat = summary[(summary["case"] == case_o["case"]) & (summary["outcome"] == "o2_saturation")]
        if not sat.empty and pd.notna(sat.iloc[0]["did"]):
            s = sat.iloc[0]
            # Second line - the saturation decomposition does not fit beside the
            # gap levels without running off the column. What it is for is
            # explained in FIGURE_NOTES.md, not on the figure.
            extra += f"\nSaturation {s['did']:+.2f} % (p {s['p']:.3g}) {_stars(s['p'])}"
        _column_header(fig, x_right, "DISSOLVED OXYGEN",
                       f"DiD = {row_o['did']:+.2f} mg/l   (SE {row_o['se']:.2f}, "
                       f"p {row_o['p']:.3g}) {_stars(row_o['p'])}", extra)

    fig.text(0.062, 0.975, sheet["title"], fontsize=16, fontweight="bold", color=C_INK, va="top")
    fig.text(0.062, 0.949, sheet["subtitle"], fontsize=9.5, color=C_INK2, va="top")
    fig.text(0.062, 0.931, "2×2 DiD · paired daily difference, month FE, Newey-West HAC(30) · "
                           "window 6 Aug 2006 – 5 Aug 2016 · cut-off 6 Aug 2011",
             fontsize=8.5, color=C_INK2, va="top")

    fig.savefig(path, dpi=110)
    plt.close(fig)


# --------------------------------------------------------------------------- #
# cross-plant figures
# --------------------------------------------------------------------------- #
def overview_figure(summary: pd.DataFrame, path: Path) -> None:
    """All DiD estimates, one panel per unit — never two scales on one axis."""
    outcomes = [("temperature", "Water temperature [°C]"),
                ("oxygen", "Dissolved oxygen [mg/l]"),
                ("o2_saturation", "Oxygen saturation [%]")]
    rows = [
        ("A1", "Isar 1 → Landau"),
        ("B1", "Neckarwestheim 1 → Lauffen"),
        ("B2", "Neckarwestheim 1 → Mannheim"),
        ("C1", "Philippsburg 1 → Mannheim (n.i.)"),
        ("P1", "Placebo Danube → Donauwörth"),
        ("P2", "Placebo Karlsruhe → Besigheim"),
    ]
    # One row order for all three panels, so a station sits at the same height
    # everywhere and a missing estimate reads as missing rather than shifting
    # every row below it.
    order = {case: len(rows) - 1 - i for i, (case, _) in enumerate(rows)}
    fig, axes = plt.subplots(1, 3, figsize=(14, 5.6), sharey=True)

    for ax, (outcome, title) in zip(axes, outcomes):
        sub = summary[(summary["outcome"] == outcome) & summary["did"].notna()]
        for _, r in sub.iterrows():
            yi = order[r["case"]]
            col = C_MUTED if r["role"] in ("placebo", "not_identified") else C_TREAT
            ax.plot([r["ci_lo"], r["ci_hi"]], [yi, yi], color=col, lw=2.2, solid_capstyle="round")
            ax.plot(r["did"], yi, "o", ms=9, color=col,
                    markeredgecolor=SURFACE, markeredgewidth=2, zorder=5)
            ax.annotate(f"{r['did']:+.2f}", xy=(r["did"], yi), xytext=(0, 10),
                        textcoords="offset points", ha="center", fontsize=8.5, color=C_INK)
        ax.axvline(0, color=C_INK, lw=1.0)
        ax.set_yticks(list(order.values()))
        ax.set_yticklabels([f"{lbl}" for _, lbl in rows], fontsize=8.5)
        ax.set_ylim(-0.7, len(rows) - 0.3)
        ax.set_title(title, loc="left", fontweight="bold")
        ax.set_xlabel("DiD estimate with 95% CI")
        ax.grid(axis="y", visible=False)
        _tidy(ax)

    handles = [plt.Line2D([], [], marker="o", ls="-", color=C_TREAT, ms=8, lw=2.2,
                          label="Treated pair (upstream → downstream of the plant)"),
               plt.Line2D([], [], marker="o", ls="-", color=C_MUTED, ms=8, lw=2.2,
                          label="Placebo / not-identified pair")]
    fig.legend(handles=handles, loc="lower center", ncol=2, fontsize=9.5, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("2×2 DiD, shutdowns of 6 August 2011 — five years before vs. five years after",
                 fontweight="bold", x=0.09, ha="left", y=1.0)
    fig.tight_layout()
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def isar_level_figure(path: Path) -> None:
    """The Isar temperature jump against the stage gap of the same two gauges.

    The folder carries no oxygen for the Isar, so this asks the other question
    the data can answer: did the hydrology of the pair shift at the same moment?
    If it had, the temperature result would be suspect.
    """
    case = next(c for c in A.CASES if c["case"] == "A1")
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0))
    specs = [("temperature", "Temperature gap Landau − Landshut-Birket [°C]", "°C"),
             ("level", "Stage gap Landau − Landshut-Birket [cm]", "cm")]

    for ax, (outcome, title, unit) in zip(axes, specs):
        panel = A.panel_for(case, outcome)
        gap = panel.set_index("date")["gap"]
        ax.plot(gap.index, gap.values, color=C_CONTROL, lw=0.6, alpha=0.28)
        ax.plot(gap.index, gap.rolling(31, min_periods=2, center=True).mean(),
                color=C_CONTROL, lw=1.9)
        pre = panel[panel["date"] < A.CUT]["gap"].mean()
        post = panel[panel["date"] >= A.CUT]["gap"].mean()
        ax.hlines(pre, panel["date"].min(), A.CUT, color=C_INK, lw=2.4, zorder=5)
        ax.hlines(post, A.CUT, panel["date"].max(), color=C_INK, lw=2.4, zorder=5)
        ax.annotate(f"{pre:+.2f}", xy=(panel["date"].min(), pre), xytext=(6, 8),
                    textcoords="offset points", fontweight="bold", fontsize=9.5)
        ax.annotate(f"{post:+.2f}", xy=(A.CUT, post), xytext=(6, 8),
                    textcoords="offset points", fontweight="bold", fontsize=9.5)
        ax.axvline(A.CUT, color=C_INK, lw=1.2)
        ax.axhline(0, color=C_MUTED, lw=0.9)
        ax.set_title(title, loc="left", fontweight="bold")
        ax.set_ylabel(unit)
        _tidy(ax)

    fig.suptitle("Isar 1 — temperature gap and stage gap, same two gauges",
                 fontweight="bold", x=0.04, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(exist_ok=True)
    # Drop the earlier per-case-per-outcome sheets; one sheet per station now.
    for old in FIG_DIR.glob("*.png"):
        old.unlink()

    summary = pd.read_csv(OUT_DIR / "DiD_summary.csv", encoding="utf-8-sig")
    written = []

    for sheet in SHEETS:
        station_sheet(sheet, summary, FIG_DIR / sheet["file"])
        written.append(sheet["file"])

    overview_figure(summary, FIG_DIR / "Overview-all-DiD.png")
    isar_level_figure(FIG_DIR / "Isar-1_stage-check.png")
    written += ["Overview-all-DiD.png", "Isar-1_stage-check.png"]

    print(f"{len(written)} figures written to {FIG_DIR}:")
    for name in written:
        print("  ", name)


if __name__ == "__main__":
    main()
