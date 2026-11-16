"""Building triangle budget of a region from the data in git (ADR 0238), without Data/raw.

Runs streetscape.buildings_mesh on Data/Regions/<id>/buildings.geojson + overrides.yaml with
  - a stand-in height field: the LoD1 base level of the nearest building (the real terrain needs the NMT rasters
    of Data/raw),
  - the road footprint approximated by the road graph edges buffered by half their width,
  - the paved yards of generated/streetscape_sources.json (dock detection), no hero assets,
and counts triangles of the layers `buildings` (LOD0) and `buildings_low` (LOD1) per world chunk (triangle
centroid, as the chunker). The numbers are an ESTIMATE of the real build (measured against the committed
world_manifest.json by --check: the harness / manifest ratio per layer), good for a before / after DELTA of a
generator change: the per-camera estimate is the committed mesh_budget.frame_estimate + the delta of the chunks
that camera draws (same wedge rule as roads.build_world.mesh_budget).

    uv run --project tools/worldgen python tools/worldgen/qa/typology_budget.py --region bialystok-industrial-c \
        --out <file.json> [--baseline <file.json>]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import shapely
import yaml
from shapely.geometry import LineString, Polygon

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

LAYERS = ("buildings", "buildings_low")
BLD_HIGH_M = 700.0             # roads.build_world.LOD_POLICY["High"]["bld"]; Low draws LOD1 everywhere


class Buf:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, **kw):
        self.parts.append((layer, mat, np.asarray(V, float), np.asarray(T).reshape(-1, 3), kw.get("src")))


def region_inputs(rid):
    d = REPO / "Data" / "Regions" / rid
    fc = json.loads((d / "buildings.geojson").read_text(encoding="utf-8"))
    ov = (yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides", []) or []
    man = json.loads((d / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
    origin = (man["origin_epsg2180"]["x"], man["origin_epsg2180"]["y"])
    graph = json.loads((d / "roads.graph.json").read_text(encoding="utf-8"))
    o = np.array(origin)
    roads = []
    for e in graph["edges"]:
        w = (e.get("attrs", {}).get("width") or {}).get("v") or 6.0
        roads.append(LineString(np.asarray(e["geometry"], float) - o).buffer(float(w) / 2 + 1.5, cap_style="flat"))
    roads_poly = shapely.union_all(roads)
    yards = [roads_poly]
    sp = d / "generated" / "streetscape_sources.json"
    if sp.exists():
        src = json.loads(sp.read_text(encoding="utf-8"))
        for f in src.get("bdot10k", {}).get("OT_PTPL_A", []):
            if f["props"].get("materialnawierzchni") != "grunt naturalny":
                for ring in ([f["geometry"]["coordinates"]] if f["geometry"]["type"] == "Polygon"
                             else f["geometry"]["coordinates"]):
                    yards.append(shapely.make_valid(Polygon(np.asarray(ring[0], float) - o)))
    return fc, ov, man, origin, roads_poly, shapely.union_all(yards)


def ground(blds):
    """Stand-in height field: the LoD1 base level (`ground_z_evrf2007`) of the nearest building that has one, so a
    region with the `lod1_base_datum` rule (roof = LoD1 base + height) keeps its real building heights."""
    from scipy.spatial import cKDTree
    pts = [(b["poly"].centroid.x, b["poly"].centroid.y, float(b["props"]["ground_z_evrf2007"])) for b in blds
           if b["props"].get("ground_z_evrf2007") is not None]
    if not pts:
        return lambda x, y: np.zeros(np.shape(x))
    P = np.array(pts)
    tree = cKDTree(P[:, :2])

    def sample(x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        _, i = tree.query(np.c_[x.ravel(), y.ravel()])
        return P[i, 2].reshape(x.shape)
    return sample


def build(rid):
    from streetscape import buildings_mesh as BM
    fc, ov, man, origin, roads_poly, yard_union = region_inputs(rid)
    blds = BM.load(fc, origin, ov)
    hf = SimpleNamespace(sample=ground(blds))
    buf, rep = Buf(), {}
    BM.build(buf, blds, hf, hf.sample, yard_union, roads_poly, rep, sign_out=[])
    size = float(man.get("chunk_size_m", 256.0))
    ids = {}
    for ch in man["chunks"]:                      # chunk id <-> grid cell of its south-west corner
        b = ch["bounds_local_m"]
        ids[(round(b["e_min"] / size), round(b["n_min"] / size))] = ch["id"]
    per = {}
    mats = {lay: set() for lay in LAYERS}
    pb = {}
    for layer, mat, V, T, src in buf.parts:
        if layer not in LAYERS or not len(T):
            continue
        mats[layer].add(mat)
        e = pb.setdefault(str(src).split("#")[0], {})
        e[(layer, mat)] = e.get((layer, mat), 0) + len(T)
        c = V[T].mean(1)[:, :2]
        cells = np.floor(c / size).astype(int)
        for cell, n in zip(*np.unique(cells, axis=0, return_counts=True)):
            cid = ids.get((int(cell[0]), int(cell[1])), f"out:{int(cell[0])}:{int(cell[1])}")
            per.setdefault(cid, {lay: 0 for lay in LAYERS})[layer] += int(n)
    tot = {lay: sum(v[lay] for v in per.values()) for lay in LAYERS}
    per_b = {k: [sum(n for (lay, _), n in v.items() if lay == "buildings"),
                 sum(n for (lay, _), n in v.items() if lay == "buildings_low"),
                 hashlib.sha1(repr(sorted(v.items())).encode()).hexdigest()[:10]] for k, v in sorted(pb.items())}
    return {"region": rid, "typologies": rep["typologies"], "subtypes": rep.get("subtypes"),
            "roofs_other": rep.get("roofs_other"), "pavilion_fronts": rep.get("pavilion_fronts"),
            "house_roofs": rep.get("house_roofs"), "total": tot,
            "materials": {lay: len(mats[lay]) for lay in LAYERS}, "per_chunk": dict(sorted(per.items())),
            "per_building": per_b}, man


def cameras(rid, man, per, base=None):
    """Per control camera: building triangles High / Low of the harness, and (with a baseline) the delta."""
    p = REPO / "Data" / "Regions" / rid / "generated" / "control_cameras.json"
    qa = json.loads((REPO / "Data" / "Regions" / rid / "generated" / "streetscape_qa.json").read_text(encoding="utf-8"))
    fe = {f["camera"]: f for f in qa["mesh_budget"]["frame_estimate"]}
    out = []
    for cam in json.loads(p.read_text(encoding="utf-8"))["cameras"]:
        if cam["type"] != "persp":
            continue
        pos = np.array(cam["pos"][:2])
        look = np.array(cam["look_at"][:2]) - pos
        look /= max(np.linalg.norm(look), 1e-9)
        hi = lo = dhi = dlo = 0
        for ch in man["chunks"]:
            b = ch["bounds_local_m"]
            c = np.array([(b["e_min"] + b["e_max"]) / 2, (b["n_min"] + b["n_max"]) / 2])
            d = float(np.linalg.norm(c - pos))
            if d > 1600 or (d > 200 and float(np.dot((c - pos) / d, look)) < 0.5):
                continue
            t = per.get(ch["id"], {lay: 0 for lay in LAYERS})
            tb = (base or {}).get(ch["id"], {lay: 0 for lay in LAYERS})
            k = "buildings" if d < BLD_HIGH_M else "buildings_low"
            hi += t[k]
            lo += t["buildings_low"]
            dhi += t[k] - tb[k]
            dlo += t["buildings_low"] - tb["buildings_low"]
        row = {"camera": cam["id"], "harness_bld_high": hi, "harness_bld_low": lo}
        f = fe.get(cam["id"])
        if f:
            row.update(qa_tris_high=f["tris_high"], qa_tris_low=f["tris_low"],
                       qa_bld_high=f["by_category_high"].get("buildings", 0),
                       qa_bld_low=f["by_category_low"].get("buildings", 0))
        if base is not None:
            row.update(delta_high=dhi, delta_low=dlo)
            if f:
                row.update(est_tris_high=f["tris_high"] + dhi, est_tris_low=f["tris_low"] + dlo)
        out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--out")
    ap.add_argument("--baseline", help="JSON written by an earlier run (the generator before the change)")
    ap.add_argument("--check", action="store_true", help="compare the harness with the committed world manifest")
    a = ap.parse_args()
    res, man = build(a.region)
    base = json.loads(Path(a.baseline).read_text(encoding="utf-8"))["per_chunk"] if a.baseline else None
    res["cameras"] = cameras(a.region, man, res["per_chunk"], base)
    if a.check:
        mt = {"buildings": sum(c["triangles"].get("buildings", 0) for c in man["chunks"]),
              "buildings_low": sum(c["triangles"].get("buildings_lod1", 0) for c in man["chunks"])}
        res["manifest_total"] = mt
        res["harness_over_manifest"] = {lay: round(res["total"][lay] / max(mt[lay], 1), 4) for lay in LAYERS}
    if a.out:
        Path(a.out).write_text(json.dumps(res, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in res.items() if k not in ("per_chunk", "cameras", "per_building")}, sort_keys=True))
    for r in res["cameras"]:
        if base is not None:
            print(f"{r['camera']:32s} dHigh {r['delta_high']:+8d} dLow {r['delta_low']:+7d}"
                  + (f"  est High {r['est_tris_high']:>9d} Low {r['est_tris_low']:>8d}" if "est_tris_high" in r else ""))


if __name__ == "__main__":
    main()
