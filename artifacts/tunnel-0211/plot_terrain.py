import sys, pickle, json
sys.path.insert(0, "tools/worldgen"); sys.path.insert(0, "tools/worldgen/qa")
import numpy as np, shapely
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import junction_topview as jt
from roads import pipeline, tunnels as TN
jt.colour = lambda n: (0, 0, 0)
W = jt.load_world("bialystok-kleeberga")
d = pickle.load(open("artifacts/tunnel-0211/dev_dump.pkl", "rb")); w = d["w"]
g = json.loads((pipeline.REGIONS / "bialystok-kleeberga" / "roads.graph.json").read_text(encoding="utf-8"))
G = TN.plan(w, g)[0]; F = G["F"]
fig, axs = plt.subplots(1, 2, figsize=(20, 10))
for ax, (cx, cy) in zip(axs, ((-95, -192), (-160, -228))):
    for nm, tr, lo, hi in W:
        if nm != "terrain_grass": continue
        c = tr.mean(1)
        m = (np.abs(c[:, 0] - cx) < 25) & (np.abs(c[:, 1] - cy) < 25)
        if not m.any(): continue
        pc = PolyCollection(tr[m][:, :, :2], array=c[m, 2], cmap="viridis", clim=(117, 124), edgecolors="none")
        ax.add_collection(pc)
    ax.plot(*F.exterior.xy, "r-")
    ax.set_xlim(cx - 25, cx + 25); ax.set_ylim(cy - 25, cy + 25); ax.set_aspect("equal")
fig.colorbar(pc, ax=axs)
fig.savefig("artifacts/tunnel-0211/vqa-r2/terrain_portals.png", dpi=55)
