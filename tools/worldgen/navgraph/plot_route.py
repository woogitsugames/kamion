"""Plot a routing-graph dump: region edges (one-way in blue), a route JSON from NavRoutingTests (artifacts/gps-map/*.json).
Usage: uv run --project tools/worldgen python tools/worldgen/navgraph/plot_route.py artifacts/gps-map/route_x.json [out.png]"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
import build_route_graph as brg  # noqa: E402

route = json.load(open(sys.argv[1], encoding="utf-8"))
region = route.get("region", "bialystok-industrial-c")
t = brg.parse(open(os.path.join(brg.OUT_DIR, region + "_route.bytes"), "rb").read())
fig, ax = plt.subplots(figsize=(10, 10), dpi=96)
for e in t["edges"]:
    xs, ys = zip(*e["pts"])
    ow = e["flags"] & brg.F_ONEWAY
    ax.plot(xs, ys, color="#5577aa" if ow else "#bbbbbb", lw=0.6 + 0.5 * e["class"])
    if ow and len(e["pts"]) >= 2:
        (x0, y0), (x1, y1) = e["pts"][len(e["pts"]) // 2 - 1], e["pts"][len(e["pts"]) // 2]
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="->", color="#5577aa", lw=0.6))
xs, ys = zip(*route["points"])
ax.plot(xs, ys, color="#d23", lw=2.2)
ax.plot(xs[0], ys[0], "go", ms=8)
ax.plot(xs[-1], ys[-1], "rs", ms=8)
cum = [0.0]
for (a, b), (c, d) in zip(route["points"], route["points"][1:]):
    cum.append(cum[-1] + ((c - a) ** 2 + (d - b) ** 2) ** 0.5)
for m in route["maneuvers"]:
    i = min(range(len(cum)), key=lambda k: abs(cum[k] - m["s"]))
    ax.annotate(f'{m["type"]} {m["turn"]}° {m["name"][:18]}', route["points"][i], fontsize=7, color="#222")
ax.set_aspect("equal")
ax.set_title(f'{os.path.basename(sys.argv[1])}: {route["length"]:.0f} m, {route["cost_s"]:.0f} s')
out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(sys.argv[1])[0] + ".png"
fig.savefig(out, bbox_inches="tight")
print(out)
