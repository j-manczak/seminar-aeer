"""Draw a map of Germany with the study reactors, the water-quality monitoring
sites and per-site river-flow arrows.

All coordinates come straight from the project data so the map matches the
analysis exactly: reactor positions and groups from pipeline.reactors, the water
sites from the enriched analysis files, the flow directions from
pipeline.river_position.FLOW.

    python scripts/make_study_map.py

Writes figures/study_map.png. Needs matplotlib and internet (for the Germany
outline; a bundled bounding box is used if the download fails).
"""

import csv
import io
import json
import math
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from pipeline.reactors import REACTORS  # noqa: E402
from pipeline.river_position import FLOW  # noqa: E402

ANALYSIS = ROOT / "data" / "processed" / "analysis"
OUT = ROOT / "figures" / "study_map.png"

# --- categorical palette (from the dataviz reference), by group identity ------
GROUP_STYLE = {
    "treatment":           ("#e34948", "^", "Treatment (2011 ganzer Standort aus)"),
    "partial":             ("#eb6834", "s", "Partial (2011 ein Block aus)"),
    "control":             ("#2a78d6", "o", "Control (durchgehend am Netz)"),
    "staggered_treatment": ("#4a3aa7", "D", "Gestaffelt (2015/2017 aus)"),
    "excluded":            ("#898781", "X", "Ausgeschlossen (vor 2011 aus)"),
}
GROUP_PRIORITY = ["treatment", "partial", "staggered_treatment", "control", "excluded"]

WATER_DOWNSTREAM = "#1baf7a"   # aqua: on a study river, downstream of a reactor
WATER_OTHER = "#b4b3ac"        # muted grey: off-river / upstream
INK = "#0b0b0b"
SECONDARY = "#52514e"

GERMANY_GEOJSON_URLS = [
    "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/1_deutschland/4_niedrig.geo.json",
    "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/master/1_deutschland/4_niedrig.geo.json",
]


def _site_name(reactor_name: str) -> str:
    return re.sub(r"\s+(A|B|C|1|2|I|II)$", "", reactor_name)


def _study_sites():
    """Aggregate the reactors to physical sites, keeping the most-treated group."""
    grouped = defaultdict(list)
    for reactor in REACTORS:
        grouped[_site_name(reactor.reactor)].append(reactor)
    sites = []
    for name, blocks in grouped.items():
        group = min((b.group for b in blocks), key=GROUP_PRIORITY.index)
        sites.append(
            {
                "name": name,
                "lat": sum(b.latitude for b in blocks) / len(blocks),
                "lon": sum(b.longitude for b in blocks) / len(blocks),
                "group": group,
                "river": blocks[0].river,
            }
        )
    return sites


def _water_sites():
    """Unique water-quality monitoring sites from the enriched analysis files."""
    seen = {}
    for filename in ("water_temperature_2006_2018.csv", "dissolved_oxygen_2006_2018.csv"):
        path = ANALYSIS / filename
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as handle:
            rows = csv.DictReader(line for line in handle if not line.startswith("#"))
            for row in rows:
                sid = row.get("site_id")
                if not sid or sid in seen:
                    continue
                try:
                    seen[sid] = (
                        float(row["latitude"]),
                        float(row["longitude"]),
                        row.get("position", ""),
                    )
                except (TypeError, ValueError):
                    continue
    return list(seen.values())


def _germany_polygons():
    for url in GERMANY_GEOJSON_URLS:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "seminar-aeer/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            polygons = []
            for feature in data.get("features", [data]):
                geometry = feature.get("geometry", feature)
                if geometry["type"] == "Polygon":
                    polygons.append(geometry["coordinates"][0])
                elif geometry["type"] == "MultiPolygon":
                    polygons.extend(part[0] for part in geometry["coordinates"])
            if polygons:
                return polygons
        except Exception as error:
            print(f"  outline download failed ({url}): {error}")
    return None


