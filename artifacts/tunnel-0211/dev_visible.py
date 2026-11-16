"""ADR 0211 dev QA: run tunnels.build on the dev dump; report terrain / cover geometry that is visible inside the cut
(between the outer wall faces) above the floor: pyramids in front of walls, curtains at portals."""
import json, pickle, sys, time
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np, shapely
from roads import pipeline, tunnels as TN
d = pickle.load(open(REPO / "artifacts/tunnel-0211/dev_dump.pkl", "rb"))
w, zc = d["w"], d["zc"].copy()
g = json.loads((pipeline.REGIONS / "bialystok-kleeberga" / "roads.graph.json").read_text(encoding="utf-8"))
polys = []
orig = TN._poly_mask
def rec(poly, grid, buffer=0.0):
    polys.append(poly); return orig(poly, grid, buffer)
TN._poly_mask = rec
_plan = TN.plan; _cache = {}
def plan_c(w_, g_):
    if "g" not in _cache: _cache["g"] = _plan(w_, g_)
    return _cache["g"]
TN.plan = plan_c
t0 = time.time()
stats, low = TN.build(w, "bialystok-kleeberga", zc, d["mask"], [], g, lambda *a: None)
print("build s", round(time.time() - t0, 1))
CU = max(polys, key=lambda p: p.area)
G = TN.plan(w, g)[0]; F = G["F"]
print("CU area", round(CU.area), "F area", round(F.area))
grid = TN.Grid(w.hf, zc)
floor = TN._floor_field([G], grid, np.ones(zc.shape, bool) & TN._poly_mask(CU.buffer(3), grid)) + TN.FLOOR_DROP_M
def report(name, X, Y, Z, thr=0.6):
    fi, fj = grid.ij(X, Y)
    h = Z - floor[fj, fi]
    bad = h > thr
    print(name, "samples", len(X), "above floor+%.1f:" % thr, int(bad.sum()), "max", round(float(h.max()), 2) if len(h) else None)
    if bad.any():
        P = np.column_stack([X[bad], Y[bad], h[bad]])
        key = np.round(P[:, :2] / 8).astype(int)
        u, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
        for k in np.argsort(-cnt)[:25]:
            q = P[inv.reshape(-1) == k]
            print("   cluster", (u[k] * 8).tolist(), "n", int(cnt[k]), "hmax", round(float(q[:, 2].max()), 2), "inF", bool(F.contains(shapely.Point(q[0, :2]))))
    return int(bad.sum())
