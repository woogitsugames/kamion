"""Generate road + terrain meshes for a region tile and export engine-ready chunks.

Usage (repo root, after build_region.py):
    uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c
    [--context]   re-extract generated/osm_context.json from the OSM cache first

Inputs : Data/Regions/<id>/{region.yaml, roads.graph.json, terrain.json, overrides.yaml,
         generated/osm_context.json}, Data/raw/derived/<id>/heightmap_2049.r16
Outputs: Data/raw/derived/<id>/world/chunk_<ci>_<cj>.glb  (big, not in git, regenerable)
         Data/raw/derived/<id>/world/preview_buildings.json (render context only)
         Data/Regions/<id>/generated/world_manifest.json   (chunks, bounds, materials, sha256)
         Data/Regions/<id>/generated/roads_qa.json         (widths, grades, junctions, low_confidence)
         Data/Regions/<id>/generated/control_cameras.json  (visual QA camera set)
Deterministic: same inputs -> byte-identical GLBs and JSON (tests/gis/test_world_*.py).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from roads import decals as DC           # noqa: E402
from roads import markings as MK          # noqa: E402
from roads import meshing as M            # noqa: E402
from roads import pipeline                # noqa: E402
from roads import standards as S          # noqa: E402
from terrain_mesh import chunks as CH     # noqa: E402
from terrain_mesh import conform as CF    # noqa: E402
from terrain_mesh.gltf import GLB, GLTF_AXES, smooth_normals  # noqa: E402
from streetscape import export as PR      # noqa: E402

LAYERS = ("road", "bridge", "markings", "paved", "buildings", "buildings_low", "furniture", "wires", "collision")
NODES = (("road", "road"), ("bridge", "bridge"), ("markings", "markings"), ("paved", "paved"),
         ("buildings", "buildings"), ("buildings_low", "buildings_lod1"), ("furniture", "furniture"),
         ("wires", "wires"), ("collision", "road_collision"))


def DEFAULT_OUT(region_id):
    return REPO / "Data" / "raw" / "derived" / region_id / "world"


REPO = pipeline.REPO
GENERATOR_VERSION = "world-c/1"

# PBR placeholders (linear albedo, roughness). WORKING_VALUE: to be replaced by the calibrated albedo
# table of docs/06 §3; values chosen in the range of measured asphalt (0.05-0.12), concrete (0.3-0.4),
# grass (0.1-0.2). `surface` = physics surface type for the vehicle model (docs/04).
MATERIALS = {
    # Ground materials with a generated PBR set (art-source/world/materials/materials_spec.json, ADR 0022):
    # `color` = the set's calibrated mean linear albedo, so the engine tint is 1; `texture_set` names the set.
    "road_asphalt": {"color": [0.131, 0.13, 0.129], "rough": 0.9, "surface": "asphalt", "texture_set": "asphalt_worn"},
    "road_asphalt_new": {"color": [0.075, 0.075, 0.073], "rough": 0.85, "surface": "asphalt",
                         "texture_set": "asphalt_sma_fresh"},
    "road_concrete": {"color": [0.30, 0.297, 0.288], "rough": 0.85, "surface": "concrete",
                      "texture_set": "concrete_cast_5m_joints", "uv1": "along_m"},
    "road_paving": {"color": [0.26, 0.255, 0.245], "rough": 0.85, "surface": "paving_stones",
                    "texture_set": "paving_20x10_grey"},
    "road_sett": {"color": [0.24, 0.22, 0.20], "rough": 0.9, "surface": "sett"},
    "road_gravel": {"color": [0.20, 0.19, 0.17], "rough": 0.95, "surface": "gravel", "texture_set": "gravel_compacted"},
    "curb_concrete": {"color": [0.28, 0.278, 0.27], "rough": 0.85, "surface": "concrete_kerb",
                      "texture_set": "kerb_concrete_1m"},
    "sidewalk_paving": {"color": [0.26, 0.255, 0.245], "rough": 0.85, "surface": "paving_stones",
                        "texture_set": "paving_20x10_grey"},
    "apron_sett": {"color": [0.27, 0.24, 0.21], "rough": 0.9, "surface": "sett"},
    # viaducts: precast-concrete modulation map projected in world metres (the deck / pier meshes have no metric UV);
    # albedo from the CC0 Bieżeństwa photo (piers mid grey, soffit in its own shadow, REVIEW r3 W4). WORKING_VALUE
    "bridge_concrete": {"color": [0.42, 0.42, 0.40], "rough": 0.85, "surface": "concrete",
                        "texture_set": "concrete_precast", "uv": "planar"},
    "bridge_soffit": {"color": [0.15, 0.15, 0.145], "rough": 0.9, "surface": "concrete",
                      "texture_set": "concrete_precast", "uv": "planar"},
    "barrier_steel": {"color": [0.55, 0.56, 0.57], "rough": 0.45, "metal": 0.9, "surface": "steel"},
    "verge_grass": {"color": [0.08, 0.105, 0.038], "rough": 0.95, "surface": "grass", "texture_set": "grass_verge"},
    "shoulder_gravel": {"color": [0.20, 0.19, 0.17], "rough": 0.95, "surface": "gravel", "texture_set": "gravel_compacted"},
    "terrain_grass": {"color": [0.08, 0.105, 0.038], "rough": 0.95, "surface": "grass", "texture_set": "grass_verge"},
    # road paint film, albedo 0.60 (0.55-0.65, r4/r6 W-H6, WORKING_VALUE) over the asphalt_worn set of the road beneath:
    # Kamion/World PBR _DECAL_PAINT wears it through to that asphalt on the aggregate peaks in the wheel paths of
    # transverse marks (TEXCOORD_1, roads.markings._paint_uv1), adds a grey-brown traffic film by age and keeps the
    # distance pre-filter towards the real asphalt albedo (0.12 m line < 1 px). ADR 0049.
    "marking_white": {"color": [0.60, 0.60, 0.59], "rough": 0.65, "surface": "paint", "texture_set": "asphalt_worn",
                      "paint": {"wheel_wear": 0.85, "age_wear": 0.25, "dirt": 0.43, "line_w_m": 0.12},
                      "decal": True, "depth_offset_m": S.MARKING_LIFT},
    "collision_asphalt": {"color": [1, 0, 1], "rough": 1.0, "surface": "asphalt", "collision": True},
    "collision_curb": {"color": [1, 0, 1], "rough": 1.0, "surface": "concrete_kerb", "collision": True},
    "collision_paving": {"color": [1, 0, 1], "rough": 1.0, "surface": "paving_stones", "collision": True},
    "collision_grass": {"color": [1, 0, 1], "rough": 1.0, "surface": "grass", "collision": True},
}
from streetscape.materials import M as _SM   # noqa: E402
from streetscape import forest_hlod as FH     # noqa: E402
MATERIALS.update(_SM)
MATERIALS.update(FH.materials())
_GLB_MATS = None


def glb_materials():
    global _GLB_MATS
    if _GLB_MATS is None:
        _GLB_MATS = {**MATERIALS, **PR.glb_materials()}
    return _GLB_MATS


WELD = {"road_asphalt", "road_asphalt_new", "road_concrete", "road_paving", "road_sett", "road_gravel", "collision_asphalt",
        "sidewalk_paving", "apron_sett"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def write_json(path: Path, obj) -> str:
    text = json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8", newline="\n")
    return sha(text.encode("utf-8"))


def r(x, n=3):
    return float(round(float(x), n))


# --------------------------------------------------------------------------------------------
def chunk_of(e, n, half, size=CH.CHUNK_M):
    nch = int(2 * half // size)
    ci = np.clip(np.floor((e + half) / size).astype(int), 0, nch - 1)
    cj = np.clip(np.floor((half - n) / size).astype(int), 0, nch - 1)
    return ci, cj


def assemble(parts, layers, half):
    """Group triangles by (chunk, layer, material); weld smooth surfaces; per-vertex normals."""
    groups = {}
    for pi, p in enumerate(parts):
        if p.layer not in layers:
            continue
        N = smooth_normals(p.V, p.T)
        cen = p.V[p.T].mean(1)
        ci, cj = chunk_of(cen[:, 0], cen[:, 1], half)
        for key in sorted(set(zip(ci.tolist(), cj.tolist()))):
            sel = (ci == key[0]) & (cj == key[1])
            g = groups.setdefault((key, p.layer, p.mat), [])
            g.append((pi, p.V, N, p.UV, p.T[sel], p.UV1, p.COL))
    out = {}
    for (key, layer, mat), items in sorted(groups.items()):
        V = np.concatenate([it[1][it[4]].reshape(-1, 3) for it in items])
        Nn = np.concatenate([it[2][it[4]].reshape(-1, 3) for it in items])
        UV = np.concatenate([it[3][it[4]].reshape(-1, 2) for it in items])
        has1 = any(it[5] is not None for it in items)
        hasc = any(it[6] is not None for it in items)
        UV1 = np.concatenate([(it[5] if it[5] is not None else np.tile([-1.0, 5.0], (len(it[1]), 1)))[it[4]].reshape(-1, 2)
                              for it in items]) if has1 else None
        COL = np.concatenate([(it[6] if it[6] is not None else np.zeros((len(it[1]), 4)))[it[4]].reshape(-1, 4)
                              for it in items]) if hasc else None
        if mat in WELD:
            q = np.round(V * 1000).astype(np.int64)
            u, inv = np.unique(q, axis=0, return_inverse=True)
            inv = inv.ravel()
            first = np.full(len(u), -1)
            first[inv[::-1]] = np.arange(len(inv))[::-1]
            Vw, UVw = V[first], UV[first]
            UV1w = UV1[first] if has1 else None
            COLw = COL[first] if hasc else None
            T = inv.reshape(-1, 3)
            T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
            Nw = smooth_normals(Vw, T)
        else:
            ids = np.concatenate([np.full(it[4].size, it[0]) * 10_000_000 + it[4].ravel() for it in items])
            u, first, inv = np.unique(ids, return_index=True, return_inverse=True)
            Vw, Nw, UVw = V[first], Nn[first], UV[first]
            UV1w = UV1[first] if has1 else None
            COLw = COL[first] if hasc else None
            T = inv.ravel().reshape(-1, 3)
        out.setdefault(key, {}).setdefault(layer, []).append({"V": Vw, "N": Nw, "UV": UVw, "T": T, "mat": mat,
                                                              "UV1": UV1w, "COL": COLw})
    return out


# --------------------------------------------------------------------------------------------
def route_polyline(region_id, w):
    """Start route (D4 candidate) as local polyline with per-vertex edge id (cameras, QA)."""
    import networkx as nx
    import roadgraph
    graph = json.loads((pipeline.REGIONS / region_id / "roads.graph.json").read_text(encoding="utf-8"))
    cand = json.loads((REPO / "docs/reports/map/candidates.json").read_text(encoding="utf-8"))
    route = next(c for c in cand["candidates"] if c["id"] == w.region["candidate"])["route"]

    def nearest(xy):
        return min(graph["nodes"], key=lambda n: math.hypot(n["x"] - xy[0], n["y"] - xy[1]))["id"]
    g = roadgraph.to_digraph(graph)
    path = nx.shortest_path(g, nearest(route["start_epsg2180"]), nearest(route["end_epsg2180"]), weight="length")
    edges = {e["id"]: e for e in graph["edges"]}
    pts, eids, nodes_s = [], [], {}
    ox, oy = w.origin
    for a, b in zip(path, path[1:]):
        e = edges[g[a][b]["id"]]
        geo = e["geometry"] if e["from"] == a else e["geometry"][::-1]
        if pts:
            geo = geo[1:]
        for x, y in geo:
            pts.append((x - ox, y - oy))
            eids.append(e["id"])
    P = np.array(pts)
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    acc = 0.0
    for a, b in zip(path, path[1:]):
        nodes_s[a] = acc
        acc += g[a][b]["length"]
    nodes_s[path[-1]] = acc
    return P, s, eids, nodes_s, path


def chain_of_edge(net, eid):
    for c in net.chains:
        if any(x == eid for x, _ in c.edges):
            return c
    return None


def surface_at(w, xy):
    """(chain, s, lat, z) of the closest chain to a local point."""
    best = None
    for c in w.net.chains:
        lo, hi = c.line.p.min(0) - 20, c.line.p.max(0) + 20
        if not (lo[0] <= xy[0] <= hi[0] and lo[1] <= xy[1] <= hi[1]):
            continue
        s, lat = c.line.project(np.asarray(xy, float))
        d = abs(lat) - float(c.hw_at(s))
        if best is None or d < best[0]:
            best = (d, c, s, lat)
    _, c, s, lat = best
    return c, s, lat, float(c.crossfall_z(s, np.clip(lat, -c.hw_at(s), c.hw_at(s))))


def cameras(region_id, w):
    P, s, eids, nodes_s, path = route_polyline(region_id, w)

    def at(st):
        st = float(np.clip(st, 0, s[-1]))
        return np.array([np.interp(st, s, P[:, 0]), np.interp(st, s, P[:, 1])])

    def lane_point(st, lane="right"):
        p = at(st)
        t = at(st + 1.0) - at(st - 1.0)
        t /= max(np.hypot(*t), 1e-9)
        c, cs, lat, z = surface_at(w, p)
        sec = c.section(cs, w.net.sec_list)
        hw = float(c.hw_at(cs))
        # rightmost lane centre in travel direction
        tch, nch = c.line.frame(cs)
        trav = 1 if float(np.dot(tch, t)) > 0 else -1
        lat_l = -trav * (hw - sec.edge_strip - sec.lane_w / 2)     # rightmost lane of travel
        q = c.line.offset_point(cs, lat_l)
        zq = float(c.crossfall_z(cs, lat_l))
        return q, zq, t

    names = [graph_name(w, e) for e in eids]
    # Andersa: last route vertex on Andersa, then back off 160 m
    idx_and = [i for i, nme in enumerate(names) if nme == "Generała Władysława Andersa"]
    s_and_end = s[idx_and[-1]]
    cams = []
    q, z, t = lane_point(s_and_end - 170)
    tgt = at(s_and_end - 60)
    _, _, _, zt = surface_at(w, tgt)
    cams.append({"id": "driver_andersa_to_putry", "type": "persp", "fov_deg": 60.0,
                 "pos": [r(q[0]), r(q[1]), r(z + 2.5)], "look_at": [r(tgt[0]), r(tgt[1]), r(zt + 1.2)],
                 "note": "truck driver eye 2.5 m, right lane of Andersa (DK19/DK65) approaching Rondo Putry"})
    # Rondo Putry from above
    ring = [c for c in w.net.chains if c.roundabout and "Putry" in graph_name(w, c.edges[0][0])]
    pts = np.vstack([c.line.p for c in ring])
    ctr = pts.mean(0)
    _, _, _, zc = surface_at(w, ctr)
    cams.append({"id": "putry_above", "type": "persp", "fov_deg": 55.0,
                 "pos": [r(ctr[0] + 70), r(ctr[1] + 80), r(zc + 42)], "look_at": [r(ctr[0]), r(ctr[1]), r(zc)],
                 "note": "Rondo Putry from ~40 m (two-level: Andersa viaduct above the ring)"})
    # depot gate: junction where the depot access road meets the public road
    gate_node = "n1882887381"
    sj = nodes_s.get(gate_node, 265.0)
    q, z, t = lane_point(sj + 30)                 # far enough out that the booms and the gatehouse are in frame
    tgt = at(max(0.0, sj - 25))
    _, _, _, zt = surface_at(w, tgt)
    cams.append({"id": "kwadrat_park_gate", "type": "persp", "fov_deg": 60.0,
                 "pos": [r(q[0]), r(q[1]), r(z + 2.5)], "look_at": [r(tgt[0]), r(tgt[1]), r(zt + 1.0)],
                 "note": "from the public road back into the Kwadrat Park depot access road (route start)"})
    # DK8/DK19 exit (end of route, Al. Tysiąclecia northbound)
    q, z, t = lane_point(s[-1] - 150)
    tgt = at(s[-1] - 40)
    _, _, _, zt = surface_at(w, tgt)
    cams.append({"id": "dk8_dk19_exit", "type": "persp", "fov_deg": 60.0,
                 "pos": [r(q[0]), r(q[1]), r(z + 2.5)], "look_at": [r(tgt[0]), r(tgt[1]), r(zt + 1.2)],
                 "note": "Al. Tysiąclecia Państwa Polskiego northbound, DK8/DK19 exit from the city"})
    # Rondo Bieżeństwa from above
    ring = [c for c in w.net.chains if c.roundabout and "Bieżeństwa" in graph_name(w, c.edges[0][0])]
    if ring:
        ctr2 = np.vstack([c.line.p for c in ring]).mean(0)
        _, _, _, zc2 = surface_at(w, ctr2)
        cams.append({"id": "biezenstwa_above", "type": "persp", "fov_deg": 55.0,
                     "pos": [r(ctr2[0] - 50), r(ctr2[1] - 45), r(zc2 + 38)],
                     "look_at": [r(ctr2[0]), r(ctr2[1]), r(zc2)], "note": "Rondo Pamięci Bieżeństwa 1915 r."})
        # side-by-side with the CC0 photo 20201102_152339 (Rakoon, docs/REFERENCES.md): pedestrian eye 1.6 m on the
        # north-east side of the ring, looking SSW across the ring under the Andersa viaduct (EC chimneys on the left)
        pe = ctr2 + np.array([0.483, 0.875]) * 46.0
        _, _, _, zpe = surface_at(w, pe)
        la = ctr2 - np.array([0.483, 0.875]) * 25.0
        cams.append({"id": "photo_biezenstwa_ground", "type": "persp", "fov_deg": 62.0,
                     "pos": [r(pe[0]), r(pe[1]), r(zpe + 1.6)], "look_at": [r(la[0]), r(la[1]), r(zc2 + 3.0)],
                     "note": "photo match: CC0 20201102_152339 Rondo Pamięci Bieżeństwa (approximate viewpoint)"})
    # Stage 3 reference stretch: driver eye (2.5 m) along the first ~420 m of the route, Kwadrat Park yard ->
    # depot gate -> Rondo Bieżeństwa (the most polished part of the tile)
    for k, (st, look, note) in enumerate(((30.0, 60.0, "Kwadrat Park yard, loading docks on the right"),
                                          (150.0, 60.0, "yard road between the halls toward the gate"),
                                          (255.0, 55.0, "depot gate (lift gate) and the exit to the public road"),
                                          (360.0, 60.0, "approach to Rondo Bieżeństwa under the Andersa viaduct"))):
        q, z, t = lane_point(st)
        tgt = at(st + look)
        _, _, _, zt = surface_at(w, tgt)
        cams.append({"id": f"stretch_{k + 1:02d}", "type": "persp", "fov_deg": 60.0, "route_s_m": st,
                     "pos": [r(q[0]), r(q[1]), r(z + 2.5)], "look_at": [r(tgt[0]), r(tgt[1]), r(zt + 1.4)],
                     "note": f"reference stretch, driver eye 2.5 m: {note}"})
    # r4 blocker check: the on-ramp from Rondo Bieżeństwa beside the Andersa westbound ramp (truck stopped at
    # s = 571 m on the walled ramp's cap, kerb ridge at s = 604 m): driver eye and an oblique view from above-left
    q, z, t = lane_point(540.0)
    tgt = at(590.0)
    _, _, _, zt = surface_at(w, tgt)
    cams.append({"id": "route_onramp_andersa", "type": "persp", "fov_deg": 60.0, "route_s_m": 540.0,
                 "pos": [r(q[0]), r(q[1]), r(z + 2.5)], "look_at": [r(tgt[0]), r(tgt[1]), r(zt + 1.0)],
                 "note": "driver eye 2.5 m on the on-ramp beside the Andersa westbound ramp (r4 blocker, s 571 / 604 m)"})
    # v3.4 signs (ADR 0023): the Andersa approach to Rondo Putry (E-1 diagram, A-7 + C-12, C-9 on the island) and a
    # close look at the entry plates (rim, weathering) from the driver's seat
    for cid, st, look, note in (("route_putry_approach", 1540.0, 120.0, "driver eye, Andersa approach to Rondo Putry: E-1 diagram, A-7 + C-12"),
                                ("route_putry_entry_signs", 1648.0, 16.0, "driver eye 12 m before the Putry entry: A-7 + C-12 plates, C-9")):
        q, z, t = lane_point(st)
        tgt = at(st + look)
        _, _, _, zt = surface_at(w, tgt)
        cams.append({"id": cid, "type": "persp", "fov_deg": 60.0, "route_s_m": st,
                     "pos": [r(q[0]), r(q[1]), r(z + 2.5)], "look_at": [r(tgt[0]), r(tgt[1]), r(zt + 2.0)], "note": note})
    q2 = at(585.0)
    _, _, _, z2 = surface_at(w, q2)
    t2 = at(590.0) - at(580.0)
    t2 = t2 / max(np.hypot(*t2), 1e-9)
    pos2 = q2 - t2 * 35.0 + np.array([-t2[1], t2[0]]) * 22.0
    cams.append({"id": "route_onramp_andersa_above", "type": "persp", "fov_deg": 55.0,
                 "pos": [r(pos2[0]), r(pos2[1]), r(z2 + 16.0)], "look_at": [r(q2[0]), r(q2[1]), r(z2)],
                 "note": "oblique from above-left over the on-ramp / Andersa ramp end (r4 blocker, s 571-610 m)"})
    for k, hd in enumerate(w.stats.get("hero_docks", [])[:1]):
        pos = hd["mid"] + hd["nout"] * 26.0 - hd["d"] * 18.0
        tgt = hd["mid"] + hd["d"] * 6.0
        cams.append({"id": "stretch_05_docks", "type": "persp", "fov_deg": 60.0,
                     "pos": [r(pos[0]), r(pos[1]), r(hd["z"] + 2.5)], "look_at": [r(tgt[0]), r(tgt[1]), r(hd["z"] + 2.0)],
                     "note": f"reference stretch: Kwadrat Park loading docks ({hd['n']} doors) from the yard, eye 2.5 m"})
    # Gate 3 street / roundabout views (r5 W-H3+ evidence: parked cars, shelters, bins, noise barriers) as editor
    # control cameras, copied from Data/Regions/<id>/gate3_cameras.json (scripts/gate3-segment.py) by id.
    g3 = pipeline.REGIONS / region_id / "gate3_cameras.json"
    if g3.exists():
        want = ("g3a_rondo_bie_approach", "g3a_eye_s0262", "g3b_eye_s1482", "g3b_rondo_putry_approach")
        for c in json.loads(g3.read_text(encoding="utf-8"))["cameras"]:
            if c["id"] in want:
                cams.append({"id": c["id"], "type": "persp", "fov_deg": c.get("fov_deg", 60.0),
                             "pos": c["pos"], "look_at": c["look_at"], "note": "gate3: " + c.get("note", "")})
    cams.append({"id": "ortho_putry", "type": "ortho", "center": [r(ctr[0]), r(ctr[1])], "size_m": 260.0,
                 "height": r(zc + 120), "note": "orthographic top view for overlay on the GUGiK orthophoto"})
    return cams


_names = {}


def graph_name(w, eid):
    if not _names:
        g = json.loads((pipeline.REGIONS / w.region["id"] / "roads.graph.json").read_text(encoding="utf-8"))
        for e in g["edges"]:
            _names[e["id"]] = e["attrs"].get("name", {}).get("v", "") or ""
    return _names.get(eid, "")


# --------------------------------------------------------------------------------------------
def preview_buildings(region_id, w, out: Path):
    fc = json.loads((pipeline.REGIONS / region_id / "buildings.geojson").read_text(encoding="utf-8"))
    ox, oy = w.origin
    items = []
    for f in fc["features"]:
        p = f["properties"]
        if p.get("is_roof_only"):
            continue
        for poly in f["geometry"]["coordinates"]:
            ring = np.array(poly[0]) - np.array([ox, oy])
            zb = float(np.min(w.hf.sample(ring[:, 0], ring[:, 1])))
            items.append({"id": f["id"], "ring": [[r(x, 2), r(y, 2)] for x, y in ring[:-1]], "z0": r(zb, 2),
                          "h": r(p.get("height_m") or 6.0, 2), "function": p.get("function")})
    out.write_text(json.dumps({"note": "render context only (extruded LoD1); not a game asset",
                               "buildings": items}, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def preview_trees(region_id, w, zc, mask, out: Path):
    """Render-context vegetation: points scattered (fixed seed) in BDOT10k forest (OT_PTLZ_A) and shrub
    (OT_PTRK_A) polygons, kept >= 3 m from roads. Not a game asset: the game will use GUGiK 3D tree
    models (Modele 3D drzew 2023) — see docs/WORLD_GENERATION.md."""
    import pyogrio
    import shapely
    from scipy import ndimage
    sys.path.insert(0, str(REPO / "tools" / "worldgen"))
    from build_region import extract_from_zip, manifest_files
    t = w.region["teryt_powiat"]
    try:
        z = manifest_files(f"gugik-bdot10k-{t}")[0]
    except SystemExit:
        return 0
    if not z.exists():
        return 0
    gdir = REPO / "Data" / "raw" / "gugik" / f"bdot10k-{t}" / "gpkg"
    b = w.region["bbox"]
    box = (b["xmin"], b["ymin"], b["xmax"], b["ymax"])
    tile = shapely.box(*box)
    near_road = ndimage.binary_dilation(mask, iterations=3)
    rng = np.random.default_rng(20261109)
    ox, oy = w.origin
    pts = []
    for layer, spacing, kind in (("OT_PTLZ_A", 4.5, "forest"), ("OT_PTRK_A", 3.5, "shrub")):
        df = pyogrio.read_dataframe(extract_from_zip(z, f"__{layer}.gpkg", gdir), bbox=box)
        geom = shapely.intersection(shapely.union_all(df.geometry.values), tile)
        x0, y0, x1, y1 = geom.bounds
        gx, gy = np.meshgrid(np.arange(x0, x1, spacing), np.arange(y0, y1, spacing))
        P = np.column_stack([gx.ravel(), gy.ravel()]) + rng.uniform(-spacing * 0.45, spacing * 0.45, (gx.size, 2))
        P = P[shapely.contains_xy(geom, P[:, 0], P[:, 1])]
        for x, y in P:
            i, j = int(round(x - b["xmin"])), int(round(b["ymax"] - y))
            if not (0 <= j < zc.shape[0] and 0 <= i < zc.shape[1]) or near_road[j, i]:
                continue
            h = rng.uniform(13, 24) if kind == "forest" else rng.uniform(2.5, 5.0)
            pts.append([r(x - ox, 2), r(y - oy, 2), r(zc[j, i], 2), r(h, 1), 0 if kind == "forest" else 1])
    out.write_text(json.dumps({"note": "render context only; BDOT10k OT_PTLZ_A/OT_PTRK_A scatter, seed 20261109",
                               "columns": ["e", "n", "z", "h", "kind"], "trees": pts}), encoding="utf-8")
    return len(pts)


# --------------------------------------------------------------------------------------------
def build(region_id: str, out_root: Path | None = None, verbose=True):
    t0 = time.time()
    log = (lambda *a: print(f"[world {time.time() - t0:6.1f}s]", *a)) if verbose else (lambda *a: None)
    # pass 1: geometry with the raw NMT -> bridge decks -> remove deck-contaminated NMT under them
    w0 = pipeline.build(region_id)
    deck_parts = [p for p in w0.buf.parts if p.layer == "bridge" and not p.src.endswith(":parapet")]
    for p in deck_parts:
        p.footprint = True
    deck, deck_mask = CF.rasterise(deck_parts, w0.hf)
    thick = S.BRIDGE_DECK_THICKNESS + S.BRIDGE_KERB_H
    clean, bad = CF.clean_under_bridges(w0.hf.z, deck, deck_mask, thick)
    log(f"pass 1: deck nodes {int(deck_mask.sum())}, NMT nodes replaced under decks {int(bad.sum())}")
    hf = pipeline.P.Heightfield(clean, w0.hf.bbox, (w0.hf.ox, w0.hf.oy))
    # pass 2: final geometry on the cleaned ground model
    w = pipeline.build(region_id, hf=hf)
    w.stats["nmt_replaced_under_decks"] = int(bad.sum())
    log(f"network: {len(w.net.chains)} chains, {len(w.junctions)} junctions")
    mk_report = {}
    MK.build_markings(w.buf, w.net, w.junctions, w.ctx["points"], mk_report)
    log("markings", mk_report.get("markings"))
    DC.build(w.buf, w.net, w.junctions, mk_report)
    log("decals", mk_report.get("decals"))

    # terrain conform (roads + paved areas) + streetscape (buildings, yards, furniture, vegetation)
    road_z, rmask = CF.rasterise([p for p in w.buf.parts if p.layer == "road"], w.hf)
    deck_parts = [p for p in w.buf.parts if p.layer == "bridge" and not p.src.endswith(":parapet")]
    for p in deck_parts:
        p.footprint = True
    deck, deck_mask = CF.rasterise(deck_parts, w.hf)
    for p in deck_parts:
        p.footprint = False
    from streetscape import stage as SS
    st = SS.run(w, road_z, rmask, deck, deck_mask, thick, log)
    zc, dist, mask = st["zc"], st["dist"], st["mask"]
    w.stats["hero_docks"] = []
    for dk in st["docks"]:
        if "9962cca0" not in dk["id"] and not dk.get("hero"):
            continue
        p, q = (np.asarray(x, float) for x in dk["edge"])
        d = (q - p) / np.linalg.norm(q - p)
        nout = np.array([d[1], -d[0]])
        u0, u1 = dk["docks"][0]["u"], dk["docks"][-1]["u"]
        mid = p + d * (0.5 * (u0 + u1))
        w.stats["hero_docks"].append({"mid": mid, "d": d, "nout": nout, "z": dk["yard_z"], "n": len(dk["docks"])})
    log(f"terrain conformed: footprint {int(rmask.sum())} road + {int(mask.sum() - rmask.sum())} paved nodes")

    def on_ground_road(q):
        i = int(round(q[0] - w.hf.x0))
        j = int(round(w.hf.y1 - q[1]))
        if 0 <= j < mask.shape[0] and 0 <= i < mask.shape[1]:
            return bool(mask[max(0, j - 2):j + 3, max(0, i - 2):i + 3].any())
        return False
    for c in w.net.chains:
        M.build_bridge_supports(w.buf, c, w.hf, on_ground_road, w.bridges)

    half = w.region["bbox"]["width_m"] / 2
    e0 = w.region["bbox"]["xmin"] - w.origin[0]
    n0 = w.region["bbox"]["ymax"] - w.origin[1]
    terrain = CH.build_chunks(zc, mask, e0, n0, w.region["bbox"]["width_m"], col=st["col"])
    log("terrain chunks", len(terrain))
    roads = assemble(w.buf.parts, LAYERS, half)
    log("road chunks", len(roads))

    out_root = out_root or (REPO / "Data" / "raw" / "derived" / region_id / "world")
    out_root.mkdir(parents=True, exist_ok=True)
    inst_by_chunk = {}
    for it in sorted(st["instances"], key=lambda t: (t["p"], t["e"], t["n"])):
        ci_, cj_ = chunk_of(np.array([it["e"]]), np.array([it["n"]]), half)
        inst_by_chunk.setdefault((int(ci_[0]), int(cj_[0])), []).append(it)
    props_meta = PR.export(st["codes"], st["boards"], out_root.parent / "props" if out_root != DEFAULT_OUT(region_id) else None)
    chunks_meta = []
    for key in sorted(terrain):
        ci, cj = key
        glb = GLB(glb_materials())
        tri = {}
        for li, prims in sorted(terrain[key].items()):
            glb.add_mesh(f"terrain_lod{li}", prims, {"lod": li, "spacing_m": CH.LODS[li]})
            tri[f"terrain_lod{li}"] = int(sum(len(p["T"]) for p in prims))
        layers = roads.get(key, {})
        for layer, node in NODES:
            prims = layers.get(layer, [])
            if prims:
                glb.add_mesh(node, prims, {"layer": layer, "collision": layer == "collision"})
                tri[node] = int(sum(len(p["T"]) for p in prims))
        cells = sorted((cid, c) for cid, c in st["forest_hlod"].items() if c["chunk"] == key)
        cell_meta = []
        for cid, c in cells:
            ex = {"layer": "forest_hlod", "cell": cid, "bbox_local_m": c["bbox"], "trees": c["trees"],
                  "switch_m": {p_: pol["forest_hlod_m"] for p_, pol in LOD_POLICY.items()}}
            glb.add_mesh(f"forest_hlod_{cid}", c["prims"], ex)
            cell_meta.append({"id": cid, "bbox_local_m": c["bbox"], "tris": c["tris"], "trees": c["trees"],
                              "mix": c["mix"]})
        if cells:
            tri["forest_hlod"] = int(sum(c["tris"] for _, c in cells))
        data = glb.bytes({"region": region_id, "chunk": [ci, cj], "axes": GLTF_AXES})
        fn = f"chunk_{ci}_{cj}.glb"
        (out_root / fn).write_bytes(data)
        # Low/Medium variant: no 1 m terrain LOD, no detailed buildings (LOD1 prisms only)
        glb_lo = GLB(glb_materials(), compact=True)
        for li, prims in sorted(terrain[key].items()):
            if li >= 1:
                glb_lo.add_mesh(f"terrain_lod{li}", prims, {"lod": li, "spacing_m": CH.LODS[li]})
        for layer, node in NODES:
            prims = layers.get(layer, [])
            if prims and layer != "buildings":
                glb_lo.add_mesh(node, prims, {"layer": layer, "collision": layer == "collision"})
        for cid, c in cells:
            glb_lo.add_mesh(f"forest_hlod_{cid}", c["prims"], {"layer": "forest_hlod", "cell": cid,
                                                               "bbox_local_m": c["bbox"], "trees": c["trees"],
                                                               "switch_m": {p_: pol["forest_hlod_m"]
                                                                            for p_, pol in LOD_POLICY.items()}})
        data_lo = glb_lo.bytes({"region": region_id, "chunk": [ci, cj], "axes": GLTF_AXES, "variant": "low"})
        fn_lo = f"chunk_{ci}_{cj}.low.glb"
        (out_root / fn_lo).write_bytes(data_lo)
        allz = [p["V"][:, 2] for p in terrain[key][0]] + [p["V"][:, 2] for L in layers.values() for p in L]
        zz = np.concatenate(allz)
        inst = inst_by_chunk.get(key, [])
        ifn = f"instances_{ci}_{cj}.json"
        itext = json.dumps({"chunk": [ci, cj], "frame": "local E,N,U; yaw about U, rotates prototype +y",
                            "instances": inst}, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        (out_root / ifn).write_text(itext, encoding="utf-8", newline="\n")
        chunks_meta.append({
            "id": f"{ci}_{cj}", "file": f"Data/raw/derived/{region_id}/world/{fn}", "bytes": len(data),
            "sha256": sha(data),
            "bounds_local_m": {"e_min": e0 + ci * CH.CHUNK_M, "e_max": e0 + (ci + 1) * CH.CHUNK_M,
                               "n_min": n0 - (cj + 1) * CH.CHUNK_M, "n_max": n0 - cj * CH.CHUNK_M,
                               "z_min_evrf2007": r(zz.min(), 2), "z_max_evrf2007": r(zz.max(), 2)},
            "triangles": tri,
            "forest_cells": cell_meta,
            "materials": sorted({p["mat"] for L in layers.values() for p in L} | {"terrain_grass"}),
            "instances": {"file": f"Data/raw/derived/{region_id}/world/{ifn}", "count": len(inst),
                          "sha256": sha(itext.encode("utf-8"))},
            "low": {"file": f"Data/raw/derived/{region_id}/world/{fn_lo}", "bytes": len(data_lo),
                    "sha256": sha(data_lo)},
        })
    log("exported", len(chunks_meta), "GLB,", sum(c["bytes"] for c in chunks_meta) // 2**20, "MiB (High), ",
        sum(c["low"]["bytes"] for c in chunks_meta) // 2**20, "MiB (Low)")

    gen = pipeline.REGIONS / region_id / "generated"
    srcs = {}
    for k in ("roads.graph.json", "terrain.json", "overrides.yaml", "generated/osm_context.json"):
        p = pipeline.REGIONS / region_id / k
        srcs[k] = sha(p.read_bytes()) if p.exists() else None
    tm = json.loads((pipeline.REGIONS / region_id / "terrain.json").read_text(encoding="utf-8"))
    srcs["heightmap.r16 (Data/raw)"] = tm["sha256_r16"]
    manifest = {
        "schema": "truck-sim-pl/world-manifest/1", "region": region_id, "generator": GENERATOR_VERSION,
        "origin_epsg2180": {"x": w.origin[0], "y": w.origin[1]},
        "units": "metres; local E = x - origin.x, N = y - origin.y; heights absolute PL-EVRF2007-NH",
        "gltf_axes": GLTF_AXES,
        "chunk_size_m": CH.CHUNK_M,
        "terrain_lods": [{"lod": i, "spacing_m": s, "suggested_switch_m": [0, 120, 300, 700][i]}
                         for i, s in enumerate(CH.LODS)],
        "nodes": {"terrain_lod<k>": "terrain LODs (with skirts); COLOR_0 = ground masks (R dist to road/20 m, "
                                    "G forest floor, B unmown, A bare soil)",
                  "road": "ground-level road surfaces: carriageways, junction patches, kerbs, sidewalks; "
                          "TEXCOORD_1 = (lane coordinate, distance to carriageway edge m)",
                  "bridge": "bridge decks, soffits, parapets, abutments, piers (low confidence)",
                  "markings": "horizontal markings decal mesh (lift %.3f m, use depth offset)" % S.MARKING_LIFT,
                  "paved": "yards, parking lots, dock aprons, set-back paths + edging; TEXCOORD_1 = (distance to "
                           "the area edge m, distance to a building wall m)",
                  "buildings": "LOD0 buildings with openings, docks, roofs",
                  "buildings_lod1": "LOD1 prisms with the same wall materials",
                  "furniture": "linear furniture: fences, guard rails, noise barriers, retaining walls",
                  "wires": "power-line conductors as thin ribbons: TEXCOORD_0 = (side -1/+1, physical half width m), "
                           "COLOR_0 = tangent * 0.5 + 0.5; the engine re-expands them towards the camera to >= 1 px",
                  "forest_hlod_<i>_<j>": "forest HLOD cell (64 m): canopy + alpha-tested edge walls; draw it instead "
                                         "of the trees with instance field fc = <i>_<j> when the cell bbox is farther "
                                         "than lod_policy.<profile>.forest_hlod_m; textures: material extras "
                                         "texture_ref (art-source/world/vegetation/forest_*.png)",
                  "road_collision": "collision: smooth road surfaces (4 m stations, no flanges), paved areas, "
                                    "LOD1 buildings, fences/rails/walls; one primitive per surface material"},
        "instances": "Data/raw/derived/<id>/world/instances_<ci>_<cj>.json: point instances {p: prototype, e, n, z, "
                     "yaw [, sz scale z][, h/v/lean for trees]} of art-source/world/props/street_props.glb and "
                     "art-source/world/vegetation/trees.glb (+ trees_lod2.glb impostors)",
        "lod_policy": LOD_POLICY,
        "materials": MATERIALS, "chunks": chunks_meta, "sources_sha256": srcs,
        "overrides_applied": w.net.overrides_applied, "overrides_stale": w.net.overrides_stale,
    }
    write_json(gen / "world_manifest.json", manifest)
    qa = qa_report(w, mk_report, mask)
    write_json(gen / "roads_qa.json", qa)
    cams = cameras(region_id, w)
    write_json(gen / "control_cameras.json", {"schema": "truck-sim-pl/control-cameras/1", "region": region_id,
                                              "frame": "local E,N,U (U absolute EVRF2007)", "cameras": cams})
    budget = mesh_budget(chunks_meta, inst_by_chunk, props_meta, cams)
    write_json(gen / "streetscape_qa.json", {"schema": "truck-sim-pl/streetscape-qa/1", "region": region_id,
                                             **st["report"], "mesh_budget": budget})
    walls = CF.terrain_walls(w.buf.parts, zc, w.hf, mask=mask)
    log("terrain walls > %.2f m:" % walls["thresh_m"], walls["count"], "max", walls["max_m"])
    write_json(gen / "terrain_walls_qa.json", walls)
    if os.environ.get("WORLDGEN_DUMP_WALLS"):     # debug: ground parts + conformed terrain for offline wall analysis
        import pickle
        keep = [(p.layer, p.mat, p.src, p.V, p.T) for p in w.buf.parts if p.layer in ("road", "paved")]
        with open(os.environ["WORLDGEN_DUMP_WALLS"], "wb") as fh:
            pickle.dump({"parts": keep, "zc": zc, "mask": mask, "x0": w.hf.x0, "y1": w.hf.y1}, fh)
    np.save(out_root / "terrain_conformed.npy", zc.astype(np.float32))
    log("done")
    return w, manifest, qa


# --------------------------------------------------------------------------------------------
# LOD policy (WORKING_VALUE until measured on the Samsung A16 / Mali-G57 MC2, docs/06 §6):
#   High: terrain LOD0 < 330 m, LOD1 < 600 m, LOD2 beyond; buildings LOD0 < 700 m; trees LOD0 < 35 m,
#         LOD1 < 80 m, impostor < 1500 m; forest stands (trees with "fc") are replaced by their forest HLOD
#         cell when the cell bbox is > 120 m away (v3.1); props LOD0 < 120 m, LOD1 < 650 m.
#   Low : terrain LOD1 < 330 m, LOD2 < 600 m, LOD3 beyond; buildings LOD1; trees LOD1 < 35 m, impostor < 400 m,
#         culled beyond; forest HLOD 70-1000 m, culled beyond; props LOD1 < 250 m, culled beyond;
#         linear furniture < 400 m.
#   Parked cars / vans (ADR 0041): InstanceImporter 25 / 90 / 400 m x lodBias (High 1.5, Low 0.5).
# v3 had trees LOD0 < 80 m / LOD1 < 250 m and no forest HLOD (DK8 forest frame 8.2 M triangles on High).
LOD_POLICY = {
    "High": {"terrain": [[330, 0], [600, 1], [1e9, 2]], "bld": 700,
             "tree": [[35, "tris_lod0"], [80, "tris_lod1"], [1500, "tris_lod2"]],
             "forest_hlod_m": 120, "forest_hlod_cull_m": 1e9,
             "prop": [[120, "tris_lod0"], [650, "tris_lod1"]], "furn": 1e9,
             "car": [[37.5, "tris_lod0"], [135, "tris_lod1"], [600, "tris_lod2"]]},
    "Low": {"terrain": [[330, 1], [600, 2], [1e9, 3]], "bld": 0,
            "tree": [[35, "tris_lod1"], [400, "tris_lod2"]], "forest_hlod_m": 70, "forest_hlod_cull_m": 1000,
            "prop": [[250, "tris_lod1"]], "furn": 400,
            "car": [[12.5, "tris_lod0"], [45, "tris_lod1"], [200, "tris_lod2"]]},
}


def _bbox_dist(b, p):
    dx = max(b[0] - p[0], 0.0, p[0] - b[2])
    dy = max(b[1] - p[1], 0.0, p[1] - b[3])
    return math.hypot(dx, dy)


def mesh_budget(chunks_meta, inst_by_chunk, props_meta, cams):
    """Static triangles/materials per chunk + per-camera frame estimate (120 deg wedge around the view) with a
    breakdown by category (terrain, roads = road + bridge + markings + paved, furniture, buildings, trees per
    LOD, forest HLOD, props)."""
    tp = REPO / "art-source" / "world" / "vegetation" / "trees_meta.json"
    trees = json.loads(tp.read_text(encoding="utf-8"))["trees"] if tp.exists() else {}

    def itris(it, key):
        if it["p"].startswith("tree_"):
            m = trees.get(f"{it['p']}_{it.get('v', 0)}")
            return m.get(key, 0) if m else 0
        m = props_meta.get(it["p"]) or {}
        return m.get(key, m.get("tris_lod1", 0))

    per_chunk = []
    for ch in chunks_meta:
        t = ch["triangles"]
        stat = sum(t.get(k, 0) for k in ("road", "bridge", "markings", "paved", "furniture", "wires"))
        ci, cj = (int(x) for x in ch["id"].split("_"))
        inst = inst_by_chunk.get((ci, cj), [])
        per_chunk.append({"chunk": ch["id"], "materials": len(ch["materials"]),
                          "tris_high_static": stat + t.get("terrain_lod0", 0) + t.get("buildings", 0),
                          "tris_low_static": stat + t.get("terrain_lod1", 0) + t.get("buildings_lod1", 0),
                          "tris_forest_hlod": t.get("forest_hlod", 0),
                          "instances": len(inst), "trees": sum(1 for i in inst if i["p"].startswith("tree_"))})
    frames = []
    for cam in cams:
        if cam["type"] != "persp":
            continue
        pos = np.array(cam["pos"][:2])
        look = np.array(cam["look_at"][:2]) - pos
        look /= max(np.linalg.norm(look), 1e-9)
        res = {"camera": cam["id"]}
        for prof, pol in LOD_POLICY.items():
            cat = {}

            def add(k, v):
                cat[k] = cat.get(k, 0) + int(v)
            mats = set()
            for ch in chunks_meta:
                b = ch["bounds_local_m"]
                c = np.array([(b["e_min"] + b["e_max"]) / 2, (b["n_min"] + b["n_max"]) / 2])
                d = float(np.linalg.norm(c - pos))
                if d > 1600 or (d > 200 and float(np.dot((c - pos) / d, look)) < 0.5):
                    continue
                t = ch["triangles"]
                lod = next(l for lim, l in pol["terrain"] if d < lim)
                add("terrain", t.get(f"terrain_lod{lod}", 0))
                add("roads", sum(t.get(k, 0) for k in ("road", "bridge", "markings", "paved")))
                add("furniture", (t.get("furniture", 0) + t.get("wires", 0)) if d < pol["furn"] else 0)
                add("buildings", t.get("buildings", 0) if d < pol["bld"] else t.get("buildings_lod1", 0))
                mats |= set(ch["materials"])
                far_cells = set()
                for fc in ch.get("forest_cells", []):
                    dfc = _bbox_dist(fc["bbox_local_m"], pos)
                    if dfc > pol["forest_hlod_m"]:
                        far_cells.add(fc["id"])
                        if dfc < pol["forest_hlod_cull_m"]:
                            add("forest_hlod", fc["tris"])
                ci, cj = (int(x) for x in ch["id"].split("_"))
                for it in inst_by_chunk.get((ci, cj), []):
                    if it.get("fc") in far_cells:
                        continue
                    di = math.hypot(it["e"] - pos[0], it["n"] - pos[1])
                    if di > 200 and float(np.dot((np.array([it["e"], it["n"]]) - pos) / di, look)) < 0.5:
                        continue
                    is_tree = it["p"].startswith("tree_")
                    rule = pol["tree"] if is_tree else pol["prop"]
                    if it["p"].startswith(("car_", "van_")):   # 3 LODs, InstanceImporter.Policy 25/90/400 m x lodBias
                        rule = pol["car"]
                    if it["p"].startswith("landmark_"):       # landmarks are never culled (LOD1 beyond 650 m)
                        rule = [[650, "tris_lod0"], [1e9, "tris_lod1"]]
                    key = next((k for lim, k in rule if di < lim), None)
                    if key:
                        add(("trees_" + key[5:]) if is_tree else "props", itris(it, key))
            res[f"tris_{prof.lower()}"] = int(sum(cat.values()))
            res[f"by_category_{prof.lower()}"] = dict(sorted(cat.items()))
            res[f"materials_{prof.lower()}"] = len(mats)
        frames.append(res)
    return {"lod_policy": LOD_POLICY, "per_chunk": per_chunk, "frame_estimate": frames,
            "note": "frame estimate = chunks/instances within 1.6 km in a 120 deg wedge (everything within 200 m), "
                    "no occlusion culling; forest HLOD cells beyond forest_hlod_m replace their trees; "
                    "docs/06 par. 6 hypotheses: Low <= 400-600 k tris, High <= 1.5-2 M"}


def budget_from_disk(region_id: str, out_root: Path | None = None):
    """Recompute the mesh budget from the exported manifest + instance files (after a LOD policy change)."""
    gen = pipeline.REGIONS / region_id / "generated"
    man = json.loads((gen / "world_manifest.json").read_text(encoding="utf-8"))
    cams = json.loads((gen / "control_cameras.json").read_text(encoding="utf-8"))["cameras"]
    pm = json.loads((REPO / "art-source/world/props/props_meta.json").read_text(encoding="utf-8"))["prototypes"]
    inst = {}
    for ch in man["chunks"]:
        ci, cj = (int(x) for x in ch["id"].split("_"))
        p = (out_root / Path(ch["instances"]["file"]).name) if out_root else REPO / ch["instances"]["file"]
        inst[(ci, cj)] = json.loads(p.read_text(encoding="utf-8"))["instances"]
    return mesh_budget(man["chunks"], inst, pm, cams)


def qa_report(w, mk_report, mask):
    from roads.geom import Polyline
    net = w.net
    chains = []
    dev_all = []
    for c in net.chains:
        if c.meta.get("absorbed"):
            continue
        raw = Polyline(c.raw)
        k = max(1, len(c.line.p) // 200)
        dev = [abs(raw.project(p)[1]) for p in c.line.p[::k]]
        dev_all += dev
        secs = [net.sec_list[i] for i in np.unique(c.sec_idx)]
        st = w.profiles["chains"][c.id]
        chains.append({
            "id": c.id, "length_m": r(c.length, 1), "highway": sorted({s.highway for s in secs}),
            "width_m": sorted({s.width for s in secs}), "width_src": sorted({s.width_src for s in secs}),
            "lanes": sorted({s.lanes for s in secs}), "max_grade": st["max_grade"],
            "grade_limit": st["grade_limit_difficult"], "profile_rms_vs_nmt_m": st["rms_vs_nmt_m"],
            "bridge_m": st["bridge_m"], "axis_smoothing_dev_max_m": r(max(dev), 2),
            "sidewalk_frac": r(np.mean([c.side[sd]["w"].mean() > 0.5 for sd in "LR"]), 2),
            "overrides": sorted({s.provenance.get("authored_override") for s in secs} - {None}),
        })
    dev_all = np.array(dev_all)
    pstats = w.stats["patch"]
    over = [c for c in chains if c["max_grade"] > c["grade_limit"]]
    return {
        "schema": "truck-sim-pl/roads-qa/1", "region": w.region["id"],
        "summary": {
            "chains": len(chains), "junctions": len(w.junctions),
            "junction_patches": {k: v for k, v in pstats.items() if not k.endswith("_ids")},
            "junctions_repaired": pstats.get("repaired_ids", []),
            "junctions_earclip": pstats.get("earclip_ids", []),
            "roundabout_junctions": sum(1 for j in w.junctions if j.roundabout),
            "signalised_junctions": sum(1 for j in w.junctions if j.signalized),
            "grade_over_limit": [c["id"] for c in over],
            "axis_smoothing_deviation_m": {"p50": r(np.percentile(dev_all, 50), 3),
                                           "p95": r(np.percentile(dev_all, 95), 3),
                                           "max": r(dev_all.max(), 3)},
            "footprint_nodes": int(mask.sum()),
            "nmt_nodes_replaced_under_decks": w.stats.get("nmt_replaced_under_decks", 0),
            "markings": mk_report.get("markings", {}),
            "markings_overlap_removed_tris": mk_report.get("overlap_removed_tris", 0),
            "decals": mk_report.get("decals", {}),
            "crossings_snapped": mk_report.get("crossings_snapped", 0),
            "crossings_skipped": mk_report.get("crossings_skipped", []),
            "bridges": w.bridges,
            "walled_ramps": w.profiles.get("walled_ramps", []),
            "clearance_by_class_m": S.CLEARANCE_BY_CLASS,
            "fork_tapers": w.stats.get("fork_tapers", []),
            "overrides_applied": net.overrides_applied, "overrides_stale": net.overrides_stale,
            "low_confidence": [
                "bridge deck heights interpolated between abutments (NMT = ground under deck); piers by rule",
                "sidewalks inferred from parallel OSM footways (≤ 1.4 m from the sidewalk centre line)",
                "kerb returns: WORKING_VALUE radii by class (standards.CURB_RADIUS)",
                "carriageway width: BDOT10k clamped to PTB2022 §17 ranges, else class standard",
            ],
        },
        "junction_notes": {j.id: j.notes for j in w.junctions if j.notes},
        "chains": chains,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--context", action="store_true", help="re-extract generated/osm_context.json first")
    ap.add_argument("--budget-only", action="store_true",
                    help="recompute mesh_budget in streetscape_qa.json from the exported files (no rebuild)")
    a = ap.parse_args()
    if a.budget_only:
        gen = pipeline.REGIONS / a.region / "generated"
        qa = json.loads((gen / "streetscape_qa.json").read_text(encoding="utf-8"))
        qa["mesh_budget"] = budget_from_disk(a.region)
        write_json(gen / "streetscape_qa.json", qa)
        for f in qa["mesh_budget"]["frame_estimate"]:
            print(f["camera"], f["tris_high"], f["tris_low"])
        return
    if a.context:
        from roads import context
        reg = pipeline.load_region(a.region)
        b = reg["bbox"]
        ctx = context.extract((b["xmin"], b["ymin"], b["xmax"], b["ymax"]))
        p = pipeline.REGIONS / a.region / "generated" / "osm_context.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(ctx, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
                     encoding="utf-8", newline="\n")
    build(a.region)


if __name__ == "__main__":
    main()
