"""ADR 0233: built cross-section of the route carriageway on both sides of a tile seam, read off the generated chunk GLBs.

For each seam (tile A | tile B, the point where the OSM axis of the route crosses the shared tile edge): on each side,
perpendicular cross-sections 2, 4 and 6 m inside the tile (lateral -7..+7 m, 0.02 m): asphalt extent (materials
road_asphalt*), painted-line centres (node `markings`), surface height; the axis height (EVRF2007, the GLB up axis) at
0.1, 1, 2, 5, 10 m inside the tile, extrapolated linearly to the seam (0 m); the lateral offset of the route point.
uv run --project tools/worldgen python tools/worldgen/qa/seam_section.py <out.json> [tag] [a:b ...]   (default: the
dk65-10 | dk65-11 | knyszyn-s seams; test: tests/gis/test_dk65_seam_knyszyn_0233.py)"""
import json, math, struct, sys
from pathlib import Path
import numpy as np, yaml
SEAMS = [("dk65-10", "dk65-11"), ("dk65-11", "knyszyn-s")]
LAT = np.arange(-7.0, 7.0001, 0.02)


def read_glb(path):
    data = path.read_bytes(); jlen, = struct.unpack("<I", data[12:16])
    return json.loads(data[20:20 + jlen]), data, 20 + jlen + 8


def acc(doc, data, off, ai):
    a = doc["accessors"][ai]; bv = doc["bufferViews"][a["bufferView"]]
    o = off + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}[a["type"]]; dt = {5126: "<f4", 5125: "<u4", 5123: "<u2"}[a["componentType"]]
    v = np.frombuffer(data, dt, a["count"] * n, o)
    return v.reshape(a["count"], n) if n > 1 else v


def tris(root, tile, node, centre, rad=30.0):
    """{material: (k,3,3) ENU local} of `node` in the chunks around centre (local E, N)."""
    m = json.loads((root / "Data/Regions" / tile / "generated/world_manifest.json").read_text(encoding="utf-8"))
    out = {}
    for c in m["chunks"]:
        b = c["bounds_local_m"]
        if not (b["e_min"] - rad <= centre[0] <= b["e_max"] + rad and b["n_min"] - rad <= centre[1] <= b["n_max"] + rad):
            continue
        doc, data, off = read_glb(root / c["file"])
        for nd in doc["nodes"]:
            if nd.get("name") != node or "mesh" not in nd:
                continue
            for pr in doc["meshes"][nd["mesh"]]["primitives"]:
                P = acc(doc, data, off, pr["attributes"]["POSITION"]).astype(np.float64)
                V = np.column_stack([-P[:, 0], P[:, 2], P[:, 1]])
                T = V[acc(doc, data, off, pr["indices"]).astype(np.int64).reshape(-1, 3)]
                T = T[(np.abs(T[:, :, 0] - centre[0]).min(1) < rad) & (np.abs(T[:, :, 1] - centre[1]).min(1) < rad)]
                out.setdefault(doc["materials"][pr["material"]]["name"], []).append(T)
    return {k: np.concatenate(v) for k, v in out.items() if sum(len(x) for x in v)}


