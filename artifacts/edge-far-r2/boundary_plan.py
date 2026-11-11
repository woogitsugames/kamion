"""Open-GIS footprint evidence for edge-south; diagnostic plan, not a game render."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely import affinity
from shapely.geometry import Polygon, box, shape

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts/edge-far-r2"
old = json.loads((OUT / "baseline/argon-gis-cache.json").read_text())
new = json.loads((OUT / "after/generated/far_field_gis_cache.json").read_text())
region = json.loads((ROOT / "Data/Regions/bialystok-industrial-c/buildings.geojson").read_text())
tile = box(-1024, -1024, 1024, 1024)
window = box(-360, -1160, 100, -900)
fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.5), dpi=100, sharex=True, sharey=True)
for ax, (label, gis) in zip(axes, [("Before: Argon r1", old), ("After: H r2", new)]):
    for feature in region["features"]:
        geom = affinity.translate(shape(feature["geometry"]), -777995, -596223)
        if geom.intersects(window):
            for polygon in getattr(geom, "geoms", [geom]):
                ax.fill(*polygon.exterior.xy, color="#7aaed2", alpha=.8)
    for building in gis["buildings"]:
        polygon = Polygon(building["rect"])
        if polygon.intersects(window):
            color = "#d8473a" if polygon.intersects(tile) else "#676767"
            ax.plot(*polygon.exterior.xy, color=color, linewidth=1.4)
    ax.axhline(-1024, color="black", linestyle="--", linewidth=1)
    ax.arrow(-267.6, -965.9, 27.6, -53.4, width=1.5, color="#7744aa", length_includes_head=True)
    ax.text(-355, -1020, "Region boundary N=-1024", fontsize=8)
    ax.set(xlim=(-360,100), ylim=(-1160,-900), title=label, xlabel="E (m)")
    ax.set_aspect("equal")
axes[0].set_ylabel("N (m)")
fig.suptitle("edge-south | blue: region buildings | red: overlapping far-field rectangles", fontsize=10)
fig.tight_layout()
fig.savefig(OUT / "boundary-plan.png")
