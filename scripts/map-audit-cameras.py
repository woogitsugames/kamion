"""Map audit r9: driver-eye cameras every N m along the start route in BOTH directions + top-down cameras over junctions.

    uv run --project tools/worldgen python scripts/map-audit-cameras.py --region bialystok-industrial-c \
        --out artifacts/map-audit-r9/cameras/audit_cameras.json [--step 20] [--left-step 40]

Read-only inputs: Data/Regions/<id>/region.yaml, roads.graph.json, route_start.json (graph_nodes), heightmap_2049.r16.
Forward = route_start graph path (Kwadrat Park -> DK8/DK19); reverse = shortest drivable path end -> start on the same
graph (roadgraph.to_digraph, same as export-route.py). Lane: right-most lane centre of the travel direction
(two-way: lane_w * (lanes/2 - 0.5) right of the centreline; one-way: (lanes-1)/2 * lane_w right), lane_w = width/lanes
clamped 2.75..3.5 m (export-route.py rule, WORKING_VALUE). Extra "left lane" cameras on multi-lane one-way edges.
Format = gate3_cameras.json (Gate3Cameras.cs): driver_eye re-seated 2.5 m above the road collision (task asks ~2.4 m;
Gate3Cameras.HeightAboveRoad is 2.5, kept), rondo_above re-seated 45 m (task ~40 m). FOV 55 = CameraRig.cabFov.
Points on or under OSM bridge/layer edges: on a bridge the file U is lifted so the downward raycast starts above the deck;
under a bridge seat="file" (NMT + 2.5 m) so the camera is not put on the deck.
Also writes <out>.index.csv: id, dir, s, E, N, lat, lon, heading, edge, road name, lanes, width.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
sys.path.insert(0, str(REPO / "scripts"))
MAIN = Path(r"C:\Users\matma\Documents\Claude\kamion")

EYE = 2.5
LOOK_AHEAD = 30.0
FOV_CAB = 55.0


def load_height(region):
    import importlib.util
    spec = importlib.util.spec_from_file_location("g3s", REPO / "scripts" / "gate3-segment.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    bbox = [region["bbox"][k] for k in ("xmin", "ymin", "xmax", "ymax")]
    for base in (REPO, MAIN):
        p = base / "Data/raw/derived" / region["id"] / "heightmap_2049.r16"
        if p.exists():
            return m.Height(str(p), bbox)
    raise SystemExit("heightmap_2049.r16 not found")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="bialystok-industrial-c")
    ap.add_argument("--out", default="artifacts/map-audit-r9/cameras/audit_cameras.json")
    ap.add_argument("--step", type=float, default=20.0)
    ap.add_argument("--left-step", type=float, default=40.0)
    a = ap.parse_args()

    import networkx as nx
    import roadgraph
    from pyproj import Transformer

    rdir = REPO / "Data" / "Regions" / a.region
    region = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
    graph = json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8"))
    route = json.loads((rdir / "route_start.json").read_text(encoding="utf-8"))
    ox, oy = region["origin"]["x"], region["origin"]["y"]
    H = load_height(region)
    tr = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    edges = {e["id"]: e for e in graph["edges"]}
    nodes = {n["id"]: n for n in graph["nodes"]}
    g = roadgraph.to_digraph(graph)
    fwd_path = route["graph_nodes"]
    rev_path = nx.shortest_path(g, fwd_path[-1], fwd_path[0], weight="length")

    bridges = []
    for e in graph["edges"]:
        at = e["attrs"]
        if at.get("bridge", {}).get("v") not in (None, "no") or str(at.get("layer", {}).get("v", "0")) not in ("0", "None"):
            bridges.append((e["id"], np.array([(x - ox, y - oy) for x, y in e["geometry"]])))

    def ground(p):
        return H.z(p[0] + ox, p[1] + oy)

    def lane_geom(path, which):
        """which = 'right' | 'left'. Returns resampled points (2 m), per-point edge id, per-point flag multilane-oneway."""
        pts, eid, ml = [], [], []
        for u, v in zip(path, path[1:]):
            e = edges[g[u][v]["id"]]
            geo = e["geometry"] if e["from"] == u else e["geometry"][::-1]
            P = np.array([(x - ox, y - oy) for x, y in geo], dtype=float)
            at = e["attrs"]
            oneway = at["oneway"]["v"] != "no"
            lanes = max(1, int(at.get("lanes", {}).get("v", 2) or 2))
            width = at.get("width", {}).get("v")
            lane_w = min(3.5, max(2.75, (float(width) / lanes) if width else 3.0))
            if oneway:
                off = (lanes - 1) / 2.0 * lane_w * (1 if which == "right" else -1)
            else:
                per = max(1, lanes // 2)
                off = lane_w * (per - 0.5) if which == "right" else lane_w * 0.5
            if off:
                T = np.gradient(P, axis=0)
                T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
                P = P + np.stack([T[:, 1], -T[:, 0]], axis=1) * off
            for i, p in enumerate(P):
                if pts and i == 0 and np.hypot(*(np.array(pts[-1]) - p)) < 0.5:
                    continue
                pts.append(p.tolist()); eid.append(e["id"]); ml.append(oneway and lanes >= 2)
        P = np.array(pts)
        s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
        si = np.arange(0, s[-1], 2.0)
        R = np.stack([np.interp(si, s, P[:, 0]), np.interp(si, s, P[:, 1])], axis=1)
        idx = np.clip(np.searchsorted(s, si, side="right") - 1, 0, len(eid) - 1)
        return R, [eid[i] for i in idx], [ml[i] for i in idx]

    cams, rows = [], []

    def add(cid, kind, pos, pos_u, look, look_u, fov, note, seat=None, meta=None):
        d = {"id": cid, "type": "persp", "kind": kind, "pos": [round(pos[0], 3), round(pos[1], 3), round(pos_u, 3)],
             "look_at": [round(look[0], 3), round(look[1], 3), round(look_u, 3)], "fov_deg": fov, "note": note}
        if seat:
            d["seat"] = seat
        cams.append(d)
        lon, lat = tr.transform(pos[0] + ox, pos[1] + oy)
        hd = (math.degrees(math.atan2(look[0] - pos[0], look[1] - pos[1])) + 360) % 360
        r = {"id": cid, "kind": kind, "E": round(pos[0], 2), "N": round(pos[1], 2), "lat": round(lat, 6), "lon": round(lon, 6),
             "heading_deg": round(hd, 1)}
        r.update(meta or {})
        rows.append(r)

    def bridge_state(p, eid):
        on = any(b[0] == eid for b in bridges)
        if on:
            return "on"
        for bid, B in bridges:
            if np.min(np.hypot(B[:, 0] - p[0], B[:, 1] - p[1])) < 14.0:
                return "under"
        return None

    for dtag, path in (("f", fwd_path), ("r", rev_path)):
        for which, step in (("right", a.step), ("left", a.left_step)):
            R, E, ML = lane_geom(path, which)
            n = len(R)
            k = 0
            for i in range(0, n, int(step / 2)):
                if which == "left" and not ML[i]:
                    continue
                j = min(n - 1, i + int(LOOK_AHEAD / 2))
                if j - i < 5:
                    continue
                p, la = R[i], R[j]
                e = edges[E[i]]; at = e["attrs"]
                bs = bridge_state(p, E[i])
                pu, lu, seat = ground(p) + EYE, ground(la) + 1.2, None
                if bs == "on":
                    pu += 12.0; lu += 12.0
                elif bs == "under":
                    seat = "file"
                s = i * 2.0
                cid = f"au_{dtag}{'l' if which == 'left' else ''}_s{int(s):04d}"
                add(cid, "driver_eye", p, pu, la, lu, FOV_CAB,
                    f"audit r9 {'forward' if dtag == 'f' else 'reverse'} {which} lane s={s:.0f} m, edge {E[i]}" + (f", bridge:{bs}" if bs else ""),
                    seat, {"dir": dtag, "lane": which, "s_m": s, "edge": E[i], "name": at.get("name", {}).get("v", ""),
                           "highway": at["highway"]["v"], "lanes": at.get("lanes", {}).get("v"), "width": at.get("width", {}).get("v"),
                           "turn_lanes": at.get("turn:lanes", {}).get("v"), "bridge": bs or ""})

    # top-down cameras over junction nodes (degree >= 3) of both paths, merged within 35 m
    tops = []
    for nid in list(dict.fromkeys(fwd_path + rev_path)):
        nd = nodes[nid]
        if nd.get("degree", 0) < 3:
            continue
        p = np.array([nd["x"] - ox, nd["y"] - oy])
        if any(np.hypot(*(p - q)) < 35.0 for q, _ in tops):
            continue
        tops.append((p, nid))
    seg = json.loads((rdir / "gate3_segment.json").read_text(encoding="utf-8"))
    for key, rf in seg["ring_fits"].items():
        c = np.array(rf["centre_en"])
        tops = [(q, n) for q, n in tops if np.hypot(*(q - c)) > rf["radius_m"] + 10]
        tops.append((c, f"ring_{key}"))
    for p, nid in tops:
        ring = nid.startswith("ring_")
        gz = ground(p)
        add(f"au_top_{nid}", "rondo_above", p, gz + 45.0, p + np.array([0.0, 0.5]), gz, 80.0 if ring else 65.0,
            f"audit r9 top-down over {nid}", None, {"dir": "top", "node": nid})

    out = {"schema": "truck-sim-pl/gate3-cameras/1", "region": a.region,
           "frame": "local E,N,U (EPSG:2180 minus region origin; U absolute EVRF2007 NMT + height, re-seated by raycast unless seat=file)",
           "note": "map audit r9 cameras (scripts/map-audit-cameras.py)", "cameras": cams}
    op = (REPO / a.out) if not Path(a.out).is_absolute() else Path(a.out)
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    with open(op.with_suffix(".index.csv"), "w", newline="", encoding="utf-8") as f:
        keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("id", "kind", "dir", "lane", "s_m", "E", "N", "lat", "lon", "heading_deg"), k))
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    from collections import Counter
    print(f"cameras: {len(cams)}", Counter((r.get('dir'), r.get('lane')) for r in rows), "-> ", op)
    print("rev path len nodes", len(rev_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