def locate(T, pts):
    """z of the highest triangle of T (k,3,3) over each (E,N) of pts, nan where none."""
    z = np.full(len(pts), np.nan)
    if not len(T):
        return z
    a, b, c = T[:, 0, :2], T[:, 1, :2], T[:, 2, :2]
    den = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    ok = np.abs(den) > 1e-12
    den = np.where(ok, den, 1.0)
    for i, p in enumerate(pts):
        w0 = ((b[:, 1] - c[:, 1]) * (p[0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (p[1] - c[:, 1])) / den
        w1 = ((c[:, 1] - a[:, 1]) * (p[0] - c[:, 0]) + (a[:, 0] - c[:, 0]) * (p[1] - c[:, 1])) / den
        w2 = 1 - w0 - w1
        hit = ok & (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
        if hit.any():
            z[i] = (w0[hit] * T[hit, 0, 2] + w1[hit] * T[hit, 1, 2] + w2[hit] * T[hit, 2, 2]).max()
    return z


def region(root, t):
    d = root / "Data/Regions" / t
    o = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))["origin"]
    g = {e["id"]: e for e in json.loads((d / "roads.graph.json").read_text(encoding="utf-8"))["edges"]}
    r = json.loads((d / "route_start.json").read_text(encoding="utf-8"))
    return o, g, r


def runs(mask, lat):
    out = []; i = 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j + 1 < len(mask) and mask[j + 1]:
                j += 1
            out.append((float(lat[i]), float(lat[j]))); i = j + 1
        else:
            i += 1
    return out


def seam_axis(root, a, b):
    """Seam point (EPSG:2180) and unit travel directions of the route axis just before / after it."""
    oa, ga, ra = region(root, a); ob, gb, rb = region(root, b)
    ea, eb = ga[ra["edge"][-1]], gb[rb["edge"][0]]
    pa, pb = np.asarray(ea["geometry"], float)[:, :2], np.asarray(eb["geometry"], float)[:, :2]
    sp = min(((np.linalg.norm(x - y), x) for x in (pa[0], pa[-1]) for y in (pb[0], pb[-1])), key=lambda q: q[0])[1]
    if np.linalg.norm(pa[-1] - sp) > 0.01:
        pa = pa[::-1]
    if np.linalg.norm(pb[0] - sp) > 0.01:
        pb = pb[::-1]
    da = (pa[-1] - pa[-2]) / np.linalg.norm(pa[-1] - pa[-2]); db = (pb[1] - pb[0]) / np.linalg.norm(pb[1] - pb[0])
    return sp, da, db, (oa, ra, ea), (ob, rb, eb)


def measure_side(root, t, o, r, first, sp, d, sign):
    loc = sp - np.array([o["x"], o["y"]]); n = np.array([-d[1], d[0]])        # left of travel
    road = tris(root, t, "road", loc); mark = tris(root, t, "markings", loc)
    # a deck at the seam carries its asphalt in the `bridge` node (s8-02 | s8-03, S8 way 98599908: ADR 0288 s24);
    # it fills only the points where the road node has no asphalt (a deck above a road must not win `locate`)
    asp = np.concatenate([v for k, v in road.items() if k.startswith("road_asphalt")] or [np.zeros((0, 3, 3))])
    deck = [v for k, v in tris(root, t, "bridge", loc).items() if k.startswith("road_asphalt")]
    deck = np.concatenate(deck) if deck else None

    def locate_asp(p):
        z = locate(asp, p)
        return z if deck is None else np.where(np.isnan(z), locate(deck, p), z)
    other = {k: v for k, v in road.items() if not k.startswith("road_asphalt")}
    mk = np.concatenate(list(mark.values())) if mark else np.zeros((0, 3, 3))
    side = {"sections": []}
    for dist in (2.0, 4.0, 6.0):
        c = loc + sign * dist * d; pts = c[None, :] + LAT[:, None] * n[None, :]
        za = locate_asp(pts); zm = locate(mk, pts)
        ar = [x for x in runs(~np.isnan(za), LAT) if x[1] - x[0] > 1.0]
        lines = [(round((x0 + x1) / 2, 2), round(x1 - x0 + 0.02, 2)) for x0, x1 in runs(~np.isnan(zm), LAT)]
        el = [ln for ln in lines if abs(ln[0]) > 2.0]
        sh = {k: [(round(x0, 2), round(x1, 2)) for x0, x1 in runs(~np.isnan(locate(v, pts)), LAT) if x1 - x0 > 0.1]
              for k, v in other.items()}
        zi = lambda l: (None if np.isnan(za[int(round((l + 7) / 0.02))]) else round(float(za[int(round((l + 7) / 0.02))]), 3))
        side["sections"].append({
            "inside_m": dist, "asphalt": [(round(x0, 2), round(x1, 2)) for x0, x1 in ar],
            "asphalt_width": round(sum(x1 - x0 + 0.02 for x0, x1 in ar), 2), "lines": lines,
            "edge_lines": [ln[0] for ln in el],
            "edge_line_spacing": round(max(ln[0] for ln in el) - min(ln[0] for ln in el), 2) if len(el) >= 2 else None,
            "other": sh, "z_axis": zi(0.0), "z_at": {str(l): zi(l) for l in (-3.0, -1.5, 1.5, 3.0)}})
    dd = np.array([0.1, 1.0, 2.0, 5.0, 10.0])
    z = locate_asp(loc[None, :] + sign * dd[:, None] * d[None, :])
    side["axis"] = [{"inside_m": float(x), "z": None if np.isnan(v) else round(float(v), 3)} for x, v in zip(dd, z)]
    ok = ~np.isnan(z[:3])
    side["z_seam"] = round(float(np.polyval(np.polyfit(dd[:3][ok], z[:3][ok], 1), 0.0)), 3) if ok.sum() >= 2 else None
    side["grade_pct_travel"] = None if np.isnan(z[[1, 4]]).any() else round(float(sign * (z[4] - z[1]) / (dd[4] - dd[1]) * 100), 2)
    rp = np.asarray(r["points_en"][0 if first else -1][:2], float) - loc
    side["route_lat"] = round(float(rp @ n), 3); side["route_along"] = round(float(rp @ d), 3)
    return side


def measure(root, seams=SEAMS, tag=""):
    res = {"tag": tag, "seams": []}
    for a, b in seams:
        sp, da, db, (oa, ra, ea), (ob, rb, eb) = seam_axis(root, a, b)
        row = {"a": a, "b": b, "seam_epsg2180": [round(float(sp[0]), 2), round(float(sp[1]), 2)],
               "osm_way": [ea["osm_way"], eb["osm_way"]],
               "axis_kink_deg": round(math.degrees(math.acos(float(np.clip(da @ db, -1, 1)))), 3),
               "sides": {a: measure_side(root, a, oa, ra, False, sp, da, -1.0), b: measure_side(root, b, ob, rb, True, sp, db, 1.0)}}
        sa, sb = row["sides"][a], row["sides"][b]; xa, xb = sa["sections"][0], sb["sections"][0]
        dif = lambda p, q: None if p is None or q is None else round(q - p, 3)
        row["delta"] = {"asphalt_width": dif(xa["asphalt_width"], xb["asphalt_width"]),
                        "edge_line_spacing": dif(xa["edge_line_spacing"], xb["edge_line_spacing"]),
                        "z_seam": dif(sa["z_seam"], sb["z_seam"]), "route_lat": dif(sa["route_lat"], sb["route_lat"])}
        res["seams"].append(row)
    return res


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]; out = Path(sys.argv[1])
    pairs = [tuple(p.split(":")) for p in sys.argv[3:]] or SEAMS
    res = measure(root, pairs, tag=sys.argv[2] if len(sys.argv) > 2 else "")
    for row in res["seams"]:
        print(f"{row['a']}|{row['b']} seam {row['seam_epsg2180']} kink {row['axis_kink_deg']} deg")
        for t in (row["a"], row["b"]):
            s = row["sides"][t]; x = s["sections"][0]
            print(f"  {t:10s} asphalt {x['asphalt_width']} {x['asphalt']} edge-lines {x['edge_lines']} spacing {x['edge_line_spacing']} "
                  f"lines {x['lines']} z_seam {s['z_seam']} grade {s['grade_pct_travel']}% route_lat {s['route_lat']} other {x['other']}")
            print("             axis", [(q["inside_m"], q["z"]) for q in s["axis"]])
        print("  delta", row["delta"])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=1), encoding="utf-8")