def main() -> None:
    sites = _study_sites()
    water = _water_sites()
    polygons = _germany_polygons()

    fig, ax = plt.subplots(figsize=(8.2, 9.6), dpi=200)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    # Germany outline.
    if polygons:
        for ring in polygons:
            xs = [p[0] for p in ring]
            ys = [p[1] for p in ring]
            ax.fill(xs, ys, facecolor="#f4f3ef", edgecolor="#c3c2b7", linewidth=0.8, zorder=0)

    # Water-quality sites (small dots; downstream ones emphasised).
    for lat, lon, position in water:
        if position == "downstream":
            ax.plot(lon, lat, "o", ms=4.5, mfc=WATER_DOWNSTREAM, mec="white",
                    mew=0.4, zorder=2)
        else:
            ax.plot(lon, lat, "o", ms=2.6, mfc=WATER_OTHER, mec="none", alpha=0.7, zorder=1)

    # Flow-direction arrows at each site.
    for site in sites:
        flow = FLOW.get(site["river"])
        if not flow:
            continue
        ue, un = flow
        length = 0.42  # degrees, purely for visibility
        start = (site["lon"], site["lat"])
        end = (site["lon"] + ue * length, site["lat"] + un * length)
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=11,
                                     lw=1.4, color=SECONDARY, alpha=0.9, zorder=3))

    # Reactor sites, coloured + shaped by group, with labels. A few crowded
    # northern sites get a manual label offset so the names don't collide.
    label_offsets = {
        "Brunsbüttel": (-58, 9),
        "Brokdorf": (10, -12),
        "Unterweser": (9, 2),
    }
    for site in sites:
        color, marker, _ = GROUP_STYLE[site["group"]]
        ax.plot(site["lon"], site["lat"], marker=marker, ms=12, mfc=color,
                mec="#1a1a19", mew=1.1, zorder=5)
        ax.annotate(site["name"], (site["lon"], site["lat"]),
                    xytext=label_offsets.get(site["name"], (7, 6)),
                    textcoords="offset points",
                    fontsize=8.5, color=INK, weight="medium", zorder=6)

    ax.set_xlim(5.4, 15.5)
    ax.set_ylim(47.1, 55.2)
    ax.set_aspect(1.0 / math.cos(math.radians(51.0)))
    ax.set_xlabel("Länge (°O)", color=SECONDARY, fontsize=9)
    ax.set_ylabel("Breite (°N)", color=SECONDARY, fontsize=9)
    ax.tick_params(colors="#898781", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#e1e0d9")

    ax.set_title("Kernkraftwerke und Wasserqualitäts-Messstellen im Studiengebiet",
                 fontsize=13, color=INK, weight="bold", pad=12)

    # Legend: groups + water layers + flow arrow.
    handles = [
        Line2D([0], [0], marker=m, color="none", markerfacecolor=c, markeredgecolor="#1a1a19",
               markersize=11, label=label)
        for (c, m, label) in GROUP_STYLE.values()
    ]
    handles += [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=WATER_DOWNSTREAM,
               markeredgecolor="white", markersize=8, label="Messstelle: downstream eines AKW"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=WATER_OTHER,
               markeredgecolor="none", markersize=6, label="Messstelle: off-river / upstream"),
        Line2D([0], [0], color=SECONDARY, lw=1.6, marker=">", markersize=6,
               label="Fließrichtung"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=8, framealpha=0.95,
              edgecolor="#e1e0d9", facecolor="#ffffff")

    fig.text(0.5, 0.012,
             "Quellen: Reaktoren (BASE/OPSD, eigene Zuordnung), Wasserqualität EEA Waterbase v2020_1. "
             "Pfeile = grobe Fließrichtung. Partial-Standorte haben zusätzlich einen weiterlaufenden Block.",
             ha="center", fontsize=6.6, color="#898781")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="#ffffff")
    print(f"reactor sites: {len(sites)} | water sites: {len(water)} "
          f"(downstream {sum(1 for _,_,p in water if p=='downstream')})")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
