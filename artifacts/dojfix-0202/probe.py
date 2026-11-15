"""ADR 0202: what surface lies under every chain post, and across the row (carriageway -> behind the row).

For each post: every non-collision triangle of the chunk whose plan projection contains the post (material, node, z).
Cross-section at post 4: the same every 0.5 m from 8 m toward the carriageway to 6 m behind.
"""
import glob
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "tests/gis")
import route_corridor as RC  # noqa: E402

it = []
for f in glob.glob("Data/raw/derived/bialystok-dojlidy/world/instances_*.json"):
    for i in json.load(open(f, encoding="utf-8"))["instances"]:
        if str(i.get("p", "")).startswith("bollard_rw"):
            it.append((int(i["src"].rsplit(":", 1)[1]), i, Path(f).name))
it.sort(key=lambda x: x[0])
P = np.array([[i["e"], i["n"], i["z"]] for _, i, _ in it])
print("posts", len(P), {f for _, _, f in it}, [i["p"] for _, i, _ in it])
chunk = it[0][2].replace("instances_", "chunk_").replace(".json", ".glb")
doc, data, binoff = RC.read_glb(Path("Data/raw/derived/bialystok-dojlidy/world") / chunk)
tris = {}
for node in doc["nodes"]:
    if "mesh" not in node:
        continue
    for mat, T in RC.node_triangles(doc, data, binoff, node["name"]).items():
        if mat.startswith("collision"):
            continue
        tris.setdefault((node["name"], mat), []).append(T)
tris = {k: np.concatenate(v) for k, v in tris.items()}


def under(e, n):
    out = []
    for (node, mat), T in tris.items():
        a, b, c = T[:, 0, :2], T[:, 1, :2], T[:, 2, :2]
        q = np.array([e, n])
        d1 = (b[:, 0] - a[:, 0]) * (q[1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (q[0] - a[:, 0])
        d2 = (c[:, 0] - b[:, 0]) * (q[1] - b[:, 1]) - (c[:, 1] - b[:, 1]) * (q[0] - b[:, 0])
        d3 = (a[:, 0] - c[:, 0]) * (q[1] - c[:, 1]) - (a[:, 1] - c[:, 1]) * (q[0] - c[:, 0])
        hit = ((d1 >= 0) & (d2 >= 0) & (d3 >= 0)) | ((d1 <= 0) & (d2 <= 0) & (d3 <= 0))
        # only near-horizontal faces (ground), not walls
        nz = np.abs(np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]))
        hit &= nz[:, 2] > 0.5 * np.linalg.norm(nz, axis=1) + 1e-12
        for t in T[hit]:
            out.append((round(float(t[:, 2].mean()), 2), node, mat))
    return sorted(set(out), reverse=True)


res = {"posts": [], "section": []}
for k, p in enumerate(P):
    u = [x for x in under(p[0], p[1]) if "lod" not in x[1].lower() or "lod0" in x[1].lower()]
    top = u[0] if u else None
    res["posts"].append({"post": k + 1, "e": round(p[0], 2), "n": round(p[1], 2), "z_seat": round(p[2], 2), "top": top, "all": u[:5]})
    print(k + 1, np.round(p, 2), "TOP:", top, "| below:", [x[2] for x in u[1:4]])
t = (P[-1, :2] - P[0, :2]) / np.hypot(*(P[-1, :2] - P[0, :2]))
west = np.array([t[1], -t[0]])
if west[0] > 0:
    west = -west
print("section at post 4 (d > 0 = toward the carriageway):")
for d in np.arange(8.0, -6.01, -0.5):
    q = P[3, :2] + west * d
    u = [x for x in under(q[0], q[1]) if "lod" not in x[1].lower() or "lod0" in x[1].lower()]
    res["section"].append({"d_m": float(d), "top": u[0] if u else None})
    print(f"{d:5.1f}", u[0] if u else None)
json.dump(res, open("artifacts/dojfix-0202/probe.json", "w"), indent=1)
