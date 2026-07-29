"""Nationale Studienkarte: echte Flussgeometrie, Standorte und benannte Messstellen.

Alles, was hier gezeichnet wird, ist dieselbe Geometrie, die auch die Schätzung
benutzt. Die Flussachsen stammen aus dem HydroRIVERS-v1.0-Netz (tidale Elbe und
Unterweser aus OpenStreetMap ergänzt) — keine Skizze und keine geschätzte
Fließrichtung: die Pfeile folgen der Topologie des Netzes selbst. Die
Messstellen sind die Pegel, die tatsächlich Wassertemperatur liefern, verortet
über den Flusskilometer entlang der Achse.

Jede Messstelle ist auf der Karte nummeriert und in der Tabelle darunter mit
Namen aufgeführt, damit die Karte lesbar bleibt und trotzdem jede Station
benannt ist.

    python scripts/make_study_map.py    ->  figures/study_map.png
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
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pipeline import boundaries, monitoring_stations, river_network, station_pairs  # noqa: E402

OUT = ROOT / "figures" / "study_map.png"

GROUP_STYLE = {
    "treatment": ("#d13438", "^", "Treatment — ganzer Standort 2011 aus"),
    "partial": ("#e8730c", "s", "Partial — ein Block 2011 aus"),
    "control": ("#1f6fd0", "o", "Control — durchgehend am Netz"),
    "staggered_treatment": ("#5b3fb8", "D", "Gestaffelt — Last 2015/2017 weg"),
}
SOURCE_STYLE = {
    "gkd": ("#0f9d58", "GKD Bayern — Tagesmittel, ab den 1990ern"),
    "waterbase": ("#8c8c8c", "EEA Waterbase — Stichproben, erst ab 2020"),
}
RIVER_COLOR = "#5aa9dd"
LAND_FILL = "#f5f4f0"
BORDER_COLOR = "#b9b7ae"
INK = "#111111"
RIVER_DE = {"Rhine": "Rhein", "Danube": "Donau", "Main": "Main", "Neckar": "Neckar",
            "Isar": "Isar", "Weser": "Weser", "Elbe": "Elbe", "Ems": "Ems"}


MAX_PAIR_KM = 120.0  # wie in scripts/plant_2x2_did.py


def _to_geo(line):
    return gpd.GeoSeries([line], crs=river_network.METRIC_CRS).to_crs(river_network.GEO_CRS).iloc[0]


def _label_point(points, xlim, ylim, avoid):
    """Wo der Flussname hin soll: im Ausschnitt und möglichst weit weg von den
    Standortmarkern, damit die Beschriftungen sich nicht überlagern."""
    inside = [p for p in points if xlim[0] < p[0] < xlim[1] and ylim[0] < p[1] < ylim[1]]
    if not inside:
        return None
    candidates = inside[:: max(1, len(inside) // 40)] or inside
    if not avoid:
        return candidates[len(candidates) // 3]
    return max(
        candidates,
        key=lambda p: min((p[0] - x) ** 2 + (p[1] - y) ** 2 for x, y in avoid),
    )


def main() -> int:
    stems = river_network.study_river_stems()
    sites = station_pairs.plant_sites()
    stations = monitoring_stations.all_stations()
    if stations.empty:
        print("make_study_map: keine Messstellen gefunden.")
        return 1

    # Nur Messstellen zeigen, die für die Schätzung überhaupt in Frage kommen:
    # auf einem Studienfluss und höchstens MAX_PAIR_KM entlang des Laufs von
    # einem Standort entfernt. Alles andere macht die Karte nur voll.
    usable = station_pairs.candidate_pairs(stations, max_km=MAX_PAIR_KM)
    if not usable.empty:
        stations = stations[stations["station_id"].isin(set(usable["station_id"]))].copy()

    # Messstellen flussweise von oben nach unten durchnummerieren.
    stations = stations.sort_values(["river", "river_km"], ascending=[True, False]).reset_index(drop=True)
    stations["label"] = np.arange(1, len(stations) + 1)

    xlim, ylim = (5.6, 14.6), (47.2, 54.8)
    figure = plt.figure(figsize=(13.0, 15.0), dpi=170)
    grid = figure.add_gridspec(2, 1, height_ratios=[3.4, 1.0], hspace=0.10)
    axis = figure.add_subplot(grid[0])
    table_axis = figure.add_subplot(grid[1])
    table_axis.axis("off")

    site_points = [(s.longitude, s.latitude) for s in sites]

    # --- Staatsgrenze ------------------------------------------------------
    # Die Flüsse laufen über die Grenze hinaus (Rhein in die Niederlande, Donau
    # nach Österreich); ohne Umriss ist nicht erkennbar, welcher Abschnitt im
    # Sample liegt.
    for ring in boundaries.germany_rings():
        axis.fill([p[0] for p in ring], [p[1] for p in ring],
                  facecolor=LAND_FILL, edgecolor=BORDER_COLOR, linewidth=1.0, zorder=0)

    # --- Flüsse aus dem echten Netz --------------------------------------
    for river, stem in stems.items():
        geo = _to_geo(stem.line)
        points = list(geo.coords)
        lon, lat = zip(*points)
        axis.plot(lon, lat, color=RIVER_COLOR, lw=2.0, alpha=0.92, zorder=1,
                  solid_capstyle="round")
        for fraction in (0.4, 0.68, 0.9):
            index = min(int(fraction * (len(points) - 2)), len(points) - 2)
            (x0, y0), (x1, y1) = points[index], points[index + 1]
            axis.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=2,
                          arrowprops=dict(arrowstyle="-|>", color="#2f7fb5", lw=1.5,
                                          mutation_scale=13))
        anchor = _label_point(points, xlim, ylim, site_points)
        if anchor is not None:
            axis.text(anchor[0], anchor[1], RIVER_DE.get(river, river), fontsize=10.5,
                      color="#1f6fa8", ha="center", va="bottom", weight="bold", zorder=3,
                      bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))

    # --- Messstellen ------------------------------------------------------
    for source, (colour, _) in SOURCE_STYLE.items():
        subset = stations[stations["source"] == source]
        if subset.empty:
            continue
        axis.scatter(subset["longitude"], subset["latitude"], s=26, c=colour,
                     marker="o", edgecolors="white", linewidths=0.6, zorder=4)
        for row in subset.itertuples():
            axis.annotate(str(row.label), (row.longitude, row.latitude),
                          textcoords="offset points", xytext=(4.5, 3.0),
                          fontsize=6.4, color="#3a3a3a", zorder=5)

    # --- Kraftwerksstandorte ---------------------------------------------
    for site in sites:
        group = min((b.group for b in site.blocks), key=list(GROUP_STYLE).index)
        colour, marker, _ = GROUP_STYLE[group]
        axis.scatter([site.longitude], [site.latitude], s=190, c=colour, marker=marker,
                     edgecolors="white", linewidths=1.3, zorder=6)
        axis.annotate(site.site, (site.longitude, site.latitude),
                      textcoords="offset points", xytext=(11, -13),
                      fontsize=9.5, weight="bold", color=INK, zorder=8,
                      bbox=dict(boxstyle="round,pad=0.16", fc="white", ec="none", alpha=0.8))

    axis.set_xlim(*xlim)
    axis.set_ylim(*ylim)
    axis.set_aspect(1 / np.cos(np.deg2rad(51)))
    axis.set_xlabel("Länge (°O)", fontsize=9)
    axis.set_ylabel("Breite (°N)", fontsize=9)
    axis.tick_params(labelsize=8)
    axis.spines[["top", "right"]].set_visible(False)
    axis.set_title("Kernkraftwerksstandorte, Studienflüsse und Wassertemperatur-Messstellen",
                   fontsize=15, loc="left", weight="bold", pad=26)
    axis.text(0, 1.012,
              "Flussachsen: HydroRIVERS v1.0 (tidale Elbe und Unterweser aus OpenStreetMap); "
              f"Pfeile = Fließrichtung aus der Netztopologie. Gezeigt sind nur Messstellen "
              f"≤ {MAX_PAIR_KM:.0f} km entlang des Flusses von einem Standort.",
              transform=axis.transAxes, fontsize=8.6, color="#555555", va="bottom")

    handles = [Line2D([], [], color=c, marker=m, ls="", ms=10, label=t)
               for c, m, t in GROUP_STYLE.values()]
    handles += [Line2D([], [], color=c, marker="o", ls="", ms=7, label=t)
                for c, t in SOURCE_STYLE.values()]
    handles += [
        Line2D([], [], color=RIVER_COLOR, lw=2, label="Studienfluss (Hauptlauf)"),
        Patch(facecolor=LAND_FILL, edgecolor=BORDER_COLOR, label="Deutschland (Staatsgrenze)"),
    ]
    axis.legend(handles=handles, loc="upper left", fontsize=8.6, frameon=False,
                borderpad=0.4, labelspacing=0.55)

    # --- Namenstabelle unter der Karte ------------------------------------
    table_axis.set_title("Messstellen (Nummern wie in der Karte)", fontsize=11.5,
                         loc="left", weight="bold", pad=10)
    columns = 3
    per_column = int(np.ceil(len(stations) / columns))
    header = f"{'#':>3s} {'Messstelle':<22s} {'Fluss':<6s} {'Fluss-km':>9s}  {'Zeitraum':<9s}"
    for column in range(columns):
        block = stations.iloc[column * per_column:(column + 1) * per_column]
        if block.empty:
            continue
        lines = [header, "-" * len(header)] + [
            f"{row.label:>3d} {row.station_name.title()[:22]:<22s} "
            f"{RIVER_DE.get(row.river, row.river)[:6]:<6s} {row.river_km:9.1f}  "
            f"{row.year_min}-{row.year_max}"
            for row in block.itertuples()
        ]
        table_axis.text(column * 0.345, 1.0, "\n".join(lines), transform=table_axis.transAxes,
                        fontsize=7.0, family="monospace", va="top", color="#222222",
                        linespacing=1.32)
    table_axis.text(0, -0.10,
                    "Fluss-km zählen ab der Mündung, nehmen also flussabwärts ab. "
                    "Zeitraum = Spanne der verfügbaren Temperaturmessungen "
                    "(GKD grün: Tagesmittel; Waterbase grau: Stichproben ab 2020).",
                    transform=table_axis.transAxes, fontsize=8.0, color="#666666", va="top")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUT, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    print(f"make_study_map: {OUT} geschrieben ({len(stations)} Messstellen, {len(sites)} Standorte)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
