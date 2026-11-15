"""ADR 0211 dev: run roads/tunnels.build on dev_dump.pkl, print stats, plot top view + cross sections."""
import json
import pickle
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from roads import pipeline, tunnels as TN  # noqa: E402

OUT = REPO / "artifacts/tunnel-0211/dev"
OUT.mkdir(parents=True, exist_ok=True)
d = pickle.load(open(REPO / "artifacts/tunnel-0211/dev_dump.pkl", "rb"))
w, zc = d["w"], d["zc"].copy()
zc0 = zc.copy()
g = json.loads((pipeline.REGIONS / "bialystok-kleeberga" / "roads.graph.json").read_text(encoding="utf-8"))
n0 = len(w.buf.parts)
t0 = time.time()
inst = [{"p": "lamp_10m", "e": -128.0, "n": -210.0, "z": 117.5}]
stats, low = TN.build(w, "bialystok-kleeberga", zc, d["mask"], inst, g, print)
print("build", round(time.time() - t0, 1), "s")
st = {k: v for k, v in stats.items() if k != "walls"}
print(json.dumps(st, default=str))
for x in stats["walls"]:
    print(x)
new = [p for p in w.buf.parts[n0:]] + [p for p in w.buf.parts if p.src.startswith("tunnel")]
new = list({id(p): p for p in new}.values())
print("new parts", len(new), "tris", sum(len(p.T) for p in new))
by = {}
for p in new:
    k = (p.layer, p.mat, p.src.split(":")[-1])
    by[k] = by.get(k, 0) + len(p.T)
for k, v in sorted(by.items()):
    print(" ", k, v)
# orientation checks: wall faces must look at the nearest run axis, cover/top faces up, soffit down
G = TN.plan(w, g)[0]
F = G["F"]
cx, cy = F.centroid.x, F.centroid.y
fig, ax = plt.subplots(figsize=(14, 14))
colors = {"ramp_wall_panels": "red", "bridge_concrete": "grey", "bridge_soffit": "black", "verge_grass": "green",
          "barrier_steel": "blue", "collision_fence": "magenta", "collision_grass": "lime"}
for p in new:
    if p.layer == "collision":
        continue
    tri = p.V[p.T]
    for t in tri[:: max(1, len(tri) // 3000)]:
        ax.fill(t[:, 0], t[:, 1], color=colors.get(p.mat, "orange"), alpha=0.35, lw=0)
ax.plot(*F.exterior.xy, "k-")
ax.set_xlim(cx - 160, cx + 160)
ax.set_ylim(cy - 160, cy + 160)
ax.set_aspect("equal")
fig.savefig(OUT / "top.png", dpi=70)
# cross sections across the axis at a few positions
ax_d = G["axis"]
nrm = np.array([-ax_d[1], ax_d[0]])
fig, axs = plt.subplots(5, 1, figsize=(12, 18))
grid = TN.Grid(w.hf, zc)
for a_, off in zip(axs, (-80, -36, 0, 36, 80)):
    c0 = np.array([cx, cy]) + ax_d * off
    lat = np.arange(-30, 30.01, 0.25)
    Q = c0 + np.outer(lat, nrm)
    a_.plot(lat, grid.bilinear(Q[:, 0], Q[:, 1], zc0), "c-", label="zc0")
    a_.plot(lat, grid.bilinear(Q[:, 0], Q[:, 1], zc), "g-", label="zc")
    a_.plot(lat, grid.bilinear(Q[:, 0], Q[:, 1], low[1]), "y:", label="low lod")
    # new geometry crossing this line: plot vertices within 1 m of the section plane
    for p in new:
        if p.layer == "collision":
            continue
        dd = (p.V[:, :2] - c0) @ ax_d
        m = np.abs(dd) < 1.0
        if m.any():
            a_.plot((p.V[m, :2] - c0) @ nrm, p.V[m, 2], ".", ms=2, color=colors.get(p.mat, "orange"))
    a_.set_title(f"section at {off} m along axis")
    a_.set_xlim(-30, 30)
fig.tight_layout()
fig.savefig(OUT / "sections.png", dpi=60)
pickle.dump({"zc": zc, "low": low}, open(OUT / "zc.pkl", "wb"))
