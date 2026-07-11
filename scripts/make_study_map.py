"""Draw a static map of Germany with the study reactors, the study rivers, the
*used* water-quality monitoring sites and per-site river-flow arrows.

All coordinates come from the project data (via scripts/mapdata.py) so the map
matches the analysis exactly. "Used" sites are those on a study river; off-river
sites within the radius are not shown.

    python scripts/make_study_map.py

Writes figures/study_map.png. Needs matplotlib and internet (for the outline and
river geometry).
"""

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mapdata  # noqa: E402

OUT = ROOT / "figures" / "study_map.png"

GROUP_STYLE = {
    "treatment":           ("#e34948", "^", "Treatment (2011 ganzer Standort aus)"),
    "partial":             ("#eb6834", "s", "Partial (2011 ein Block aus)"),
    "control":             ("#2a78d6", "o", "Control (durchgehend am Netz)"),
    "staggered_treatment": ("#4a3aa7", "D", "Gestaffelt (2015/2017 aus)"),
    "excluded":            ("#898781", "X", "Ausgeschlossen (vor 2011 aus)"),
}
RIVER_COLOR = "#7bb8e0"
WATER_DOWNSTREAM = "#1baf7a"
WATER_UPSTREAM = "#c98500"
INK = "#0b0b0b"
SECONDARY = "#52514e"

LABEL_OFFSETS = {"Brunsbüttel": (-58, 9), "Brokdorf": (10, -12), "Unterweser": (9, 2)}


def main() -> None:
    outline = mapdata.germany_outline()
    rivers = mapdata.study_rivers()
    sites = mapdata.study_sites()
    water = mapdata.used_water_sites()

    fig, ax = plt.subplots(figsize=(8.2, 9.6), dpi=200)
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    for ring in outline:
        ax.fill([p[0] for p in ring], [p[1] for p in ring],
                facecolor="#f4f3ef", edgecolor="#c3c2b7", linewidth=0.8, zorder=0)

    for polylines in rivers.values():
        for line in polylines:
            ax.plot([p[0] for p in line], [p[1] for p in line],
                    color=RIVER_COLOR, linewidth=1.1, alpha=0.9, zorder=1, solid_capstyle="round")

    for site in water:
        if site["position"] == "downstream":
            ax.plot(site["lon"], site["lat"], "o", ms=5, mfc=WATER_DOWNSTREAM,
                    mec="white", mew=0.5, zorder=3)
        else:
            ax.plot(site["lon"], site["lat"], "o", ms=4, mfc=WATER_UPSTREAM,
                    mec="white", mew=0.4, alpha=0.9, zorder=2)

    for site in sites:
        if site["flow"]:
            ue, un = site["flow"]
            start = (site["lon"], site["lat"])
            end = (site["lon"] + ue * 0.42, site["lat"] + un * 0.42)
            ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=11,
                                         lw=1.4, color=SECONDARY, alpha=0.9, zorder=4))

    for site in sites:
        color, marker, _ = GROUP_STYLE[site["group"]]
        ax.plot(site["lon"], site["lat"], marker=marker, ms=12, mfc=color,
                mec="#1a1a19", mew=1.1, zorder=6)
        ax.annotate(site["name"], (site["lon"], site["lat"]),
                    xytext=LABEL_OFFSETS.get(site["name"], (7, 6)),
                    textcoords="offset points", fontsize=8.5, color=INK, weight="medium", zorder=7)

    ax.set_xlim(5.4, 15.5)
    ax.set_ylim(47.1, 55.2)
    ax.set_aspect(1.0 / math.cos(math.radians(51.0)))
    ax.set_xlabel("Länge (°O)", color=SECONDARY, fontsize=9)
    ax.set_ylabel("Breite (°N)", color=SECONDARY, fontsize=9)
    ax.tick_params(colors="#898781", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#e1e0d9")

    ax.set_title("Kernkraftwerke, Studienflüsse und genutzte Wasserqualitäts-Messstellen",
                 fontsize=12.5, color=INK, weight="bold", pad=12)

    handles = [
        Line2D([0], [0], marker=m, color="none", markerfacecolor=c, markeredgecolor="#1a1a19",
               markersize=11, label=label)
        for (c, m, label) in GROUP_STYLE.values()
    ]
    handles += [
        Line2D([0], [0], color=RIVER_COLOR, lw=2, label="Studienfluss"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=WATER_DOWNSTREAM,
               markeredgecolor="white", markersize=8, label="Messstelle: downstream (exponiert)"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=WATER_UPSTREAM,
               markeredgecolor="white", markersize=8, label="Messstelle: upstream (gleicher Fluss)"),
        Line2D([0], [0], color=SECONDARY, lw=1.6, marker=">", markersize=6, label="Fließrichtung"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=8, framealpha=0.95,
              edgecolor="#e1e0d9", facecolor="#ffffff")

    fig.text(0.5, 0.012,
             "Nur Messstellen auf einem Studienfluss (off-river ausgeblendet). "
             "Reaktoren BASE/OPSD, Wasser EEA Waterbase v2020_1, Flüsse Natural Earth. "
             "Partial-Standorte haben zusätzlich einen weiterlaufenden Block.",
             ha="center", fontsize=6.4, color="#898781")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="#ffffff")
    downstream = sum(1 for s in water if s["position"] == "downstream")
    print(f"reactor sites: {len(sites)} | used water sites: {len(water)} (downstream {downstream})")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
