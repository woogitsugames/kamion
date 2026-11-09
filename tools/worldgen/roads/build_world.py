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
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from roads import markings as MK          # noqa: E402
from roads import meshing as M            # noqa: E402
from roads import pipeline                # noqa: E402
from roads import standards as S          # noqa: E402
from terrain_mesh import chunks as CH     # noqa: E402
from terrain_mesh import conform as CF    # noqa: E402
from terrain_mesh.gltf import GLB, GLTF_AXES, smooth_normals  # noqa: E402

REPO = pipeline.REPO
GENERATOR_VERSION = "world-c/1"

# PBR placeholders (linear albedo, roughness). WORKING_VALUE: to be replaced by the calibrated albedo
# table of docs/06 §3; values chosen in the range of measured asphalt (0.05-0.12), concrete (0.3-0.4),
# grass (0.1-0.2). `surface` = physics surface type for the vehicle model (docs/04).
MATERIALS = {
    "road_asphalt": {"color": [0.075, 0.075, 0.072], "rough": 0.9, "surface": "asphalt"},
    "road_concrete": {"color": [0.32, 0.32, 0.30], "rough": 0.85, "surface": "concrete"},
    "road_paving": {"color": [0.30, 0.27, 0.24], "rough": 0.85, "surface": "paving_stones"},
    "road_sett": {"color": [0.24, 0.22, 0.20], "rough": 0.9, "surface": "sett"},
    "road_gravel": {"color": [0.30, 0.27, 0.22], "rough": 0.95, "surface": "gravel"},
    "curb_concrete": {"color": [0.40, 0.40, 0.38], "rough": 0.85, "surface": "concrete_kerb"},
    "sidewalk_paving": {"color": [0.34, 0.32, 0.29], "rough": 0.85, "surface": "paving_stones"},
    "apron_sett": {"color": [0.27, 0.24, 0.21], "rough": 0.9, "surface": "sett"},
    "bridge_concrete": {"color": [0.42, 0.42, 0.40], "rough": 0.85, "surface": "concrete"},
    "barrier_steel": {"color": [0.55, 0.56, 0.57], "rough": 0.45, "metal": 0.9, "surface": "steel"},
    "verge_grass": {"color": [0.11, 0.15, 0.06], "rough": 0.95, "surface": "grass"},
    "shoulder_gravel": {"color": [0.30, 0.27, 0.22], "rough": 0.95, "surface": "gravel"},
    "terrain_grass": {"color": [0.11, 0.15, 0.06], "rough": 0.95, "surface": "grass"},
    "marking_white": {"color": [0.72, 0.72, 0.69], "rough": 0.6, "surface": "paint",
                      "decal": True, "depth_offset_m": S.MARKING_LIFT},
    "collision_asphalt": {"color": [1, 0, 1], "rough": 1.0, "surface": "asphalt", "collision": True},
    "collision_curb": {"color": [1, 0, 1], "rough": 1.0, "surface": "concrete_kerb", "collision": True},
    "collision_paving": {"color": [1, 0, 1], "rough": 1.0, "surface": "paving_stones", "collision": True},
    "collision_grass": {"color": [1, 0, 1], "rough": 1.0, "surface": "grass", "collision": True},
}
WELD = {"road_asphalt", "road_concrete", "road_paving", "road_sett", "road_gravel", "collision_asphalt",
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
            g.append((pi, p.V, N, p.UV, p.T[sel]))
    out = {}
    for (key, layer, mat), items in sorted(groups.items()):
        V = np.concatenate([it[1][it[4]].reshape(-1, 3) for it in items])
        Nn = np.concatenate([it[2][it[4]].reshape(-1, 3) for it in items])
        UV = np.concatenate([it[3][it[4]].reshape(-1, 2) for it in items])
        if mat in WELD:
            q = np.round(V * 1000).astype(np.int64)
            u, inv = np.unique(q, axis=0, return_inverse=True)
            inv = inv.ravel()
            first = np.full(len(u), -1)
            first[inv[::-1]] = np.arange(len(inv))[::-1]
            Vw, UVw = V[first], UV[first]
            T = inv.reshape(-1, 3)
            T = T[(T[:, 0] != T[:, 1]) & (T[:, 1] != T[:, 2]) & (T[:, 0] != T[:, 2])]
            Nw = smooth_normals(Vw, T)
        else:
            ids = np.concatenate([np.full(it[4].size, it[0]) * 10_000_000 + it[4].ravel() for it in items])
            u, first, inv = np.unique(ids, return_index=True, return_inverse=True)
            Vw, Nw, UVw = V[first], Nn[first], UV[first]
            T = inv.ravel().reshape(-1, 3)
        out.setdefault(key, {}).setdefault(layer, []).append({"V": Vw, "N": Nw, "UV": UVw, "T": T, "mat": mat})
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
    q, z, t = lane_point(sj + 14)
    tgt = at(max(0.0, sj - 35))
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

    # terrain conform (uses ground road footprint) + bridge supports avoid ground roads
    road_z, mask = CF.rasterise([p for p in w.buf.parts if p.layer == "road"], w.hf)
    zc, dist = CF.conform(w.hf, road_z, mask)
    deck_parts = [p for p in w.buf.parts if p.layer == "bridge" and not p.src.endswith(":parapet")]
    for p in deck_parts:
        p.footprint = True
    deck, deck_mask = CF.rasterise(deck_parts, w.hf)
    for p in deck_parts:
        p.footprint = False
    zc = CF.clamp_under_decks(zc, deck, deck_mask, thick, mask)
    log(f"terrain conformed: footprint {int(mask.sum())} nodes")

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
    terrain = CH.build_chunks(zc, mask, e0, n0, w.region["bbox"]["width_m"])
    log("terrain chunks", len(terrain))
    roads = assemble(w.buf.parts, ("road", "bridge", "markings", "collision"), half)
    log("road chunks", len(roads))

    out_root = out_root or (REPO / "Data" / "raw" / "derived" / region_id / "world")
    out_root.mkdir(parents=True, exist_ok=True)
    chunks_meta = []
    for key in sorted(terrain):
        ci, cj = key
        glb = GLB(MATERIALS)
        tri = {}
        for li, prims in sorted(terrain[key].items()):
            glb.add_mesh(f"terrain_lod{li}", prims, {"lod": li, "spacing_m": CH.LODS[li]})
            tri[f"terrain_lod{li}"] = int(sum(len(p["T"]) for p in prims))
        layers = roads.get(key, {})
        for layer, node in (("road", "road"), ("bridge", "bridge"), ("markings", "markings"),
                            ("collision", "road_collision")):
            prims = layers.get(layer, [])
            if prims:
                glb.add_mesh(node, prims, {"layer": layer, "collision": layer == "collision"})
                tri[node] = int(sum(len(p["T"]) for p in prims))
        data = glb.bytes({"region": region_id, "chunk": [ci, cj], "axes": GLTF_AXES})
        fn = f"chunk_{ci}_{cj}.glb"
        (out_root / fn).write_bytes(data)
        allz = [p["V"][:, 2] for p in terrain[key][0]] + [p["V"][:, 2] for L in layers.values() for p in L]
        zz = np.concatenate(allz)
        chunks_meta.append({
            "id": f"{ci}_{cj}", "file": f"Data/raw/derived/{region_id}/world/{fn}", "bytes": len(data),
            "sha256": sha(data),
            "bounds_local_m": {"e_min": e0 + ci * CH.CHUNK_M, "e_max": e0 + (ci + 1) * CH.CHUNK_M,
                               "n_min": n0 - (cj + 1) * CH.CHUNK_M, "n_max": n0 - cj * CH.CHUNK_M,
                               "z_min_evrf2007": r(zz.min(), 2), "z_max_evrf2007": r(zz.max(), 2)},
            "triangles": tri,
            "materials": sorted({p["mat"] for L in layers.values() for p in L} | {"terrain_grass"}),
        })
    log("exported", len(chunks_meta), "GLB,", sum(c["bytes"] for c in chunks_meta) // 2**20, "MiB")
    preview_buildings(region_id, w, out_root / "preview_buildings.json")
    log("preview trees", preview_trees(region_id, w, zc, mask, out_root / "preview_trees.json"))

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
        "nodes": {"terrain_lod<k>": "terrain LODs (with skirts); grass material",
                  "road": "ground-level road surfaces: carriageways, junction patches, kerbs, sidewalks",
                  "bridge": "bridge decks, soffits, parapets, abutments, piers (low confidence)",
                  "markings": "horizontal markings decal mesh (lift %.3f m, use depth offset)" % S.MARKING_LIFT,
                  "road_collision": "simplified smooth collision mesh (4 m stations, no flanges); one primitive per surface"},
        "materials": MATERIALS, "chunks": chunks_meta, "sources_sha256": srcs,
        "overrides_applied": w.net.overrides_applied, "overrides_stale": w.net.overrides_stale,
    }
    write_json(gen / "world_manifest.json", manifest)
    qa = qa_report(w, mk_report, mask)
    write_json(gen / "roads_qa.json", qa)
    cams = cameras(region_id, w)
    write_json(gen / "control_cameras.json", {"schema": "truck-sim-pl/control-cameras/1", "region": region_id,
                                              "frame": "local E,N,U (U absolute EVRF2007)", "cameras": cams})
    np.save(out_root / "terrain_conformed.npy", zc.astype(np.float32))
    log("done")
    return w, manifest, qa


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
            "crossings_snapped": mk_report.get("crossings_snapped", 0),
            "crossings_skipped": mk_report.get("crossings_skipped", []),
            "bridges": w.bridges,
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
    a = ap.parse_args()
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
