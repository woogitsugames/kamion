"""Fast look at the plot-kit plants / fences without a world build (ADR 0132): a synthetic strip of fence with the
hedge, bushes, fruit trees, a wicket with its letter box - written as an .npz and rendered by Blender
(kit_preview_blender.py; EEVEE, the plot_kit atlas, foliage normals + occlusion from COLOR_0 as in the shader).
    uv run --project tools/worldgen python artifacts/buildings-r9/kit_preview.py <out dir>
    blender -b --factory-startup -P artifacts/buildings-r9/kit_preview_blender.py -- <out dir>
NOT the game renderer: shapes, proportions and silhouettes only."""
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from streetscape import plots as PLT  # noqa: E402

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
kit = PLT.Kit((0.9, 0.9, 0.88))


def zf(q):
    return 0.0


n = np.array([0.0, -1.0])           # street towards -y
A = lambda x, y=0.0: np.array([float(x), float(y)])  # noqa: E731
# 1. brick posts + bars with a hedge behind (the r15_front_brick_bars view)
PLT.fence_run(kit, "brick_bars", A(0), A(11.2), n, 1.6, zf, "k1")
PLT.hedge(kit, A(0.4, 0.6), A(10.8, 0.6), n, zf, 1.9, "h1")
# 2. chain-link with a low hedge, free standing end visible
PLT.fence_run(kit, "chainlink", A(12.5), A(22.7), n, 1.4, zf, "k2")
PLT.hedge(kit, A(13.0, 0.6), A(20.0, 0.6), n, zf, 1.25, "h2")
# 3. pickets with bushes growing through / over
PLT.fence_run(kit, "picket", A(24), A(39.4), n, 1.3, zf, "k3", lean_deg=3.0)
for k, (x, r, h) in enumerate(((26.0, 1.1, 2.2), (29.5, 0.8, 1.5), (33.0, 1.4, 2.8), (37.5, 0.9, 1.9))):
    PLT.bush(kit, A(x, 0.55), 0.0, r, h, ("b", k), red=k == 1)
# 4. wicket with the letter box in a lamella fence + a boards fence
g = {"m": A(41.5), "n": n, "t": A(1, 0), "w": 1.0, "kind": "wicket", "ph": 0.05}
PLT.gate_geo(kit, g, "lamella", 1.7, 0.0, "g1")
PLT.fence_run(kit, "lamella", A(42.1), A(47.2), n, 1.7, zf, "k4")
g = {"m": A(49.0), "n": n, "t": A(1, 0), "w": 1.0, "kind": "wicket", "ph": 0.19}
PLT.gate_geo(kit, g, "brick_picket", 1.6, 0.0, "g2")
# garden: fruit trees, shrubs, thujas, a spruce
for k, (x, y, h, r) in enumerate(((4.0, 6.0, 4.2, 1.9), (10.0, 7.0, 3.4, None), (17.0, 6.5, 5.2, 2.4), (30.0, 6.0, 4.0, 1.6))):
    PLT.fruit_tree(kit, A(x, y), 0.0, h, ("f", k), r)
for k, (x, y, h) in enumerate(((7.0, 3.5, 1.2), (14.0, 4.0, 1.7), (21.0, 3.0, 0.9), (35.0, 4.0, 1.5))):
    PLT.shrub(kit, A(x, y), 0.0, h, ("s", k))
PLT.spruce(kit, A(24.0, 8.0), 0.0, 7.0, "sp1")
for k in range(4):
    PLT.thuja(kit, A(43.0 + k * 0.9, 1.0), 0.0, 2.4, 0.42, ("t", k))
# a 1.75 m person-sized post for scale
kit.box(A(23.3, -1.0), A(1, 0), 0.22, 0.12, 0.0, 1.75, PLT.PK.SWATCH["galv"])
V, UV, T, C = kit.out()
np.savez(out / "kit.npz", V=V, UV=UV, T=T, C=C)
from streetscape import plot_kit as PK  # noqa: E402
PK.atlas().save(out / "plot_kit.png")
print("tris", len(T), "verts", len(V))
