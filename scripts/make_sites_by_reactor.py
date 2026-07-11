"""Small-multiple map: one zoomed panel per reactor, showing exactly the
downstream water-quality monitoring sites the analysis uses for that reactor.

Only the core groups are shown (treatment / partial / control); the staggered
sites (Grafenrheinfeld, Gundremmingen) are left out because they are neither a
clean 2011 treatment nor a full-window control. Each downstream site (<= 50 km)
is attributed to the reactor immediately upstream of it and labelled in that
reactor's panel. The river is named and carries small arrows showing flow
direction.

    python scripts/make_sites_by_reactor.py

Writes figures/study_sites_by_reactor.png. Uses matplotlib; the optional
`adjustText` package de-overlaps the labels if installed.
"""

import math
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import mapdata  # noqa: E402

try:
    from adjustText import adjust_text
    HAVE_ADJUST = True
except Exception:
    HAVE_ADJUST = False

OUT = ROOT / "figures" / "study_sites_by_reactor.png"

GROUP_STYLE = {
    "treatment": ("#e34948", "^", "Treatment"),
    "partial":   ("#eb6834", "s", "Partial"),
    "control":   ("#2a78d6", "o", "Control"),
}
CORE_ORDER = ["treatment", "partial", "control"]
RIVER_DE = {"Rhine": "Rhein", "Danube": "Donau", "Elbe": "Elbe", "Weser": "Weser",
            "Ems": "Ems", "Main": "Main", "Neckar": "Neckar", "Isar": "Isar"}
RIVER_COLOR = "#7bb4d8"
ARROW = "#3f7fa8"
DOWN, INK, SECONDARY = "#1baf7a", "#0b0b0b", "#52514e"

DLON, DLAT = 0.70, 0.58
NEAR_BANDS = {"0-10", "10-25", "25-50"}  # <= 50 km downstream = plausibly exposed


def short_site(reactor_name: str) -> str:
    return re.sub(r"\s+(A|B|C|1|2|I|II)$", "", reactor_name or "")


def clean(name: str) -> str:
    return (name or "").replace("�", "").strip()[:20]


def attribute(water, sites):
    """downstream site (<=50 km) -> the core reactor immediately upstream of it."""
    down = {s["name"]: [] for s in sites}
    for w in water:
        if w["position"] != "downstream" or not w["plant"]:
            continue
        if w.get("band") not in NEAR_BANDS:
            continue
        key = short_site(w["plant"])
        if key in down:  # only core (treatment/partial/control) reactors
            down[key].append(w)
    return down


def flow_arrows(ax, seg, flow):
    """Small arrowheads along a river polyline, pointing downstream."""
    ue, un = flow
    acc, step = 0.0, 0.16
    for i in range(1, len(seg)):
        (x0, y0), (x1, y1) = seg[i - 1], seg[i]
        latm = math.radians((y0 + y1) / 2)
        acc += math.hypot((x1 - x0) * math.cos(latm), y1 - y0)
        if acc < step:
            continue
        acc = 0.0
        dx, dy = x1 - x0, y1 - y0
        if (dx * math.cos(latm)) * ue + dy * un < 0:  # orient downstream
            dx, dy = -dx, -dy
        norm = math.hypot(dx, dy) or 1.0
        ux, uy, mx, my, e = dx / norm, dy / norm, (x0 + x1) / 2, (y0 + y1) / 2, 0.028
        ax.annotate("", xy=(mx + ux * e, my + uy * e), xytext=(mx - ux * e, my - uy * e),
                    arrowprops=dict(arrowstyle="-|>", color=ARROW, lw=1.1, alpha=0.9), zorder=2)


