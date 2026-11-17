"""ADR 0237 D38 QA: Knyszyn Poludniowa x Szkolna crossroads and the implied-sidewalk rule, from git data only.

    uv run --project tools/worldgen python tools/worldgen/qa/knyszyn_szkolna_d38.py junction <out.json>
    uv run --project tools/worldgen python tools/worldgen/qa/knyszyn_szkolna_d38.py budget <region> <out.json>
    uv run --project tools/worldgen python tools/worldgen/qa/knyszyn_szkolna_d38.py plan <region> <e_2180> <n_2180> <half_m> <out.png> [px]

junction: arms / trims / corners of the junctions at OSM nodes 1134846746 + 7015352011 and the P-10 placed at the OSM
          crossing nodes 11514832006-009, with and without the `cluster: separate` override (roads.junctions).
budget:   triangles of the road build with and without implied sidewalks, per control camera with the
          mesh_budget.frame_estimate visibility rule (everything <= 200 m, <= 1.6 km within +-60 deg of the view
          direction), added to the committed tris_high / tris_low of streetscape_qa.json. ESTIMATED: triangle centroids
          instead of chunks, road layer only (markings / furniture of the new sidewalks not counted).
plan:     top view PNG of the generated road meshes (scratch, keep outside git).
All builds use a FLAT heightfield (Data/raw is not needed): plan geometry only, heights are not checked here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from roads import junctions as J  # noqa: E402
from roads import pipeline  # noqa: E402
from roads import profile as P  # noqa: E402

NODES = ("n1134846746", "n7015352011")
ZEBRAS = (11514832006, 11514832007, 11514832008, 11514832009)


def _flat(region):
    reg = pipeline.load_region(region)
    o = (reg["origin"]["x"], reg["origin"]["y"])
    bb = json.loads((pipeline.REGIONS / region / "terrain.json").read_text(encoding="utf-8"))["bbox"]
    return P.Heightfield(np.full((int(bb[3] - bb[1]) + 2, int(bb[2] - bb[0]) + 2), 120.0), bb, o), o


def _build(region, implied=True, separate=True):
    from streetscape import pavements as PV
    keep_p, keep_k = PV.implied_plan, J._keep_apart
    if not implied:
        PV.implied_plan = lambda net: None
    if not separate:
        J._keep_apart = lambda *a, **k: set()
    try:
        hf, o = _flat(region)
        return pipeline.build(region, hf=hf, collision=False), o
    finally:
        PV.implied_plan, J._keep_apart = keep_p, keep_k


def junction(out):
    from roads import markings as MK
    res = {}
    for name, sep in (("before_d38", False), ("after_d38", True)):
        w, o = _build("knyszyn", implied=sep, separate=sep)
        rep = {}
        MK.build_markings(w.buf, w.net, w.junctions, w.ctx["points"], rep)
        js = []
        for j in w.junctions:
            if not set(j.nodes) & set(NODES):
                continue
            js.append({"id": j.id, "nodes": j.nodes,
                       "arms": [{"chain": a.chain.id, "end": a.end, "highway": w.net.sec_list[int(a.chain.sec_idx[0])].highway,
                                 "trim_m": round(float(j.trims[i]), 2)} for i, a in enumerate(j.arms)],
                       "corners": [{"k": c.k, "k1": c.k1, "kind": c.kind, "R_m": round(float(c.R), 2)} for c in j.corners],
                       "notes": j.notes})
        xy = {p["osm_node"]: np.array([p["e"], p["n"]]) for p in w.ctx["points"] if p.get("osm_node") in ZEBRAS}
        placed = [c.line.p[c.idx(s)] for c in w.net.chains for s in c.meta.get("crossings", [])]
        zeb = {str(k): (round(min(float(np.hypot(*(p - q))) for p in placed), 2) if placed else None) for k, q in xy.items()}
        res[name] = {"junctions": js, "p10_nearest_to_osm_crossing_m": zeb,
                     "crossings_skipped": sorted(set(rep.get("crossings_skipped", [])) & set(ZEBRAS))}
    Path(out).write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def budget(region, out):
    def cents(implied):
        w, _ = _build(region, implied=implied)
        return np.concatenate([p.V[p.T].mean(axis=1)[:, :2] for p in w.buf.parts if p.layer != "collision"])
    A, B = cents(False), cents(True)
    rdir = pipeline.REGIONS / region / "generated"
    cams = json.loads((rdir / "control_cameras.json").read_text(encoding="utf-8"))["cameras"]
    fe = {f["camera"]: f for f in json.loads((rdir / "streetscape_qa.json").read_text(encoding="utf-8"))["mesh_budget"]["frame_estimate"]}

    def vis(C, cam):
        p = np.array(cam["pos"][:2])
        d = np.array(cam["look_at"][:2]) - p
        v = C - p
        r = np.hypot(*v.T)
        ang = np.degrees(np.abs(np.arctan2(d[0] * v[:, 1] - d[1] * v[:, 0], v @ d)))
        return int(((r <= 200) | ((r <= 1600) & (ang <= 60))).sum())
    rows = []
    for cam in cams:
        if "pos" not in cam or "look_at" not in cam:
            continue
        da = vis(B, cam) - vis(A, cam)
        f = fe.get(cam["id"], {})
        rows.append({"camera": cam["id"], "delta_tris": da, "tris_high_committed": f.get("tris_high"),
                     "tris_high_estimated": None if f.get("tris_high") is None else f["tris_high"] + da,
                     "tris_low_committed": f.get("tris_low"),
                     "tris_low_estimated": None if f.get("tris_low") is None else f["tris_low"] + da})
    res = {"region": region, "method": "ESTIMATED, see module docstring", "road_tris_before": len(A),
           "road_tris_after": len(B), "cameras": sorted(rows, key=lambda r: -(r["tris_high_estimated"] or 0))}
    Path(out).write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")


def plan(region, e, n, half, out, px=960):
    from PIL import Image, ImageDraw
    w, o = _build(region)
    pal = {"road": (62, 62, 66), "curb": (220, 220, 210), "sidewalk": (176, 172, 164), "verge": (110, 138, 86),
           "apron": (150, 134, 120), "shoulder": (150, 140, 120), "marking": (250, 250, 250)}
    s = px / (2 * half)
    img = Image.new("RGB", (px, px), (40, 70, 40))
    d = ImageDraw.Draw(img)
    lx, ly = e - o[0], n - o[1]
    for p in sorted((p for p in w.buf.parts if p.layer != "collision"), key=lambda p: p.mat.startswith("curb")):
        c = next((v for k, v in pal.items() if p.mat.startswith(k)), (255, 0, 255))
        tri = p.V[p.T][:, :, :2]
        m = (np.abs(tri[:, :, 0] - lx).min(1) < half) & (np.abs(tri[:, :, 1] - ly).min(1) < half)
        for t3 in tri[m]:
            d.polygon([((x - lx + half) * s, (half - (y - ly)) * s) for x, y in t3], fill=c)
    img.save(out)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "junction":
        junction(a[1])
    elif a[0] == "budget":
        budget(a[1], a[2])
    elif a[0] == "plan":
        plan(a[1], float(a[2]), float(a[3]), float(a[4]), a[5], int(a[6]) if len(a) > 6 else 960)
    else:
        raise SystemExit(__doc__)
