import json, pickle, sys
from pathlib import Path
REPO = Path.cwd()
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np, shapely
from roads import pipeline, tunnels as TN
d = pickle.load(open("artifacts/tunnel-0211/dev_dump.pkl", "rb")); w, zc = d["w"], d["zc"].copy()
g = json.loads((pipeline.REGIONS / "bialystok-kleeberga" / "roads.graph.json").read_text(encoding="utf-8"))
bw = TN._build_wall; cap = []
def capw(buf, g_, c, side, sgn, ss, P, N, hw, u_end, lat_w, zfoot, bank, in_F, inner, *a):
    cap.append((g_, c, side, sgn, ss, P, N, hw, u_end, lat_w, in_F, inner)); return bw(buf, g_, c, side, sgn, ss, P, N, hw, u_end, lat_w, zfoot, bank, in_F, inner, *a)
TN._build_wall = capw
TN.build(w, "bialystok-kleeberga", zc, d["mask"], [], g, lambda *a: None)
for g_, c, side, sgn, ss, P, N, hw, u_end, lat_w, in_F, inner in cap:
    F = g_["F"]
    face = P + N * sgn * lat_w[:, None]
    dist = np.array([F.exterior.distance(shapely.Point(q)) * (1 if not F.contains(shapely.Point(q)) else -1) for q in face])
    k = np.where(in_F)[0]
    print(c.id[-20:], side, "inner", inner, "in_F stations", len(k), "lat_w in F", np.round(lat_w[k], 2).tolist())
    print("   raw lat (hw+u+gap)", np.round((hw + u_end + TN.WALL_GAP_M)[k], 2).tolist())
    print("   face outside F by (m, + = outside)", np.round(dist[k], 2).tolist())
