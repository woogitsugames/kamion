"""fix-pr80-s21: measure the built seam between two tiles on the generator output (chunk GLBs), not on a render.
Along the shared edge (default: dk65-05 north = dk65-06 south, y = 603391) and for E in [x0, x1]:
  - road materials cut by the seam plane -> intervals in E + surface height, per material and tile
  - terrain_lod0 vertices on the seam row -> height and vertex colour (channel A = sand of construction_site)
Prints a comparison and writes JSON.  uv run --project tools/worldgen python artifacts/verify-cloud-c/tools/seam_mesh.py [out.json]"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).parent))
import glb
ROOT = Path(__file__).resolve().parents[3]
A, B, Y, X0, X1 = "dk65-05", "dk65-06", 603391.0, 767540.0, 767860.0


def cut(P, idx, n0):
    """Segments of the triangle mesh on the plane N = n0 -> array (k, 2, 2) of (E, z) pairs."""
    T = P[idx.reshape(-1, 3)]
    d = T[:, :, 1] - n0
    hit = (d.min(1) <= 0) & (d.max(1) >= 0) & (d.max(1) - d.min(1) > 1e-9)
    out = []
    for t, dd in zip(T[hit], d[hit]):
        pts = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            if (dd[a] <= 0) != (dd[b] <= 0):
                k = dd[a] / (dd[a] - dd[b]); q = t[a] + k * (t[b] - t[a]); pts.append((q[0], q[2]))
        if len(pts) == 2:
            out.append(pts)
    return np.array(out).reshape(-1, 2, 2)


def intervals(segs, gap=0.05):
    if not len(segs):
        return []
    iv = sorted((min(s[0][0], s[1][0]), max(s[0][0], s[1][0])) for s in segs)
    out = [list(iv[0])]
    for a, b in iv[1:]:
        if a <= out[-1][1] + gap: out[-1][1] = max(out[-1][1], b)
        else: out.append([a, b])
    return [[round(a, 2), round(b, 2)] for a, b in out if b - a > 0.05]


def zat(segs, e):
    for (e0, z0), (e1, z1) in segs:
        if min(e0, e1) - 1e-6 <= e <= max(e0, e1) + 1e-6 and abs(e1 - e0) > 1e-9:
            return z0 + (z1 - z0) * (e - e0) / (e1 - e0)
    return None


def tile(t):
    m = json.loads((ROOT / "Data/Regions" / t / "generated/world_manifest.json").read_text(encoding="utf-8"))
    ox, oy = m["origin_epsg2180"]["x"], m["origin_epsg2180"]["y"]; n0 = Y - oy
    res = {"road": {}, "terrain": [], "raw": []}
    segs = {}
    for c in m["chunks"]:
        b = c["bounds_local_m"]
        if not (b["n_min"] - 0.5 <= n0 <= b["n_max"] + 0.5 and b["e_max"] + ox >= X0 and b["e_min"] + ox <= X1):
            continue
        for name, mat, at, idx in glb.load(ROOT / c["file"]):
            P = at["POSITION"]; W = np.column_stack([ox - P[:, 0], P[:, 2], P[:, 1]])      # E (EPSG:2180), N local, z
            if name == "road" and idx is not None:
                res["raw"].append((mat, np.column_stack([W[:, 0], W[:, 1] + oy, W[:, 2]]), idx))
                s = cut(W, idx, n0)
                if len(s): segs.setdefault(mat, []).extend(s.tolist())
            elif name == "terrain_lod0":
                on = np.abs(W[:, 1] - n0) < 0.02
                col = at.get("COLOR_0")
                for i in np.nonzero(on)[0]:
                    res["terrain"].append((round(float(W[i, 0]), 3), float(W[i, 2]), *(float(v) for v in (col[i] if col is not None else (0, 0, 0, 0)))))
    for mat, s in segs.items():
        s = [x for x in s if X0 <= x[0][0] <= X1]
        res["road"][mat] = {"intervals_E": intervals(s), "segs": s}
    res["terrain"] = sorted({r[0]: r for r in res["terrain"] if X0 <= r[0] <= X1}.values())
    return res


ra, rb = tile(A), tile(B)
rep = {"seam_y": Y, "tiles": [A, B], "road": {}, "terrain": {}, "sand": {}}
print(f"seam y = {Y}: {A} (north edge) | {B} (south edge), E {X0}..{X1}")
for mat in sorted(set(ra["road"]) | set(rb["road"])):
    ia = ra["road"].get(mat, {}).get("intervals_E", []); ib = rb["road"].get(mat, {}).get("intervals_E", [])
    rep["road"][mat] = {A: ia, B: ib}
    print(f"  {mat:16s} {A}: {ia}\n  {'':16s} {B}: {ib}")
    if len(ia) == len(ib):
        d = [round(max(abs(a[0] - b[0]), abs(a[1] - b[1])), 3) for a, b in zip(ia, ib)]
        rep["road"][mat]["edge_diff_m"] = d; print(f"  {'':16s} edge diff {d} m, widths {[round(a[1]-a[0],2) for a in ia]} | {[round(b[1]-b[0],2) for b in ib]}")
sa, sb = ra["road"].get("road_asphalt", {}).get("segs", []), rb["road"].get("road_asphalt", {}).get("segs", [])
dz = []
for iv in rep["road"].get("road_asphalt", {}).get(A, []):
    for e in np.linspace(iv[0] + 0.05, iv[1] - 0.05, 15):
        za, zb = zat(sa, e), zat(sb, e)
        if za is not None and zb is not None: dz.append(abs(za - zb))
if dz:
    rep["road"]["asphalt_dz_max_m"] = round(max(dz), 3); print(f"  asphalt surface dz across the seam: max {max(dz):.3f} m (n = {len(dz)})")
ta = {r[0]: r for r in ra["terrain"]}; tb = {r[0]: r for r in rb["terrain"]}
common = sorted(set(ta) & set(tb))
if common:
    d = np.array([abs(ta[e][1] - tb[e][1]) for e in common]); da = np.array([abs(ta[e][5] - tb[e][5]) for e in common])
    rep["terrain"] = {"common_vertices": len(common), "only_a": len(ta) - len(common), "only_b": len(tb) - len(common), "dz_median_m": round(float(np.median(d)), 3), "dz_p95_m": round(float(np.percentile(d, 95)), 3),
                      "dz_max_m": round(float(d.max()), 3), "dz_max_at_E": common[int(d.argmax())], "sand_alpha_diff_max": round(float(da.max()), 3)}
    print("  terrain seam row:", rep["terrain"])
for t, tt in ((A, ta), (B, tb)):
    es = sorted(tt); run = []; cur = None
    for e in es:
        if tt[e][5] > 0.5:
            cur = [e, e] if cur is None or e - cur[1] > 1.5 else [cur[0], e]
            if run and run[-1][0] == cur[0]: run[-1] = cur
            else: run.append(cur)
        else: cur = None
    rep["sand"][t] = run; print(f"  sand (terrain colour A > 0.5) {t}: {run}")
if len(rep["sand"][A]) == len(rep["sand"][B]) and rep["sand"][A]:
    rep["sand"]["edge_diff_m"] = [round(max(abs(a[0] - b[0]), abs(a[1] - b[1])), 3) for a, b in zip(rep["sand"][A], rep["sand"][B])]
    print("  sand edge diff", rep["sand"]["edge_diff_m"], "m")
# ---- perpendicular cross-sections of Ełcka (way 1560819273) on both sides of the seam
g = json.loads((ROOT / "Data/Regions" / A / "roads.graph.json").read_text(encoding="utf-8"))
ax = np.array([p[:2] for e in g["edges"] if e["osm_way"] == 1560819273 for p in e["geometry"]])
P0, u = ax[-1], (ax[-1] - ax[-2]) / np.linalg.norm(ax[-1] - ax[-2]); nrm = np.array([u[1], -u[0]])      # nrm: to the right of travel
rep["elcka"] = {"axis_at_seam": [round(float(v), 2) for v in P0], "heading_deg": round(float(np.degrees(np.arctan2(u[0], u[1])) % 360), 1), "sections": {}}
print(f"Ełcka axis at the seam {rep['elcka']['axis_at_seam']}, heading {rep['elcka']['heading_deg']} deg; perpendicular sections (t = metres right of the OSM axis):")
for t, r, stations in ((A, ra, (-30.0, -10.0, -2.0, -0.2)), (B, rb, (0.2, 2.0, 10.0, 20.0))):
    for s0 in stations:
        row = {}
        for mat, W, idx in r["raw"]:
            if mat not in ("road_asphalt", "shoulder_gravel", "road_gravel"):
                continue
            d = W[:, :2] - P0
            Q = np.column_stack([d @ nrm, d @ u, W[:, 2]])          # (t, s, z)
            sg = cut(Q, idx, s0)
            sg = [x for x in sg.tolist() if abs(x[0][0]) < 12 and abs(x[1][0]) < 12]
            if sg:
                row[mat] = intervals(sg)
            if sg and mat == "road_asphalt":
                row["z_at_t"] = {str(tt): (None if zat(sg, tt) is None else round(zat(sg, tt), 3)) for tt in (-3.0, 0.0, 3.0)}
        a = row.get("road_asphalt", [])
        rep["elcka"]["sections"][f"{t} s={s0:+.1f}"] = row
        print(f"  {t} s = {s0:+5.1f} m: asphalt {a} width {[round(x[1]-x[0],2) for x in a]}  gravel shoulder {row.get('shoulder_gravel')}  z(t=-3,0,+3) {list((row.get('z_at_t') or {}).values())}")
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text(json.dumps(rep, indent=1), encoding="utf-8")