Ci = CU.buffer(-0.10)
x0, y0, x1, y1 = Ci.bounds
xs, ys = np.meshgrid(np.arange(x0, x1, 0.25), np.arange(y0, y1, 0.25))
m = shapely.contains_xy(Ci, xs, ys)
X, Y = xs[m], ys[m]
n1 = report("terrain lod0 in cut", X, Y, grid.plane(X, Y, zc))
for step in (2,):
    from terrain_mesh import chunks as CH
    zl = CH.lod_grid(zc, d["mask"], step)
    full = np.repeat(np.repeat(zl, step, 0), step, 1)[: zc.shape[0], : zc.shape[1]]
    # coarse check: node heights of lod1 inside the cut
    jj, ii = np.where(TN._poly_mask(Ci, grid)); k = (jj % step == 0) & (ii % step == 0)
    report("terrain lod1 nodes in cut", grid.x0 + ii[k], grid.y1 - jj[k], zc[jj[k], ii[k]] * 0 + zl[jj[k] // step, ii[k] // step])
# cover mesh: triangles' sample points inside the cut but outside F; inside F below the soffit
n2 = 0
for p in w.buf.parts:
    if p.src != "tunnel:cover:vg": continue
    tri = p.V[p.T]
    S = np.concatenate([tri.mean(1), tri[:, 0] * .8 + tri[:, 1] * .1 + tri[:, 2] * .1, tri[:, 1] * .8 + tri[:, 0] * .1 + tri[:, 2] * .1, tri[:, 2] * .8 + tri[:, 1] * .1 + tri[:, 0] * .1])
    inC = shapely.contains_xy(Ci, S[:, 0], S[:, 1]); inF = shapely.contains_xy(F, S[:, 0], S[:, 1])
    a = inC & ~inF
    n2 += report("cover in cut outside F", S[a, 0], S[a, 1], S[a, 2]) if a.any() else 0
    zs = np.array([G["zroad"](tuple(q)) for q in S[inF, :2]]) + G["clear"]
    low_ = S[inF, 2] < zs + 0.25
    print("cover in F below soffit+0.25:", int(low_.sum()), "of", int(inF.sum()), np.round(S[inF][low_][:6], 2).tolist())
    n2 += int(low_.sum())
print("TOTAL defects", n1 + n2)

# ---- built world (GLB): terrain lod0 / lod1 triangles inside the cut above the floor
import struct
wdir = pipeline.REPO / "Data" / "raw" / "derived" / "bialystok-kleeberga" / "world"
def nodes(path):
    b = path.read_bytes(); n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
    ct = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}; nc = {"SCALAR": 1, "VEC3": 3, "VEC2": 2, "VEC4": 4}
    def acc(i):
        a = j["accessors"][i]; bv = j["bufferViews"][a["bufferView"]]; off = bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        return np.frombuffer(b, np.dtype(ct[a["componentType"]]), a["count"] * nc[a["type"]], off).reshape(a["count"], nc[a["type"]])
    for node in j["nodes"]:
        if "mesh" not in node: continue
        t = np.array(node.get("translation", [0, 0, 0]), float)
        for pr in j["meshes"][node["mesh"]]["primitives"]:
            p = acc(pr["attributes"]["POSITION"]).astype(float) + t; idx = acc(pr["indices"]).reshape(-1, 3)
            mat = j["materials"][pr["material"]]["name"] if "material" in pr else "?"
            yield node.get("name", ""), mat, np.stack([-p[:, 0], p[:, 2], p[:, 1]], 1)[idx]
bx0, by0, bx1, by1 = CU.bounds
acc_ = {}
for f in sorted(wdir.glob("chunk_*.glb")):
    for nm, mat, tr in nodes(f):
        if f.name.endswith(".low.glb"): nm = "LOW:" + nm
        if "collision" in nm or "collision" in mat: continue
        c = tr.mean(1)
        m = (c[:, 0] > bx0 - 8) & (c[:, 0] < bx1) & (c[:, 1] > by0) & (c[:, 1] < by1)
        if not m.any(): continue
        tr = tr[m]
        S = np.concatenate([tr.mean(1), tr[:, 0] * .8 + tr[:, 1] * .1 + tr[:, 2] * .1, tr[:, 1] * .8 + tr[:, 0] * .1 + tr[:, 2] * .1, tr[:, 2] * .8 + tr[:, 1] * .1 + tr[:, 0] * .1])
        inC = shapely.contains_xy(Ci, S[:, 0], S[:, 1]) & ~shapely.contains_xy(F.buffer(0.3), S[:, 0], S[:, 1])
        if not inC.any(): continue
        fi, fj = grid.ij(S[inC, 0], S[inC, 1]); h = S[inC, 2] - floor[fj, fi]
        if "terrain" in nm:
            dzt = tr[:, :, 2].max(1) - tr[:, :, 2].min(1)
            bw = np.array([[a, b, 1 - a - b] for a in np.linspace(0.02, 0.96, 12) for b in np.linspace(0.02, 0.96, 12) if a + b < 0.99])
            for t in tr[dzt > 1.0]:
                Pp = bw @ t
                mm = shapely.contains_xy(Ci, Pp[:, 0], Pp[:, 1]) & ~shapely.contains_xy(F.buffer(0.3), Pp[:, 0], Pp[:, 1])
                if mm.any():
                    fi2, fj2 = grid.ij(Pp[mm, 0], Pp[mm, 1]); h2 = Pp[mm, 2] - floor[fj2, fi2]
                    if h2.max() > 0.6: print("STEEP", f.name, nm, round(float(h2.max()), 2), np.round(t, 2).tolist())
            hh = np.zeros(len(S)); hh[inC] = h; tb = (hh.reshape(4, -1) > 0.6).any(0)
            for t in tr[tb]:
                if abs(t[:, 0].mean() + 176) < 6 and abs(t[:, 1].mean() + 248) < 6: print("TRI", np.round(t, 2).tolist())
        k = (nm, mat)
        a = acc_.setdefault(k, [0, 0, []])
        a[0] += int(inC.sum()); a[1] += int((h > 0.6).sum()); a[2].append(np.column_stack([S[inC][h > 0.6], h[h > 0.6]]))
for k, (n, nb, P) in sorted(acc_.items(), key=lambda x: -x[1][1]):
    if not nb: continue
    P = np.concatenate(P)
    if k[0].startswith("terrain"): report("GLBcl " + k[0], P[:, 0], P[:, 1], P[:, 2])
    print("GLB", k, "samples", n, "above floor+0.6:", nb, "hmax", round(float(P[:, 3].max()), 2), "eg", np.round(P[:: max(1, len(P) // 5)][:5], 1).tolist())

# wall faces near (-176,-248)
for wl in stats["walls"]: print(wl)
print(json.dumps(stats["terrain"]))


