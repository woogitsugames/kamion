"""ADR 0211 dev QA (r4): run tunnels.build on the dev dump and test what the Unity importer will DRAW.

The importer rebuilds the near terrain from the grid nodes (WorldMeshBake.TerrainBandData; High: 1 m, Low: 2 m grid,
diagonal SW-NE, worldgen: NW-SE - both are tested). Checks, per terrain step 1 / 2 / 4:
  A. terrain inside the cut (between the outer wall faces, incl. under the slab) above the floor + 0.6 m
     (pyramids in front of walls, curtains across portals);
  B. holes: terrain lowered > 0.4 m below the original ground within 12 m outside the cut with nothing drawn above
     (cover / road / bridge / paved triangles);
  C. cover triangles inside the cut outside F, and inside F below the soffit.
Exit code 1 when A or C find anything."""
import json, pickle, sys, time
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np, shapely
from PIL import Image, ImageDraw
from roads import pipeline, tunnels as TN
from terrain_mesh import chunks as CH

R = "bialystok-kleeberga"
d = pickle.load(open(REPO / "artifacts/tunnel-0211/dev_dump.pkl", "rb"))
w, zc = d["w"], d["zc"].copy()
zorig = d["zc"]
g = json.loads((pipeline.REGIONS / R / "roads.graph.json").read_text(encoding="utf-8"))
polys = []
_pm = TN._poly_mask
def rec(poly, grid, buffer=0.0):
    polys.append(poly); return _pm(poly, grid, buffer)
TN._poly_mask = rec
_plan = TN.plan; _cache = {}
def plan_c(w_, g_):
    if "g" not in _cache: _cache["g"] = _plan(w_, g_)
    return _cache["g"]
TN.plan = plan_c
t0 = time.time()
stats, low = TN.build(w, R, zc, d["mask"], [], g, lambda *a: None)
print("build s", round(time.time() - t0, 1), json.dumps(stats["terrain"]))
CU = max(polys, key=lambda p: p.area)
G = _cache["g"][0]; F = G["F"]
grid = TN.Grid(w.hf, zc)
near = _pm(CU.buffer(16), grid)
floor = TN._floor_field([G], grid, near) + TN.FLOOR_DROP_M

def tri_z(z, step, x, y, diag):
    """Height on a step-m grid z (rows from north) at local x, y; diag 'nwse' (worldgen) or 'swne' (Unity band)."""
    fi = (np.asarray(x) - grid.x0) / step; fj = (grid.y1 - np.asarray(y)) / step
    i0 = np.clip(np.floor(fi).astype(int), 0, z.shape[1] - 2); j0 = np.clip(np.floor(fj).astype(int), 0, z.shape[0] - 2)
    a, b = fi - i0, fj - j0
    nw, ne, sw, se = z[j0, i0], z[j0, i0 + 1], z[j0 + 1, i0], z[j0 + 1, i0 + 1]
    if diag == "nwse":
        return np.where(b >= a, nw + b * (sw - nw) + a * (se - sw), nw + a * (ne - nw) + b * (se - ne))
    return np.where(a + b <= 1, nw + a * (ne - nw) + b * (sw - nw), se + (1 - a) * (sw - se) + (1 - b) * (ne - se))

def clusters(P, cell=8, n=12):
    key = np.round(P[:, :2] / cell).astype(int)
    u, inv, cnt = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    inv = inv.reshape(-1)
    for k in np.argsort(-cnt)[:n]:
        q = P[inv == k]
        print("     cluster", (u[k] * cell).tolist(), "n", int(cnt[k]), "max", round(float(q[:, 2].max()), 2))

# drawn surfaces above the terrain (0.25 m raster): cover, roads, decks, paved
x0, y0, x1, y1 = CU.buffer(16).bounds
RES = 0.25
Wp, Hp = int((x1 - x0) / RES) + 1, int((y1 - y0) / RES) + 1
img = Image.new("L", (Wp, Hp), 0); dr = ImageDraw.Draw(img)
ncov = 0
for p in w.buf.parts:
    if p.layer not in ("road", "bridge", "paved", "plot_ground") or not len(p.T):
        continue
    tri = p.V[p.T]
    m = (tri[:, :, 0].max(1) > x0) & (tri[:, :, 0].min(1) < x1) & (tri[:, :, 1].max(1) > y0) & (tri[:, :, 1].min(1) < y1)
    for t in tri[m]:
        dr.polygon([((q[0] - x0) / RES, (y1 - q[1]) / RES) for q in t], fill=255)
    ncov += int(m.sum())
