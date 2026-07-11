"""Small-multiple map: one zoomed panel per reactor, showing exactly the
downstream water-quality monitoring sites attributed to that reactor.

Each downstream site is assigned to the reactor immediately upstream of it (its
nearest_upstream_plant), so every site appears in exactly one panel and the
"which site belongs to which reactor" question has a clean answer. Upstream
same-river sites are drawn faintly for context. Each panel names its river and
labels every attributed site.

    python scripts/make_sites_by_reactor.py

Writes figures/study_sites_by_reactor.png. Uses matplotlib; if the optional
`adjustText` package is installed the labels are de-overlapped automatically.
"""

import math
import re
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
from pipeline.geo import haversine_km  # noqa: E402

try:
    from adjustText import adjust_text
    HAVE_ADJUST = True
except Exception:
    HAVE_ADJUST = False

OUT = ROOT / "figures" / "study_sites_by_reactor.png"

GROUP_STYLE = {
    "treatment":           ("#e34948", "^", "Treatment"),
    "partial":             ("#eb6834", "s", "Partial"),
    "control":             ("#2a78d6", "o", "Control"),
    "staggered_treatment": ("#4a3aa7", "D", "Gestaffelt"),
}
RIVER_DE = {"Rhine": "Rhein", "Danube": "Donau", "Elbe": "Elbe", "Weser": "Weser",
            "Ems": "Ems", "Main": "Main", "Neckar": "Neckar", "Isar": "Isar"}
RIVER_COLOR = "#5aa0cf"
DOWN, UP, INK, SECONDARY = "#1baf7a", "#c98500", "#0b0b0b", "#52514e"

# Uniform panel half-extent (degrees) and the downstream bands we show/attribute.
DLON, DLAT = 0.70, 0.58
NEAR_BANDS = {"0-10", "10-25", "25-50"}  # <= 50 km downstream = plausibly exposed


def short_site(reactor_name: str) -> str:
    return re.sub(r"\s+(A|B|C|1|2|I|II)$", "", reactor_name or "")


def clean(name: str) -> str:
    return (name or "").replace("�", "").strip()[:20]


def attribute(water, sites):
    """downstream site -> reactor site name (nearest upstream plant);
    upstream site -> nearest same-river reactor. Returns two dicts of lists."""
    by_river = {}
    for s in sites:
        by_river.setdefault(s["river"], []).append(s)
    downstream = {s["name"]: [] for s in sites}
    upstream = {s["name"]: [] for s in sites}
    for w in water:
        if w["position"] == "downstream" and w["plant"]:
            if w.get("band") not in NEAR_BANDS:  # skip sites >50 km downstream
                continue
            key = short_site(w["plant"])
            if key in downstream:
                downstream[key].append(w)
        else:
            candidates = by_river.get(w["river"], [])
            if candidates:
                nearest = min(candidates, key=lambda s: haversine_km(w["lat"], w["lon"], s["lat"], s["lon"]))
                upstream[nearest["name"]].append(w)
    return downstream, upstream


