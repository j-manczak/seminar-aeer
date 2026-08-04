"""2x2 difference-in-differences on the 2011 shutdowns, five years either side.

Study window
------------
The 13th amendment to the Atomic Energy Act came into force on **6 August 2011**
and permanently withdrew the operating licences of Isar 1, Neckarwestheim 1 and
Philippsburg 1. That date is the cut; the window is the five years before and
the five years after it (2006-08-06 .. 2016-08-05).

The three blocks had already been taken off the grid by the moratorium in March
2011, so the March date is carried as an alternative cut and the months in
between as a donut.

Data
----
Only files in `data_temperature_oxygen/` are read. The letters in a file name
say what is in it: ``C`` temperature, ``P`` stage, ``O`` oxygen. No gauge from
any other source is used; where the folder has no data for a parameter, that
combination is reported as not estimable rather than filled from elsewhere.

Outcomes
--------
``temperature``    daily mean water temperature, deg C (every pair)
``oxygen``         daily mean dissolved oxygen, mg/l (``_CO`` pairs only)
``o2_saturation``  the same oxygen as percent of the temperature-implied
                   equilibrium value - separates the pure solubility channel
                   (warmer water holds less O2) from everything else
``level``          daily mean stage, cm - not an outcome but a confounder check
                   that the hydrology of the two gauges did not diverge

Run:
    python data_temperature_oxygen/results/did_analysis.py
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

import didlib
from didlib import build_panel, event_study, paired_did, station_series

OUT_DIR = Path(__file__).resolve().parent

CUT = pd.Timestamp("2011-08-06")           # 13. AtG-Novelle in force
MORATORIUM = pd.Timestamp("2011-03-14")    # blocks taken off the grid
WINDOW_START = pd.Timestamp("2006-08-06")
WINDOW_END = pd.Timestamp("2016-08-05")

UNITS = {"temperature": "°C", "oxygen": "mg/l", "o2_saturation": "%", "level": "cm"}

PLANTS = {
    "Isar (Ohu)": (48.6058, 12.2933),
    "Neckarwestheim": (49.0414, 9.1731),
    "Philippsburg": (49.2525, 8.4364),
    "Gundremmingen": (48.5147, 10.4022),
}

STATIONS = {
    "Landshut-Birket": dict(
        river="Isar", lat=48.5274, lon=12.1332, source="GKD Bayern",
        temperature="Landshut_Birket_2011-5_C.csv",
        level="Landshut_Birket_2011-5_P.csv",
    ),
    "Landau a.d. Isar": dict(
        river="Isar", lat=48.6751, lon=12.6926, source="GKD Bayern",
        temperature="Landau_2011-5_C.csv",
        level="Landau_2011-5_P.csv",
    ),
    "Neu-Ulm": dict(
        river="Donau", lat=48.3891, lon=9.9866, source="GKD Bayern",
        temperature="Neu_Ulm_2001-5_C.csv",
    ),
    "Donauwörth": dict(
        river="Donau", lat=48.7107, lon=10.8015, source="GKD Bayern",
        temperature="Donauworth_2011-5_C.csv",
        level="Donauworth_2011-5_P.csv",
    ),
    "Besigheim": dict(
        river="Neckar", lat=49.0023, lon=9.1472, source="LUBW",
        temperature=("Besigheim-2011-5_CO.csv", "Temperatur"),
        oxygen=("Besigheim-2011-5_CO.csv", "Sauerstoff"),
    ),
    "Lauffen": dict(
        river="Neckar", lat=49.0719, lon=9.1606, source="LUBW",
        temperature=("Lauffen-2011-5_CO.csv", "Temperatur"),
        oxygen=("Lauffen-2011-5_CO.csv", "Sauerstoff"),
    ),
    "Mannheim (Neckar)": dict(
        river="Neckar", lat=49.4943, lon=8.4687, source="LUBW",
        temperature=("Mannheim-2011-5_CO.csv", "Temperatur"),
        oxygen=("Mannheim-2011-5_CO.csv", "Sauerstoff"),
    ),
    "Karlsruhe (Rhein)": dict(
        river="Rhein", lat=49.0110, lon=8.2983, source="LUBW",
        temperature=("Karlsruhe_2011-5_CO.csv", "Temperatur"),
        oxygen=("Karlsruhe_2011-5_CO.csv", "Sauerstoff"),
    ),
}

CHEM = ["temperature", "oxygen", "o2_saturation"]

CASES = [
    dict(
        case="A1", plant="Isar (Ohu)", block="Isar 1", river="Isar",
        label="Isar 1 — Landshut-Birket → Landau",
        up="Landshut-Birket", down="Landau a.d. Isar",
        cooling="Durchlaufkühlung", heat_to_river="hoch", role="treatment",
        # Both Isar files are _C / _P - the folder carries no oxygen for Bavaria,
        # so the oxygen question cannot be asked at the one site with an effect.
        outcomes=["temperature"], level_pair=True,
    ),
    dict(
        case="B1", plant="Neckarwestheim", block="Neckarwestheim 1", river="Neckar",
        label="Neckarwestheim 1 — Besigheim → Lauffen (Nahfeld)",
        up="Besigheim", down="Lauffen",
        cooling="Kühlturm", heat_to_river="niedrig", role="treatment",
        outcomes=CHEM, level_pair=False,
    ),
    dict(
        case="B2", plant="Neckarwestheim", block="Neckarwestheim 1", river="Neckar",
        label="Neckarwestheim 1 — Besigheim → Mannheim (Fernfeld)",
        up="Besigheim", down="Mannheim (Neckar)",
        cooling="Kühlturm", heat_to_river="niedrig", role="treatment_far",
        outcomes=CHEM, level_pair=False,
    ),
    dict(
        case="C1", plant="Philippsburg", block="Philippsburg 1", river="Rhein/Neckar",
        label="Philippsburg 1 — Karlsruhe → Mannheim (flussübergreifend, NICHT identifiziert)",
        up="Karlsruhe (Rhein)", down="Mannheim (Neckar)",
        cooling="hybrid", heat_to_river="mittel", role="not_identified",
        outcomes=CHEM, level_pair=False,
    ),
    dict(
        case="P1", plant="Gundremmingen", block="— (B/C liefen weiter)", river="Donau",
        label="Placebo Donau — Neu-Ulm → Donauwörth",
        up="Neu-Ulm", down="Donauwörth",
        cooling="Kühlturm", heat_to_river="niedrig", role="placebo",
        outcomes=["temperature"], level_pair=False,
    ),
    dict(
        case="P2", plant="—", block="— (beide Pegel unbehandelt)", river="Rhein/Neckar",
        label="Placebo Kontrolle↔Kontrolle — Karlsruhe → Besigheim",
        up="Karlsruhe (Rhein)", down="Besigheim",
        cooling="—", heat_to_river="—", role="placebo",
        outcomes=CHEM, level_pair=False,
    ),
]

# Combinations the folder cannot support, reported instead of quietly dropped.
NOT_ESTIMABLE = [
    dict(case="A1", outcome="oxygen", grund=(
        "Isar: Landshut-Birket und Landau liegen nur als _C (Temperatur) und _P "
        "(Pegel) vor. Ohne eine _O-Datei für beide Pegel ist der Sauerstoffkanal "
        "am einzigen Standort mit Durchlaufkühlung nicht schätzbar.")),
    dict(case="A1", outcome="o2_saturation", grund=(
        "Folgt aus der fehlenden Sauerstoffreihe an der Isar.")),
    dict(case="B1", outcome="level", grund=(
        "Neckar: Besigheim und Lauffen sind LUBW-Gütemessstellen (_CO), es gibt "
        "keine Pegeldatei. Die Abflusskontrolle fehlt für alle Neckar- und "
        "Rheinpaare.")),
    dict(case="P1", outcome="level", grund=(
        "Neu-Ulm hat keine _P-Datei, deshalb kein Pegelpaar an der Donau.")),
]


def haversine_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def panel_for(case: dict, outcome: str) -> pd.DataFrame:
    """Balanced daily panel for one case and outcome, plus stage where available."""
    up = station_series(STATIONS[case["up"]], outcome)
    down = station_series(STATIONS[case["down"]], outcome)
    if up.empty or down.empty:
        return pd.DataFrame()
    panel = build_panel(up, down, WINDOW_START, WINDOW_END)

    if case["level_pair"]:
        for role in ("up", "down"):
            lvl = station_series(STATIONS[case[role]], "level")
            if not lvl.empty:
                panel = panel.merge(
                    lvl.rename(columns={"value": f"level_{role}"}), on="date", how="left"
                )
    return panel


def spec_rows(case: dict, outcome: str, panel: pd.DataFrame) -> list[dict]:
    """Baseline plus every robustness specification for one case-outcome."""
    base = dict(case=case["case"], label=case["label"], role=case["role"],
                river=case["river"], block=case["block"], outcome=outcome,
                unit=UNITS[outcome], upstream=case["up"], downstream=case["down"])
    rows = []

    def add(spec: str, note: str, sub: pd.DataFrame, cut=CUT, **kw):
        if len(sub) < 60:
            rows.append({**base, "spec": spec, "note": note, "n": len(sub),
                         "did": np.nan, "se": np.nan, "p": np.nan})
            return
        rows.append({**base, "spec": spec, "note": note, "cut": cut.date(),
                     **paired_did(sub, cut, **kw)})

    add("baseline", "Schnitt 06.08.2011, Monats-FE, HAC(30)", panel)
    add("no_month_fe", "ohne Monats-FE = klassisches 2×2 auf den gepaarten Tagen",
        panel, month_fe=False)
    add("cut_moratorium", "Schnitt 14.03.2011 (Moratorium, Netzabgang)",
        panel, cut=MORATORIUM)
    add("donut_transition", "Übergangsmonate 14.03.–05.08.2011 entfernt",
        panel[(panel["date"] < MORATORIUM) | (panel["date"] >= CUT)])
    add("donut_1y", "±1 Jahr um den Schnitt entfernt",
        panel[(panel["date"] < CUT - pd.Timedelta(days=365))
              | (panel["date"] >= CUT + pd.Timedelta(days=365))])
    add("placebo_cut_2008", "Nur Vorperiode, Scheinschnitt 06.08.2008",
        panel[panel["date"] < MORATORIUM], cut=pd.Timestamp("2008-08-06"))
    add("summer", "nur Juni–September (Niedrigwasser, größte thermische Last)",
        panel[panel["month"].isin(didlib.SUMMER_MONTHS)])
    add("winter", "nur Oktober–Mai", panel[~panel["month"].isin(didlib.SUMMER_MONTHS)])

    # Not for the stage outcome itself - there the controls would reproduce the
    # dependent variable exactly.
    if outcome != "level" and {"level_up", "level_down"} <= set(panel.columns):
        sub = panel.dropna(subset=["level_up", "level_down"])
        add("level_control", "zusätzlich Wasserstand beider Pegel als Kovariate",
            sub, controls=["level_up", "level_down"])

    return rows


def main() -> None:
    pairs, coverage, summary, robustness, events = [], [], [], [], []

    for case in CASES:
        up_st, down_st = STATIONS[case["up"]], STATIONS[case["down"]]
        plant = PLANTS.get(case["plant"])
        for role, name, st in (("upstream/Kontrolle", case["up"], up_st),
                               ("downstream/Treatment", case["down"], down_st)):
            pairs.append({
                "case": case["case"], "role": role, "station": name,
                "river": st["river"], "source": st["source"],
                "lat": st["lat"], "lon": st["lon"],
                "km_luftlinie_zum_kraftwerk": round(haversine_km((st["lat"], st["lon"]), plant), 1)
                if plant else np.nan,
                "dateien": ", ".join(sorted({
                    (v[0] if isinstance(v, tuple) else v)
                    for k, v in st.items() if k in ("temperature", "oxygen", "level")})),
            })

        for outcome in case["outcomes"] + (["level"] if case["level_pair"] else []):
            panel = panel_for(case, outcome)
            if panel.empty:
                continue

            coverage.append({
                "case": case["case"], "outcome": outcome, "unit": UNITS[outcome],
                "upstream": case["up"], "downstream": case["down"],
                "gepaarte_tage": len(panel),
                "davon_vor_schnitt": int((panel["date"] < CUT).sum()),
                "davon_nach_schnitt": int((panel["date"] >= CUT).sum()),
                "erster_tag": panel["date"].min().date(),
                "letzter_tag": panel["date"].max().date(),
                "abdeckung_vorperiode": round(
                    (panel["date"] < CUT).sum() / (CUT - WINDOW_START).days, 3),
                "abdeckung_nachperiode": round(
                    (panel["date"] >= CUT).sum() / (WINDOW_END - CUT).days, 3),
            })

            rows = spec_rows(case, outcome, panel)
            robustness.extend(rows)
            summary.append(next(r for r in rows if r["spec"] == "baseline"))

            es = event_study(panel, CUT)
            if not es.empty:
                es.insert(0, "outcome", outcome)
                es.insert(0, "case", case["case"])
                events.append(es)

    frames = {
        "station_pairs.csv": pd.DataFrame(pairs),
        "data_coverage.csv": pd.DataFrame(coverage),
        "not_estimable.csv": pd.DataFrame(NOT_ESTIMABLE),
        "DiD_summary.csv": pd.DataFrame(summary),
        "DiD_robustness.csv": pd.DataFrame(robustness),
        "event_study.csv": pd.concat(events, ignore_index=True) if events else pd.DataFrame(),
    }
    for name, frame in frames.items():
        frame.to_csv(OUT_DIR / name, index=False, encoding="utf-8-sig")

    _report(frames)


def _report(frames: dict[str, pd.DataFrame]) -> None:
    pd.set_option("display.width", 220, "display.max_columns", 60)
    summary = frames["DiD_summary.csv"]

    print("=" * 100)
    print("2×2 DiD — Abschaltungen August 2011, Fenster 2006-08-06 bis 2016-08-05")
    print("Datenbasis: ausschliesslich data_temperature_oxygen/")
    print("=" * 100)
    print("\nMESSSTELLEN\n")
    print(frames["station_pairs.csv"].to_string(index=False))
    print("\nABDECKUNG\n")
    print(frames["data_coverage.csv"].to_string(index=False))

    print("\nNICHT SCHÄTZBAR (keine passende Datei im Ordner)\n")
    for _, r in frames["not_estimable.csv"].iterrows():
        print(f"  [{r['case']}] {r['outcome']}: {r['grund']}")

    print("\nHAUPTERGEBNISSE (Schnitt 06.08.2011, Monats-FE, Newey-West HAC(30))\n")
    cols = ["case", "outcome", "unit", "role", "up_pre", "up_post", "down_pre", "down_post",
            "gap_pre", "gap_post", "did", "se", "p", "n_pre", "n_post"]
    view = summary[cols].copy()
    for c in ["up_pre", "up_post", "down_pre", "down_post", "gap_pre", "gap_post", "did", "se"]:
        view[c] = view[c].round(3)
    view["p"] = view["p"].map(lambda v: f"{v:.2e}" if pd.notna(v) and v < 1e-3 else round(v, 4))
    print(view.to_string(index=False))

    print("\nROBUSTHEIT\n")
    rob = frames["DiD_robustness.csv"]
    for (case, outcome), grp in rob.groupby(["case", "outcome"], sort=False):
        label = grp["label"].iloc[0]
        print(f"\n  [{case}] {label} — {outcome} ({UNITS[outcome]})")
        for _, r in grp.iterrows():
            if pd.isna(r.get("did")):
                print(f"    {r['spec']:<18} zu wenige Beobachtungen (n={int(r['n'])})")
                continue
            stars = "***" if r["p"] < 0.01 else "**" if r["p"] < 0.05 else "*" if r["p"] < 0.10 else ""
            print(f"    {r['spec']:<18} {r['did']:+7.3f}  (SE {r['se']:.3f}, p {r['p']:.4f}){stars:<3}"
                  f"  n={int(r['n']):5d}   {r['note']}")

    print("\nGeschrieben nach:", OUT_DIR)


if __name__ == "__main__":
    main()
