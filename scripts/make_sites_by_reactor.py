"""Ein Kartenausschnitt pro Standort: die Messstellen, die das 2x2 benutzt.

Jedes Panel zoomt auf einen Kernkraftwerksstandort und zeigt den echten
Flusslauf (HydroRIVERS v1.0, tidale Abschnitte aus OpenStreetMap) mit allen
Messstellen im Paarungsradius. Upstream (Kontrolle) und downstream (behandelt)
sind farblich getrennt, jede Station ist **mit Namen und Flusskilometer-Abstand
beschriftet**, und das für die Schätzung gewählte Paar ist hervorgehoben.

Oben/unten heißt hier oben/unten *am Fluss*, aus dem Flusskilometer entlang der
Achse — nicht aus einer geschätzten Fließrichtung.

    python scripts/make_sites_by_reactor.py -> figures/study_sites_by_reactor.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pipeline import monitoring_stations, river_network, station_pairs  # noqa: E402

OUT = ROOT / "figures" / "study_sites_by_reactor.png"

MAX_PAIR_KM = 120.0
PANEL_PAD_DEG = 0.16

UPSTREAM_COLOR = "#1f6fd0"
DOWNSTREAM_COLOR = "#d13438"
RIVER_COLOR = "#5aa9dd"
GKD_EDGE = "#0f9d58"

RIVER_DE = {"Rhine": "Rhein", "Danube": "Donau", "Main": "Main", "Neckar": "Neckar",
            "Isar": "Isar", "Weser": "Weser", "Elbe": "Elbe", "Ems": "Ems"}


def _stem_lonlat(river: str):
    stem = river_network.study_river_stems()[river]
    geo = gpd.GeoSeries([stem.line], crs=river_network.METRIC_CRS).to_crs(river_network.GEO_CRS).iloc[0]
    return np.array(geo.coords)


def main() -> int:
    sites = station_pairs.plant_sites()
    stations = monitoring_stations.all_stations()
    if stations.empty:
        print("make_sites_by_reactor: keine Messstellen gefunden.")
        return 1
    pairs = station_pairs.candidate_pairs(stations, max_km=MAX_PAIR_KM)

    panels = [s for s in sites if not pairs[pairs["site"] == s.site].empty]
    columns = 2
    rows = int(np.ceil(len(panels) / columns))
    figure, axes = plt.subplots(rows, columns, figsize=(15.5, 4.6 * rows), dpi=160)
    axes = np.atleast_1d(axes).ravel()

    for axis, site in zip(axes, panels):
        subset = pairs[pairs["site"] == site.site].drop_duplicates("station_id")
        merged = subset.merge(
            stations[["station_id", "latitude", "longitude", "source", "year_min", "year_max"]],
            on="station_id", how="left",
        )

        coords = _stem_lonlat(site.river)
        span = max(
            abs(merged["longitude"].max() - merged["longitude"].min()),
            abs(merged["latitude"].max() - merged["latitude"].min()),
        )
        pad = max(PANEL_PAD_DEG, span * 0.12)
        xmin = min(merged["longitude"].min(), site.longitude) - pad
        xmax = max(merged["longitude"].max(), site.longitude) + pad
        ymin = min(merged["latitude"].min(), site.latitude) - pad
        ymax = max(merged["latitude"].max(), site.latitude) + pad

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

        # Das von der Schätzung gewählte Paar (nächste saubere Station je Seite).
        chosen = set()
        for event in site.events:
            best = station_pairs.best_pair(pairs, site.site, event)
            if best:
                chosen |= {best["upstream"]["station_id"], best["downstream"]["station_id"]}

        for row in merged.itertuples():
            colour = UPSTREAM_COLOR if row.role == "upstream" else DOWNSTREAM_COLOR
            picked = row.station_id in chosen
            axis.scatter([row.longitude], [row.latitude],
                         s=125 if picked else 46, c=colour, marker="o",
                         edgecolors=GKD_EDGE if row.source == "gkd" else "white",
                         linewidths=2.0 if row.source == "gkd" else 0.7,
                         zorder=6 if picked else 4)
            label = f"{row.station_name.title()[:22]}\n{row.distance_km:.0f} km {'↑' if row.role == 'upstream' else '↓'}"
            axis.annotate(label, (row.longitude, row.latitude),
                          textcoords="offset points", xytext=(7, 5),
                          fontsize=7.4 if picked else 6.4,
                          weight="bold" if picked else "normal",
                          color="#1a1a1a" if picked else "#5a5a5a", zorder=7,
                          bbox=dict(boxstyle="round,pad=0.14", fc="white", ec="none",
                                    alpha=0.82 if picked else 0.6))

        axis.scatter([site.longitude], [site.latitude], s=280, c="#2d3748", marker="*",
                     edgecolors="white", linewidths=1.4, zorder=8)
        axis.annotate(site.site, (site.longitude, site.latitude),
                      textcoords="offset points", xytext=(0, -20), ha="center",
                      fontsize=10, weight="bold", color="#1a1a1a", zorder=9,
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
        Line2D([], [], color="#888888", marker="o", ls="", ms=11, mec=GKD_EDGE, mew=2.2,
               label="GKD Bayern — Tagesmittel (vor 2011 nutzbar)"),
        Line2D([], [], color="#2d3748", marker="*", ls="", ms=15, label="Kernkraftwerksstandort"),
        Line2D([], [], color=RIVER_COLOR, lw=2.6, label="Flusslauf (HydroRIVERS) mit Fließrichtung"),
    ]
    figure.legend(handles=handles, loc="lower center", ncol=5, fontsize=9.5,
                  frameon=False, bbox_to_anchor=(0.5, -0.012))
    figure.suptitle(
        "Messstellen je Standort — Abstand entlang des Flusses, nicht Luftlinie",
        fontsize=15, weight="bold", x=0.012, ha="left", y=1.002,
    )
    figure.text(0.012, 0.994,
                "Große Marker = das Paar, das die 2x2-Schätzung verwendet (jeweils die nächste "
                "unbelastete Station ober- und unterhalb). ↑ upstream, ↓ downstream.",
                fontsize=9.2, color="#555555", va="top", ha="left")
    figure.tight_layout(rect=(0, 0.022, 1, 0.985))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUT, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    print(f"make_sites_by_reactor: {OUT} geschrieben ({len(panels)} Standorte)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