def draw_panel(ax, site, rivers, down, up):
    box = (site["lon"] - DLON, site["lon"] + DLON, site["lat"] - DLAT, site["lat"] + DLAT)

    for river, lines in rivers.items():
        own = river == site["river"]
        for line in lines:
            seg = [(x, y) for x, y in line if box[0] <= x <= box[1] and box[2] <= y <= box[3]]
            if len(seg) >= 2:
                ax.plot([p[0] for p in seg], [p[1] for p in seg], color=RIVER_COLOR,
                        lw=2.4 if own else 0.9, alpha=0.95 if own else 0.4,
                        solid_capstyle="round", zorder=1)

    def inside(w):
        return box[0] <= w["lon"] <= box[1] and box[2] <= w["lat"] <= box[3]

    for w in up:  # context only, no label
        if inside(w):
            ax.plot(w["lon"], w["lat"], "o", ms=5, mfc=UP, mec="white", mew=0.5, alpha=0.85, zorder=2)

    texts = []
    for w in down:
        if not inside(w):
            continue
        ax.plot(w["lon"], w["lat"], "o", ms=6.5, mfc=DOWN, mec="white", mew=0.6, zorder=3)
        label = clean(w["name"]) or w["id"][-6:]
        texts.append(ax.text(w["lon"], w["lat"], label, fontsize=6.6, color=INK, zorder=5))

    if site["flow"]:
        ue, un = site["flow"]
        span = box[1] - box[0]
        ax.add_patch(FancyArrowPatch((site["lon"], site["lat"]),
                                     (site["lon"] + ue * span * 0.22, site["lat"] + un * span * 0.22),
                                     arrowstyle="-|>", mutation_scale=12, lw=1.6, color=SECONDARY, zorder=4))

    color, marker, glabel = GROUP_STYLE[site["group"]]
    ax.plot(site["lon"], site["lat"], marker=marker, ms=16, mfc=color, mec="#1a1a19", mew=1.3, zorder=6)

    if HAVE_ADJUST and texts:
        adjust_text(texts, ax=ax, expand=(1.1, 1.3),
                    arrowprops=dict(arrowstyle="-", color="#b8b7b0", lw=0.5))
    else:
        for t in texts:
            t.set_position((t.get_position()[0] + (box[1] - box[0]) * 0.012,
                            t.get_position()[1] + (box[3] - box[2]) * 0.012))

    ax.set_title(f"{site['name']} · {RIVER_DE.get(site['river'], site['river'])}  "
                 f"({glabel}, n={len(down)})", fontsize=9.5, color=INK, weight="medium")
    ax.set_xlim(box[0], box[1])
    ax.set_ylim(box[2], box[3])
    ax.set_aspect(1.0 / math.cos(math.radians(site["lat"])))
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor("#e1e0d9")


def main() -> None:
    rivers = mapdata.study_rivers()
    sites = [s for s in mapdata.study_sites() if s["group"] != "excluded"]
    water = mapdata.used_water_sites()
    down, up = attribute(water, sites)
    sites.sort(key=lambda s: -s["lat"])  # north to south

    ncols, nrows = 3, math.ceil(len(sites) / 3)
    fig, axes = plt.subplots(nrows, ncols, figsize=(13.5, 4.4 * nrows), dpi=170)
    fig.patch.set_facecolor("#ffffff")
    axes = axes.flatten()

    for ax, site in zip(axes, sites):
        ax.set_facecolor("#f7f7f4")
        draw_panel(ax, site, rivers, down[site["name"]], up[site["name"]])
    for ax in axes[len(sites):]:
        ax.axis("off")

    handles = [
        Line2D([0], [0], marker=GROUP_STYLE[g][1], color="none", markerfacecolor=GROUP_STYLE[g][0],
               markeredgecolor="#1a1a19", markersize=11, label=GROUP_STYLE[g][2])
        for g in ("treatment", "partial", "control", "staggered_treatment")
    ] + [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=DOWN, markeredgecolor="white",
               markersize=9, label="Messstelle downstream (diesem AKW zugeordnet)"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=UP, markeredgecolor="white",
               markersize=9, label="Messstelle upstream (gleicher Fluss, Kontext)"),
        Line2D([0], [0], color=RIVER_COLOR, lw=2.4, label="Studienfluss"),
        Line2D([0], [0], color=SECONDARY, lw=1.6, marker=">", markersize=6, label="Fließrichtung"),
    ]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=9, frameon=False,
               bbox_to_anchor=(0.5, 0.004))

    note = "" if HAVE_ADJUST else "  (Tipp: 'pip install adjustText' entzerrt die Beschriftungen automatisch)"
    fig.suptitle("Genutzte Wasserqualitäts-Messstellen je Kernkraftwerk",
                 fontsize=15, weight="bold", color=INK, y=1.0)
    fig.text(0.5, 0.978, "Downstream-Messstellen bis 50 km flussabwärts, dem jeweils nächsten "
             "Oberlieger-AKW zugeordnet · einheitlicher Ausschnitt ±0,7°/±0,58°",
             ha="center", fontsize=9, color=SECONDARY)
    fig.tight_layout(rect=(0, 0.05, 1, 0.985))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor="#ffffff")
    total_down = sum(len(v) for v in down.values())
    print(f"panels: {len(sites)} | downstream attributed: {total_down} | adjustText: {HAVE_ADJUST}{note}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