def draw_panel(ax, site, rivers, down):
    box = (site["lon"] - DLON, site["lon"] + DLON, site["lat"] - DLAT, site["lat"] + DLAT)

    for river, lines in rivers.items():
        own = river == site["river"]
        for line in lines:
            seg = [(x, y) for x, y in line if box[0] <= x <= box[1] and box[2] <= y <= box[3]]
            if len(seg) >= 2:
                ax.plot([p[0] for p in seg], [p[1] for p in seg], color=RIVER_COLOR,
                        lw=2.4 if own else 0.9, alpha=0.95 if own else 0.4,
                        solid_capstyle="round", zorder=1)
                if own and site["flow"]:
                    flow_arrows(ax, seg, site["flow"])

    texts = []
    for w in down:
        if not (box[0] <= w["lon"] <= box[1] and box[2] <= w["lat"] <= box[3]):
            continue
        ax.plot(w["lon"], w["lat"], "o", ms=6.5, mfc=DOWN, mec="white", mew=0.6, zorder=3)
        texts.append(ax.text(w["lon"], w["lat"], clean(w["name"]) or w["id"][-6:],
                             fontsize=6.6, color=INK, zorder=5))

    color, marker, glabel = GROUP_STYLE[site["group"]]
    ax.plot(site["lon"], site["lat"], marker=marker, ms=16, mfc=color, mec="#1a1a19", mew=1.3, zorder=6)

    if HAVE_ADJUST and texts:
        adjust_text(texts, ax=ax, expand=(1.1, 1.35),
                    arrowprops=dict(arrowstyle="-", color="#c3c2bb", lw=0.5))

    ax.set_title(f"{site['name']} · {RIVER_DE.get(site['river'], site['river'])}  "
                 f"({glabel}, n={len(down)})", fontsize=10, color=INK, weight="medium")
    ax.set_xlim(box[0], box[1])
    ax.set_ylim(box[2], box[3])
    ax.set_aspect(1.0 / math.cos(math.radians(site["lat"])))
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor("#e1e0d9")


def main() -> None:
    rivers = mapdata.study_rivers()
    sites = [s for s in mapdata.study_sites() if s["group"] in GROUP_STYLE]
    sites.sort(key=lambda s: (CORE_ORDER.index(s["group"]), -s["lat"]))
    water = mapdata.used_water_sites()
    down = attribute(water, sites)

    ncols, nrows = 3, math.ceil(len(sites) / 3)
    fig, axes = plt.subplots(nrows, ncols, figsize=(13.5, 4.6 * nrows), dpi=170)
    fig.patch.set_facecolor("#ffffff")
    axes = axes.flatten()

    for ax, site in zip(axes, sites):
        ax.set_facecolor("#f7f7f4")
        draw_panel(ax, site, rivers, down[site["name"]])
    for ax in axes[len(sites):]:
        ax.axis("off")

    handles = [
        Line2D([0], [0], marker=GROUP_STYLE[g][1], color="none", markerfacecolor=GROUP_STYLE[g][0],
               markeredgecolor="#1a1a19", markersize=11, label=GROUP_STYLE[g][2])
        for g in CORE_ORDER
    ] + [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=DOWN, markeredgecolor="white",
               markersize=9, label="genutzte Downstream-Messstelle (≤ 50 km)"),
        Line2D([0], [0], color=RIVER_COLOR, lw=2.4, label="Studienfluss"),
        Line2D([0], [0], color=ARROW, lw=1.4, marker=">", markersize=6, label="Fließrichtung"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5, fontsize=9.5, frameon=False,
               bbox_to_anchor=(0.5, 0.008))

    fig.suptitle("Genutzte Wasserqualitäts-Messstellen je Kernkraftwerk",
                 fontsize=15.5, weight="bold", color=INK, y=1.0)
    fig.text(0.5, 0.975, "Nur Treatment / Partial / Control · nur Downstream-Messstellen bis 50 km, "
             "dem nächsten Oberlieger-AKW zugeordnet", ha="center", fontsize=9.5, color=SECONDARY)
    fig.tight_layout(rect=(0, 0.04, 1, 0.965))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor="#ffffff")
    total = sum(len(v) for v in down.values())
    print(f"panels: {len(sites)} | downstream used: {total} | adjustText: {HAVE_ADJUST}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
