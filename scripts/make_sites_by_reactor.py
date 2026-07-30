"""Ein Kartenausschnitt pro Standort: die Messstellen, die das 2x2 benutzt.

Jedes Panel zoomt auf einen Kernkraftwerksstandort und zeigt den echten
Flusslauf (HydroRIVERS v1.0, tidale Abschnitte aus OpenStreetMap) mit allen
Messstellen im Paarungsradius. Upstream (Kontrolle) und downstream (behandelt)
sind farblich getrennt, jede Station ist mit Namen und Flusskilometer-Abstand
beschriftet, und das **für die Schätzung tatsächlich verwendete Paar** ist
umrandet und mit UP/DOWN gekennzeichnet.

Zusätzlich sind **andere thermische Kraftwerke** eingezeichnet, die Kühlwasser
aus demselben Fluss nehmen und innerhalb des Analyseradius liegen (der Radius
kommt aus scripts/distance_sensitivity.py, gemessen entlang des Flusses, nicht
Luftlinie). Kraftwerke, die sich zeitnah zur Abschaltung verändert haben, sind
als Confounder hervorgehoben.

Oben/unten heißt hier oben/unten *am Fluss*, aus dem Flusskilometer entlang der
Achse — nicht aus einer geschätzten Fließrichtung.

    python scripts/make_sites_by_reactor.py -> figures/study_sites_by_reactor.png
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pipeline import (  # noqa: E402
    monitoring_stations, river_network, station_pairs, thermal_confounders,
)
from pipeline.config import ANALYSIS_DIR  # noqa: E402

OUT = ROOT / "figures" / "study_sites_by_reactor.png"
RADIUS_FILE = ANALYSIS_DIR / "plant_2x2" / "analysis_radius.json"
RESULTS = ANALYSIS_DIR / "plant_2x2" / "plant_2x2_results.csv"

MAX_PAIR_KM = 120.0
DEFAULT_RADIUS_KM = 50.0
PANEL_PAD_DEG = 0.16

UPSTREAM_COLOR = "#1f6fd0"
DOWNSTREAM_COLOR = "#d13438"
RIVER_COLOR = "#5aa9dd"
GKD_EDGE = "#0f9d58"
PLANT_COLOR = "#7a5195"
CONFOUNDER_COLOR = "#e8730c"

RIVER_DE = {"Rhine": "Rhein", "Danube": "Donau", "Main": "Main", "Neckar": "Neckar",
            "Isar": "Isar", "Weser": "Weser", "Elbe": "Elbe", "Ems": "Ems"}


def analysis_radius() -> float:
    if RADIUS_FILE.exists():
        return float(json.loads(RADIUS_FILE.read_text(encoding="utf-8"))["radius_km"])
    return DEFAULT_RADIUS_KM


def used_station_names() -> set:
    """Namen der Pegel, die in einer berichteten Schätzung wirklich vorkommen."""
    if not RESULTS.exists():
        return set()
    results = pd.read_csv(RESULTS)
    used = results[results["spec"].isin(["nearest_downstream", "best_coverage"])]
    return set(used["upstream_station"]) | set(used["downstream_station"])


def _stem_lonlat(river: str):
    stem = river_network.study_river_stems()[river]
    geo = gpd.GeoSeries([stem.line], crs=river_network.METRIC_CRS).to_crs(river_network.GEO_CRS).iloc[0]
    return np.array(geo.coords)


def main() -> int:
    radius = analysis_radius()
    sites = station_pairs.plant_sites()
    stations = monitoring_stations.all_stations()
    if stations.empty:
        print("make_sites_by_reactor: keine Messstellen gefunden.")
        return 1
    pairs = station_pairs.candidate_pairs(stations, max_km=MAX_PAIR_KM)
    used = used_station_names()
    plants = thermal_confounders.load_thermal_plants()
    plants = plants[~plants["is_nuclear"]]

    panels = [s for s in sites if not pairs[pairs["site"] == s.site].empty]
    columns = 2
    rows = int(np.ceil(len(panels) / columns))
    figure, axes = plt.subplots(rows, columns, figsize=(15.5, 4.8 * rows), dpi=160)
    axes = np.atleast_1d(axes).ravel()

    for axis, site in zip(axes, panels):
        subset = pairs[pairs["site"] == site.site].drop_duplicates("station_id")
        merged = subset.merge(
            stations[["station_id", "latitude", "longitude", "source", "year_min", "year_max"]],
            on="station_id", how="left",
        )

        # Andere Kraftwerke am selben Fluss innerhalb des Radius um den Standort.
        near_plants = plants[
            plants["river"].eq(site.river)
            & (plants["river_km"] - site.river_km).abs().le(radius)
        ].copy()
        if not near_plants.empty:
            near_plants["changed"] = near_plants.apply(
                lambda p: any(
                    thermal_confounders._changed_near(p, year) for year in site.events
                ), axis=1,
            )

        coords = _stem_lonlat(site.river)
        lons = list(merged["longitude"]) + [site.longitude] + list(near_plants["longitude"])
        lats = list(merged["latitude"]) + [site.latitude] + list(near_plants["latitude"])
        span = max(max(lons) - min(lons), max(lats) - min(lats))
        pad = max(PANEL_PAD_DEG, span * 0.12)
        xmin, xmax = min(lons) - pad, max(lons) + pad
        ymin, ymax = min(lats) - pad, max(lats) + pad

        keep = ((coords[:, 0] > xmin - 0.6) & (coords[:, 0] < xmax + 0.6)
                & (coords[:, 1] > ymin - 0.6) & (coords[:, 1] < ymax + 0.6))
        visible = coords[keep]
        if len(visible) > 1:
            axis.plot(visible[:, 0], visible[:, 1], color=RIVER_COLOR, lw=2.6,
                      alpha=0.95, zorder=1, solid_capstyle="round")
            for fraction in (0.25, 0.55, 0.85):
                index = min(int(fraction * (len(visible) - 2)), len(visible) - 2)
                axis.annotate("", xy=visible[index + 1], xytext=visible[index], zorder=2,
                              arrowprops=dict(arrowstyle="-|>", color="#2f7fb5", lw=1.6,
                                              mutation_scale=15))

        # Andere Kraftwerke zeichnen.
        for plant in near_plants.itertuples():
            confounder = getattr(plant, "changed", False)
            axis.scatter([plant.longitude], [plant.latitude], s=105,
                         c=CONFOUNDER_COLOR if confounder else PLANT_COLOR,
                         marker="P", edgecolors="white", linewidths=1.0, zorder=5)
            axis.annotate(f"{plant.plant[:20]}\n{plant.energy_source}, {plant.capacity_net_bnetza:.0f} MW",
                          (plant.longitude, plant.latitude), textcoords="offset points",
                          xytext=(7, -12), fontsize=6.0,
                          color=CONFOUNDER_COLOR if confounder else "#5a4a6a", zorder=6,
                          bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.7))

        for row in merged.itertuples():
            colour = UPSTREAM_COLOR if row.role == "upstream" else DOWNSTREAM_COLOR
            picked = row.station_name in used
            axis.scatter([row.longitude], [row.latitude],
                         s=170 if picked else 44, c=colour, marker="o",
                         edgecolors="#111111" if picked else (
                             GKD_EDGE if row.source == "gkd" else "white"),
                         linewidths=2.2 if picked else (1.6 if row.source == "gkd" else 0.7),
                         zorder=8 if picked else 4)
            tag = ("UP (Kontrolle)" if row.role == "upstream" else "DOWN (behandelt)") if picked else ""
            label = f"{row.station_name.title()[:22]}\n{row.distance_km:.0f} km " \
                    f"{'↑' if row.role == 'upstream' else '↓'}"
            if tag:
                label = f"{tag}\n{label}"
            axis.annotate(label, (row.longitude, row.latitude),
                          textcoords="offset points", xytext=(8, 5),
                          fontsize=7.4 if picked else 6.2,
                          weight="bold" if picked else "normal",
                          color="#111111" if picked else "#6a6a6a", zorder=9,
                          bbox=dict(boxstyle="round,pad=0.15", fc="white",
                                    ec=colour if picked else "none",
                                    lw=0.8 if picked else 0, alpha=0.88 if picked else 0.6))

        axis.scatter([site.longitude], [site.latitude], s=300, c="#2d3748", marker="*",
                     edgecolors="white", linewidths=1.4, zorder=10)
        axis.annotate(site.site, (site.longitude, site.latitude),
                      textcoords="offset points", xytext=(0, -22), ha="center",
                      fontsize=10, weight="bold", color="#1a1a1a", zorder=11,
                      bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="#2d3748",
                                lw=0.7, alpha=0.92))

        axis.set_xlim(xmin, xmax)
        axis.set_ylim(ymin, ymax)
        axis.set_aspect(1 / np.cos(np.deg2rad(site.latitude)))
        events = " / ".join(str(y) for y in site.events)
        axis.set_title(f"{site.site} ({RIVER_DE.get(site.river, site.river)}) — Abschaltung {events}",
                       fontsize=11.5, loc="left", weight="bold")
        axis.tick_params(labelsize=7)
        axis.spines[["top", "right"]].set_visible(False)

    for axis in axes[len(panels):]:
        axis.axis("off")

    handles = [
        Line2D([], [], color=UPSTREAM_COLOR, marker="o", ls="", ms=9, label="upstream (Kontrolle)"),
        Line2D([], [], color=DOWNSTREAM_COLOR, marker="o", ls="", ms=9, label="downstream (behandelt)"),
        Line2D([], [], color="#888888", marker="o", ls="", ms=12, mec="#111111", mew=2.2,
               label="in der Schätzung verwendet (UP/DOWN)"),
        Line2D([], [], color=PLANT_COLOR, marker="P", ls="", ms=10,
               label=f"anderes Wärmekraftwerk am Fluss (≤ {radius:.0f} km)"),
        Line2D([], [], color=CONFOUNDER_COLOR, marker="P", ls="", ms=10,
               label="davon: zeitnah zur Abschaltung verändert"),
        Line2D([], [], color="#2d3748", marker="*", ls="", ms=15, label="Kernkraftwerksstandort"),
        Line2D([], [], color=RIVER_COLOR, lw=2.6, label="Flusslauf (HydroRIVERS) mit Fließrichtung"),
    ]
    figure.legend(handles=handles, loc="lower center", ncol=4, fontsize=9.5,
                  frameon=False, bbox_to_anchor=(0.5, -0.014))
    figure.suptitle("Messstellen je Standort — Abstand entlang des Flusses, nicht Luftlinie",
                    fontsize=15, weight="bold", x=0.012, ha="left", y=1.002)
    figure.text(0.012, 0.994,
                f"Große umrandete Marker = das Paar, das die 2x2-Schätzung verwendet. "
                f"↑ upstream, ↓ downstream. Andere Kraftwerke innerhalb {radius:.0f} km entlang "
                f"des Flusses (Radius aus der Sensitivitätsanalyse).",
                fontsize=9.2, color="#555555", va="top", ha="left")
    figure.tight_layout(rect=(0, 0.026, 1, 0.985))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUT, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    print(f"make_sites_by_reactor: {OUT} geschrieben ({len(panels)} Standorte, Radius {radius:.0f} km)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
