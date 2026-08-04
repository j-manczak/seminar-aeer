"""Was steht sonst noch am Fluss? Ein Inventar je Kernkraftwerksstandort.

Für jeden Standort wird aufgelistet, welche anderen Energieerzeuger auf demselben
Fluss liegen, und zwar mit:

* exakten Koordinaten und Ortsbezeichnung,
* **Entfernung entlang des Flusslaufs** zum Kernkraftwerk — nicht Luftlinie,
* Entfernung zur benutzten Upstream- und Downstream-Messstelle und der Angabe,
  ob die Anlage ober- oder unterhalb *dieser Messstellen* liegt,
* Erzeugungsart (Technologie und Energieträger),
* und der Einschätzung, ob dort Kühlwasser aus dem Fluss genutzt wird.

Die letzte Spalte ist die entscheidende: eine Laufwasserturbine steht am selben
Fluss, fügt ihm aber keine Wärme zu, während schon ein kleines Heizkraftwerk mit
Dampfteil einen Kondensator hat. Für das 2×2 zählt außerdem nur, was **zwischen
den beiden Messstellen** liegt — alles oberhalb der Kontrolle wärmt beide Pegel
gleichermaßen und fällt aus der Differenz heraus.

Ausgaben:
    data/processed/analysis/plant_2x2/energy_producers_by_site.csv
    data/processed/analysis/ENERGIEERZEUGER_JE_STANDORT.md
    figures/site_context/<standort>.png    (ein Kartenausschnitt je Standort)

    python scripts/site_energy_context.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from pipeline import (
    monitoring_stations, river_network, station_pairs, thermal_confounders,
)
from pipeline.config import ANALYSIS_DIR, PROJECT_ROOT

RADIUS_FILE = ANALYSIS_DIR / "plant_2x2" / "analysis_radius.json"
RESULTS = ANALYSIS_DIR / "plant_2x2" / "plant_2x2_results.csv"
OUT_CSV = ANALYSIS_DIR / "plant_2x2" / "energy_producers_by_site.csv"
OUT_MD = ANALYSIS_DIR / "ENERGIEERZEUGER_JE_STANDORT.md"
FIG_DIR = PROJECT_ROOT / "figures" / "site_context"

DEFAULT_RADIUS_KM = 50.0
MIN_CAPACITY_MW = 10.0
MAX_PAIR_KM = 120.0

RIVER_DE = {"Rhine": "Rhein", "Danube": "Donau", "Main": "Main", "Neckar": "Neckar",
            "Isar": "Isar", "Weser": "Weser", "Elbe": "Elbe", "Ems": "Ems"}

COOLING_COLOR = {"ja": "#c53030", "nein": "#2f855a",
                 "unwahrscheinlich": "#b7791f", "unklar": "#718096"}


def analysis_radius() -> float:
    if RADIUS_FILE.exists():
        return float(json.loads(RADIUS_FILE.read_text(encoding="utf-8"))["radius_km"])
    return DEFAULT_RADIUS_KM


def reference_gauges(stations: pd.DataFrame, pairs: pd.DataFrame) -> dict:
    """Je Standort das Pegelpaar, auf das sich die Entfernungen beziehen.

    Bevorzugt das Paar, das die Temperatur-Schätzung tatsächlich benutzt. Wo
    nichts schätzbar war (Biblis, Unterweser, …), wird auf den nächsten
    verfügbaren Pegel je Seite zurückgefallen, damit die Tabelle trotzdem eine
    Bezugsgröße hat — dann ausdrücklich markiert.
    """
    used: dict = {}
    if RESULTS.exists():
        results = pd.read_csv(RESULTS)
        headline = results[
            results["spec"].eq("nearest_downstream")
            & results["outcome"].eq("water_temperature")
            & results["sample"].eq("all_year")
        ]
        for _, row in headline.drop_duplicates("site").iterrows():
            used[row["site"]] = (row["upstream_station"], row["downstream_station"], True)

    by_name = stations.set_index("station_name")
    out: dict = {}
    for site in station_pairs.plant_sites():
        entry = used.get(site.site)
        if entry is None:
            clean = pairs[(pairs["site"] == site.site) & pairs["clean"]]
            ups = clean[clean["role"] == "upstream"].sort_values("distance_km")
            downs = clean[clean["role"] == "downstream"].sort_values("distance_km")
            entry = (
                ups["station_name"].iloc[0] if not ups.empty else None,
                downs["station_name"].iloc[0] if not downs.empty else None,
                False,
            )
        up_name, down_name, estimated = entry
        out[site.site] = {
            "upstream_station": up_name,
            "downstream_station": down_name,
            "upstream_km": float(by_name.loc[up_name, "river_km"]) if up_name in by_name.index else None,
            "downstream_km": float(by_name.loc[down_name, "river_km"]) if down_name in by_name.index else None,
            "from_estimation": estimated,
        }
    return out


# Unterhalb dieses Abstands ist "ober-" oder "unterhalb" nicht mehr sinnvoll:
# mehrere Anlagen teilen sich denselben Industriestandort (RWE Emsland steht auf
# denselben Koordinaten wie das Kernkraftwerk), und die Projektion auf die
# Flussachse ist ohnehin nur auf einige hundert Meter genau.
SAME_LOCATION_KM = 0.5


def _side(plant_km: float, reference_km: Optional[float]) -> str:
    """Liegt die Anlage ober- oder unterhalb eines Bezugspunkts?"""
    if reference_km is None or pd.isna(reference_km):
        return ""
    if abs(plant_km - reference_km) < SAME_LOCATION_KM:
        return "am Standort"
    # Flusskilometer zählen ab der Mündung: größer = weiter flussaufwärts.
    return "upstream" if plant_km > reference_km else "downstream"


def _distance(plant_km: float, reference_km: Optional[float]) -> Optional[float]:
    if reference_km is None or pd.isna(reference_km):
        return None
    return round(abs(plant_km - reference_km), 1)


def build_table(radius_km: float) -> pd.DataFrame:
    producers = thermal_confounders.load_river_energy_producers(min_capacity_mw=MIN_CAPACITY_MW)
    producers = producers[~producers["is_nuclear"]]
    stations = monitoring_stations.all_stations()
    pairs = station_pairs.candidate_pairs(stations, max_km=MAX_PAIR_KM)
    gauges = reference_gauges(stations, pairs)

    rows = []
    for site in station_pairs.plant_sites():
        reference = gauges.get(site.site, {})
        up_km = reference.get("upstream_km")
        down_km = reference.get("downstream_km")

        # Der Suchradius deckt mindestens die Analysereichweite ab und immer die
        # gesamte Messstrecke, auch wenn ein Pegel weiter entfernt liegt.
        reach = [k for k in (up_km, down_km) if k is not None and not pd.isna(k)]
        span = max((abs(k - site.river_km) for k in reach), default=0.0)
        search_km = max(radius_km, span)

        on_river = producers[producers["river"].eq(site.river)].copy()
        on_river["distance_to_npp_km"] = (on_river["river_km"] - site.river_km).abs().round(1)
        near = on_river[on_river["distance_to_npp_km"] <= search_km]

        for plant in near.itertuples():
            between = (
                up_km is not None and down_km is not None
                and min(up_km, down_km) <= plant.river_km <= max(up_km, down_km)
            )
            rows.append({
                "npp_site": site.site,
                "npp_river": RIVER_DE.get(site.river, site.river),
                "npp_shutdowns": ", ".join(str(y) for y in site.events),
                "npp_latitude": round(site.latitude, 5),
                "npp_longitude": round(site.longitude, 5),
                "npp_river_km": round(site.river_km, 1),
                "producer": plant.plant,
                "producer_city": plant.city,
                "producer_company": plant.company,
                "producer_state": plant.state,
                "producer_latitude": round(plant.latitude, 5),
                "producer_longitude": round(plant.longitude, 5),
                "producer_river_km": round(plant.river_km, 1),
                "distance_to_npp_km": plant.distance_to_npp_km,
                "side_of_npp": _side(plant.river_km, site.river_km),
                "upstream_station": reference.get("upstream_station"),
                "distance_to_upstream_station_km": _distance(plant.river_km, up_km),
                "side_of_upstream_station": _side(plant.river_km, up_km),
                "downstream_station": reference.get("downstream_station"),
                "distance_to_downstream_station_km": _distance(plant.river_km, down_km),
                "side_of_downstream_station": _side(plant.river_km, down_km),
                "between_the_gauges": between,
                "technology": plant.technology,
                "energy_source": plant.energy_source,
                "chp": plant.chp,
                "capacity_net_mw": plant.capacity_net_bnetza,
                "commissioned_year": plant.commissioned_year,
                "shutdown_year": plant.shutdown_year,
                "status": plant.status,
                "uses_river_cooling_water": plant.uses_river_cooling_water,
                "cooling_water_reason": plant.cooling_water_reason,
                "gauges_from_estimation": reference.get("from_estimation", False),
                "search_radius_km": round(search_km, 1),
            })

    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    return frame.sort_values(["npp_site", "producer_river_km"], ascending=[True, False]).reset_index(drop=True)


# --------------------------------------------------------------------------
# Karte je Standort
# --------------------------------------------------------------------------
def _stem_lonlat(river: str):
    stem = river_network.study_river_stems()[river]
    geo = gpd.GeoSeries([stem.line], crs=river_network.METRIC_CRS).to_crs(river_network.GEO_CRS).iloc[0]
    return np.array(geo.coords)


def _group_colocated(subset: pd.DataFrame) -> pd.DataFrame:
    """Anlagen am selben Ort zu einer Beschriftung zusammenfassen.

    An Industriestandorten stehen mehrere Blöcke auf denselben Koordinaten
    (Dingolfing, Mannheim, Lingen). Einzeln beschriftet überlagern sie sich zu
    Brei; zusammengefasst bleibt die Karte lesbar und die Summe der Leistung ist
    ohnehin die relevante Größe.
    """
    grouped = subset.groupby(
        ["producer_latitude", "producer_longitude"], as_index=False
    ).agg(
        blocks=("producer", "size"),
        producer_river_km=("producer_river_km", "first"),
        producer=("producer", lambda s: s.iloc[0]),
        producer_city=("producer_city", "first"),
        capacity_net_mw=("capacity_net_mw", "sum"),
        distance_to_npp_km=("distance_to_npp_km", "first"),
        side_of_npp=("side_of_npp", "first"),
        energy_source=("energy_source", lambda s: " / ".join(sorted(set(s)))),
        uses_river_cooling_water=(
            "uses_river_cooling_water",
            lambda s: "ja" if (s == "ja").any() else s.iloc[0],
        ),
        between_the_gauges=("between_the_gauges", "any"),
    )
    # Auf der Karte nur Ort, Leistung und Abstand. Energieträger und Blockzahl
    # stehen in der Flusskilometer-Leiste und in der Tabelle; lange Kästen
    # verdecken auf einem gewundenen Flusslauf sofort die Nachbarn.
    grouped["label"] = grouped.apply(
        lambda r: (f"{r['producer_city']}"
                   + (f" ({r['blocks']}x)" if r["blocks"] > 1 else "")
                   + f", {r['capacity_net_mw']:.0f} MW"
                   + f"\n{r['distance_to_npp_km']:.0f} km "
                   + ("↑" if r["side_of_npp"] == "upstream" else "↓") + " vom AKW"),
        axis=1,
    )
    return grouped


def plot_site(site, table: pd.DataFrame, stations: pd.DataFrame, reference: dict) -> None:
    subset = table[table["npp_site"] == site.site]
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    lons = [site.longitude] + list(subset["producer_longitude"])
    lats = [site.latitude] + list(subset["producer_latitude"])
    gauge_rows = stations[stations["station_name"].isin(
        [reference.get("upstream_station"), reference.get("downstream_station")])]
    lons += list(gauge_rows["longitude"])
    lats += list(gauge_rows["latitude"])

    pad = max(0.09, max(max(lons) - min(lons), max(lats) - min(lats)) * 0.14)
    xmin, xmax = min(lons) - pad, max(lons) + pad
    ymin, ymax = min(lats) - pad, max(lats) + pad

    figure = plt.figure(figsize=(12.5, 10.4), dpi=160)
    grid = figure.add_gridspec(2, 1, height_ratios=[3.1, 1.0], hspace=0.30)
    axis = figure.add_subplot(grid[0])
    strip = figure.add_subplot(grid[1])

    coords = _stem_lonlat(site.river)
    keep = ((coords[:, 0] > xmin - 0.5) & (coords[:, 0] < xmax + 0.5)
            & (coords[:, 1] > ymin - 0.5) & (coords[:, 1] < ymax + 0.5))
    visible = coords[keep]
    if len(visible) > 1:
        axis.plot(visible[:, 0], visible[:, 1], color="#5aa9dd", lw=3.0, alpha=0.95,
                  zorder=1, solid_capstyle="round")
        for fraction in (0.2, 0.5, 0.8):
            index = min(int(fraction * (len(visible) - 2)), len(visible) - 2)
            axis.annotate("", xy=visible[index + 1], xytext=visible[index], zorder=2,
                          arrowprops=dict(arrowstyle="-|>", color="#2f7fb5", lw=1.7,
                                          mutation_scale=17))

    # Messstellen
    for gauge in gauge_rows.itertuples():
        role = ("UP (Kontrolle)" if gauge.station_name == reference.get("upstream_station")
                else "DOWN (behandelt)")
        colour = "#1f6fd0" if role.startswith("UP") else "#d13438"
        axis.scatter([gauge.longitude], [gauge.latitude], s=210, c=colour, marker="o",
                     edgecolors="#111111", linewidths=2.2, zorder=8)
        axis.annotate(f"{role}\n{gauge.station_name.title()[:26]}",
                      (gauge.longitude, gauge.latitude), textcoords="offset points",
                      xytext=(10, 6), fontsize=8.6, weight="bold", color="#111111", zorder=9,
                      bbox=dict(boxstyle="round,pad=0.16", fc="white", ec=colour, lw=0.9, alpha=0.9))

    # Andere Energieerzeuger, ko-lokierte Blöcke zusammengefasst
    grouped = _group_colocated(subset)
    for index, plant in enumerate(grouped.itertuples()):
        colour = COOLING_COLOR.get(plant.uses_river_cooling_water, "#718096")
        marker = "P" if plant.uses_river_cooling_water == "ja" else "v"
        axis.scatter([plant.producer_longitude], [plant.producer_latitude],
                     s=150 if plant.between_the_gauges else 110, c=colour,
                     marker=marker, edgecolors="#111111" if plant.between_the_gauges else "white",
                     linewidths=1.6 if plant.between_the_gauges else 1.0, zorder=6)
        # Beschriftungen abwechselnd ober- und unterhalb, damit sie sich auf dem
        # dicht besetzten Flusslauf nicht gegenseitig verdecken.
        offset = (9, 8) if index % 2 == 0 else (9, -30)
        axis.annotate(plant.label, (plant.producer_longitude, plant.producer_latitude),
                      textcoords="offset points", xytext=offset, fontsize=6.8,
                      color=colour, zorder=7,
                      bbox=dict(boxstyle="round,pad=0.14", fc="white",
                                ec=colour if plant.between_the_gauges else "none",
                                lw=0.7, alpha=0.85))

    axis.scatter([site.longitude], [site.latitude], s=430, c="#2d3748", marker="*",
                 edgecolors="white", linewidths=1.6, zorder=10)
    axis.annotate(f"{site.site}\n{site.latitude:.4f}°N, {site.longitude:.4f}°O",
                  (site.longitude, site.latitude), textcoords="offset points",
                  xytext=(0, 26), ha="center", fontsize=10, weight="bold", zorder=11,
                  bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#2d3748", lw=0.9, alpha=0.94))

    axis.set_xlim(xmin, xmax)
    axis.set_ylim(ymin, ymax)
    axis.set_aspect(1 / np.cos(np.deg2rad(site.latitude)))
    axis.set_xlabel("Länge (°O)", fontsize=9)
    axis.set_ylabel("Breite (°N)", fontsize=9)
    axis.tick_params(labelsize=8)
    axis.spines[["top", "right"]].set_visible(False)

    events = ", ".join(str(y) for y in site.events) or "—"
    radius = subset["search_radius_km"].iloc[0] if not subset.empty else DEFAULT_RADIUS_KM
    axis.set_title(f"{site.site} ({RIVER_DE.get(site.river, site.river)}) — Abschaltung {events}",
                   fontsize=14, loc="left", weight="bold", pad=16)
    note = "" if reference.get("from_estimation") else "  (kein schätzbares Paar — nächste verfügbare Pegel)"
    axis.text(0, 1.012,
              f"Energieerzeuger ≥ {MIN_CAPACITY_MW:.0f} MW innerhalb {radius:.0f} km "
              f"entlang des Flusses, nicht Luftlinie.{note}",
              transform=axis.transAxes, fontsize=8.8, color="#555555", va="bottom")

    # --- Flusskilometer-Leiste -------------------------------------------
    # Die Karte zeigt, wo etwas liegt; diese Leiste zeigt eindeutig, in welcher
    # Reihenfolge am Fluss und wie weit auseinander. Bei ko-lokierten Blöcken
    # und engen Flussschleifen ist das die klarere Darstellung.
    up_km, down_km = reference.get("upstream_km"), reference.get("downstream_km")
    marks = list(grouped["producer_river_km"]) if "producer_river_km" in grouped else []
    if not marks:
        marks = list(subset["producer_river_km"])
    positions = marks + [site.river_km] + [k for k in (up_km, down_km) if k is not None]
    low, high = min(positions), max(positions)
    margin = max(2.0, (high - low) * 0.06)

    strip.axhline(0, color="#5aa9dd", lw=4, zorder=1, solid_capstyle="round")
    strip.annotate("", xy=(low - margin, 0), xytext=(low - margin + (high - low) * 0.07, 0),
                   arrowprops=dict(arrowstyle="-|>", color="#2f7fb5", lw=2, mutation_scale=18),
                   zorder=2)
    strip.text(low - margin, 0.42, "flussabwärts", fontsize=8, color="#2f7fb5", ha="left")

    if up_km is not None and down_km is not None:
        strip.axvspan(min(up_km, down_km), max(up_km, down_km), color="#fed7d7",
                      alpha=0.45, zorder=0)
        strip.text((up_km + down_km) / 2, -0.78, "Messstrecke (behandelt)",
                   fontsize=8, ha="center", color="#9b2c2c")

    for km, colour, label in [
        (up_km, "#1f6fd0", f"UP\n{reference.get('upstream_station') or ''}"),
        (down_km, "#d13438", f"DOWN\n{reference.get('downstream_station') or ''}"),
    ]:
        if km is None:
            continue
        strip.scatter([km], [0], s=180, c=colour, marker="o", edgecolors="#111111",
                      linewidths=1.8, zorder=5)
        strip.annotate(label[:34], (km, 0), textcoords="offset points", xytext=(0, 16),
                       ha="center", fontsize=7.6, weight="bold", color=colour, zorder=6)

    strip.scatter([site.river_km], [0], s=340, c="#2d3748", marker="*",
                  edgecolors="white", linewidths=1.3, zorder=7)
    strip.annotate(site.site, (site.river_km, 0), textcoords="offset points",
                   xytext=(0, -26), ha="center", fontsize=8.6, weight="bold", zorder=8)

    for index, plant in enumerate(grouped.itertuples()):
        colour = COOLING_COLOR.get(plant.uses_river_cooling_water, "#718096")
        marker = "P" if plant.uses_river_cooling_water == "ja" else "v"
        strip.scatter([plant.producer_river_km], [0], s=90, c=colour, marker=marker,
                      edgecolors="white", linewidths=0.8, zorder=4)
        strip.annotate(f"{plant.producer_city}\n{plant.capacity_net_mw:.0f} MW",
                       (plant.producer_river_km, 0), textcoords="offset points",
                       xytext=(0, 30 if index % 2 == 0 else -46), ha="center",
                       fontsize=6.4, color=colour, zorder=5)

    strip.set_xlim(high + margin, low - margin)  # flussabwärts nach rechts
    strip.set_ylim(-1.35, 1.35)
    strip.set_yticks([])
    strip.set_xlabel(f"Fluss-km ({RIVER_DE.get(site.river, site.river)}, ab Mündung)", fontsize=9)
    strip.tick_params(labelsize=8)
    strip.spines[["top", "right", "left"]].set_visible(False)

    handles = [
        Line2D([], [], color="#1f6fd0", marker="o", ls="", ms=11, mec="#111111", mew=2,
               label="Messstelle upstream (Kontrolle)"),
        Line2D([], [], color="#d13438", marker="o", ls="", ms=11, mec="#111111", mew=2,
               label="Messstelle downstream (behandelt)"),
        Line2D([], [], color=COOLING_COLOR["ja"], marker="P", ls="", ms=11,
               label="Erzeuger mit Flusskühlwasser"),
        Line2D([], [], color=COOLING_COLOR["nein"], marker="v", ls="", ms=11,
               label="Erzeuger ohne Wärmeeinleitung (Wasserkraft / Gasturbine)"),
        Line2D([], [], color="#2d3748", marker="*", ls="", ms=17, label="Kernkraftwerk"),
        Line2D([], [], color="#5aa9dd", lw=3, label="Flusslauf mit Fließrichtung"),
    ]
    figure.legend(handles=handles, loc="lower center", ncol=3, fontsize=8.6,
                  frameon=False, bbox_to_anchor=(0.5, -0.035))

    figure.tight_layout(rect=(0, 0.03, 1, 1))
    name = site.site.lower().replace(" ", "_")
    figure.savefig(FIG_DIR / f"{name}.png", bbox_inches="tight", facecolor="white")
    plt.close(figure)


def write_markdown(table: pd.DataFrame, radius_km: float) -> None:
    lines = [
        "# Energieerzeuger am Fluss je Kernkraftwerksstandort",
        "",
        "*Erzeugt von `scripts/site_energy_context.py`. Alle Entfernungen sind*",
        "***Flusskilometer entlang des Laufs***, *nicht Luftlinie — berechnet auf dem*",
        "*HydroRIVERS-Netz (siehe METHODS.md §4.7).*",
        "",
        f"Aufgenommen sind alle Anlagen ab {MIN_CAPACITY_MW:.0f} MW auf demselben Fluss "
        f"innerhalb von {radius_km:.0f} km entlang des Laufs vom Kernkraftwerk; wo ein "
        "Messpegel weiter entfernt liegt, wird der Radius auf die gesamte Messstrecke "
        "erweitert. Kernkraftwerke selbst sind ausgenommen.",
        "",
        "**Kühlwasserspalte:** eine Einschätzung aus der Technologie, keine "
        "Genehmigungsauskunft. Dampfturbine und GuD haben einen Kondensator und brauchen "
        "eine Wärmesenke; offene Gasturbinen und Wasserkraft nicht.",
        "",
        "**Was für das 2×2 zählt:** nur Anlagen *zwischen* den beiden Messstellen "
        "(`zwischen den Pegeln = ja`) sitzen in der behandelten Strecke. Alles oberhalb "
        "der Kontrollmessstelle wärmt beide Pegel gleich und fällt aus der Differenz.",
        "",
        f"Vollständige Daten: `plant_2x2/energy_producers_by_site.csv`. "
        f"Karten: `figures/site_context/`.",
        "",
    ]

    for site_name, group in table.groupby("npp_site", sort=True):
        first = group.iloc[0]
        lines += [
            f"## {site_name} ({first['npp_river']})",
            "",
            f"**Kernkraftwerk:** {first['npp_latitude']}° N, {first['npp_longitude']}° O · "
            f"Fluss-km {first['npp_river_km']} · Abschaltung {first['npp_shutdowns'] or '—'}",
            "",
        ]
        up, down = first["upstream_station"], first["downstream_station"]
        marker = "" if first["gauges_from_estimation"] else " *(kein schätzbares Paar — nächste verfügbare Pegel)*"
        lines += [
            f"**Bezugspegel:** upstream `{up or '—'}`, downstream `{down or '—'}`{marker}",
            "",
            "| Erzeuger | Ort | Koordinaten | km zum AKW | Lage zum AKW | km zu UP | Lage zu UP | km zu DOWN | Lage zu DOWN | zwischen den Pegeln | Erzeugungsart | MW | Flusskühlwasser |",
            "|---|---|---|---:|---|---:|---|---:|---|:---:|---|---:|---|",
        ]
        for row in group.itertuples():
            coords = f"{row.producer_latitude}, {row.producer_longitude}"
            technology = f"{row.technology} ({row.energy_source})"
            if str(row.chp).lower() == "yes":
                technology += ", KWK"
            lines.append(
                f"| {row.producer} | {row.producer_city} | {coords} | "
                f"{row.distance_to_npp_km:.1f} | {row.side_of_npp} | "
                f"{'' if row.distance_to_upstream_station_km is None or pd.isna(row.distance_to_upstream_station_km) else f'{row.distance_to_upstream_station_km:.1f}'} | "
                f"{row.side_of_upstream_station} | "
                f"{'' if row.distance_to_downstream_station_km is None or pd.isna(row.distance_to_downstream_station_km) else f'{row.distance_to_downstream_station_km:.1f}'} | "
                f"{row.side_of_downstream_station} | "
                f"{'**ja**' if row.between_the_gauges else 'nein'} | {technology} | "
                f"{row.capacity_net_mw:.1f} | {row.uses_river_cooling_water} |"
            )
        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    # Die Konsole ist unter Windows cp1252; die Tabellen enthalten aber Zeichen
    # wie "≥" und deutsche Umlaute in Ortsnamen.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    radius = analysis_radius()
    table = build_table(radius)
    if table.empty:
        print("site_energy_context: nichts gefunden.")
        return 1

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT_CSV, index=False)
    write_markdown(table, radius)

    stations = monitoring_stations.all_stations()
    pairs = station_pairs.candidate_pairs(stations, max_km=MAX_PAIR_KM)
    gauges = reference_gauges(stations, pairs)
    for site in station_pairs.plant_sites():
        if (table["npp_site"] == site.site).any():
            plot_site(site, table, stations, gauges.get(site.site, {}))

    pd.set_option("display.width", 300)
    pd.set_option("display.max_rows", 300)
    print(f"Energieerzeuger ≥ {MIN_CAPACITY_MW:.0f} MW je Standort "
          f"(Radius {radius:.0f} km entlang des Flusses)\n")
    print(table.groupby(["npp_site", "uses_river_cooling_water"]).size().to_string())
    print("\nAnlagen zwischen den beiden Messstellen (nur diese können das 2x2 stören):\n")
    between = table[table["between_the_gauges"]]
    if between.empty:
        print("  keine")
    else:
        print(between[["npp_site", "producer", "producer_city", "distance_to_npp_km",
                       "technology", "energy_source", "capacity_net_mw",
                       "uses_river_cooling_water"]].to_string(index=False))
    print(f"\nGeschrieben: {OUT_CSV}\n            {OUT_MD}\n            {FIG_DIR}/<standort>.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