drawn = np.asarray(img) > 0
print("drawn-surface raster", drawn.shape, "tris", ncov)

Ci = TN.DEBUG["cut_raw"].buffer(-0.10)
xs, ys = np.meshgrid(np.arange(x0, x1, RES), np.arange(y0, y1, RES))
inC = shapely.contains_xy(Ci, xs, ys)
ring = shapely.contains_xy(CU.buffer(12.0), xs, ys) & ~shapely.contains_xy(CU.buffer(0.3), xs, ys)
fi, fj = grid.ij(xs, ys)
fl = floor[fj, fi]
bad_total = 0
for step in (1, 2, 4):
    zl = CH.lod_grid(zc, d["mask"], step)
    if step >= 4:
        zl = np.where(low[0][::step, ::step], np.minimum(zl, low[1][::step, ::step]), zl)
    for diag in ("nwse", "swne"):
        zt = tri_z(zl, step, xs, ys, diag)
        a = inC & (zt - fl > 0.6)
        print(f"A step {step} {diag}: terrain in the cut above floor+0.6: {int(a.sum())} samples ({a.sum() * RES * RES:.1f} m2)",
              "max", round(float((zt - fl)[inC].max()), 2))
        if a.any():
            clusters(np.column_stack([xs[a], ys[a], (zt - fl)[a]]))
            if step <= 2: bad_total += int(a.sum())
        zo = grid.plane(xs, ys, zorig)
        py = np.clip(((y1 - ys) / RES).astype(int), 0, Hp - 1); px = np.clip(((xs - x0) / RES).astype(int), 0, Wp - 1)
        h = ring & (zo - zt > 0.4) & ~drawn[py, px]
        print(f"B step {step} {diag}: uncovered lowered terrain outside the cut: {int(h.sum())} samples ({h.sum() * RES * RES:.1f} m2)")
        if h.any():
            clusters(np.column_stack([xs[h], ys[h], (zo - zt)[h]]))
            deep = h & (zo - zt > 2.0)
            if deep.any() and step == 2: print("     deep", np.round(np.column_stack([xs[deep], ys[deep], zt[deep], zo[deep]])[:12], 2).tolist())
for p in w.buf.parts:
    if not p.src.startswith("tunnel:cover") or p.layer == "collision":
        continue
    print("cover part", p.layer, p.mat, p.src, "tris", len(p.T))
    tri = p.V[p.T]
    bw = np.array([[a, b, 1 - a - b] for a in np.linspace(0.03, 0.94, 6) for b in np.linspace(0.03, 0.94, 6) if a + b < 0.98])
    S = np.einsum("kb,nbc->nkc", bw, tri).reshape(-1, 3)
    c_in = shapely.contains_xy(Ci, S[:, 0], S[:, 1]); f_in = shapely.contains_xy(F, S[:, 0], S[:, 1])
    a = c_in & ~f_in
    si, sj = grid.ij(S[:, 0], S[:, 1])
    hh = S[:, 2] - floor[sj, si]
    a &= hh > 0.6
    print("C cover in the cut outside F:", int(a.sum()))
    if a.any(): clusters(np.column_stack([S[a, :2], hh[a]]))
    zs = np.array([G["zroad"](tuple(q)) for q in S[f_in, :2]]) + G["clear"]
    lowc = S[f_in, 2] < zs + 0.25
    print("C cover in F below soffit + 0.25:", int(lowc.sum()), "of", int(f_in.sum()))
    if lowc.any(): clusters(np.column_stack([S[f_in][lowc][:, :2], (S[f_in, 2] - zs)[lowc]]))
    bad_total += int(a.sum()) + int(lowc.sum())
rails = [p for p in w.buf.parts if p.src.endswith("slab:rail")]
print("portal railing parts", len(rails), "tris", sum(len(p.T) for p in rails), "portal_m", round(G.get("portal_m", 0), 1))
print("TOTAL A+C defects", bad_total)
sys.exit(1 if bad_total else 0)
