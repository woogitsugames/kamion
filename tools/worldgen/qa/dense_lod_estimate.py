"""Dense-tile LOD budget estimate (ADR 0282, task D28): predicted triangles per control camera under LOD rules.

Usage (repo root, read-only on Data/Regions/*/generated):
    uv run --project tools/worldgen python tools/worldgen/qa/dense_lod_estimate.py               # table, 4 dense tiles
    uv run --project tools/worldgen python tools/worldgen/qa/dense_lod_estimate.py --buildings   # + generator probe
    uv run --project tools/worldgen python tools/worldgen/qa/dense_lod_estimate.py --json docs/reports/map/dense_lod_0282.json

Two camera models, both on the chunk triangle counts of `generated/world_manifest.json`:
  legacy   = build_world.mesh_budget (the `mesh_budget.frame_estimate` gate): every chunk/instance within 200 m in any
             direction, a 120 deg wedge to 1.6 km, terrain LOD0 = the full 1 m grid, furniture never culled on High,
             buildings LOD0 to 700 m. Re-implemented here for the chunk categories (test: identical to the stored
             frame_estimate); props and trees are taken from the stored estimate (instance files are in Data/raw).
  runtime  = what Unity selects (WorldSceneBuilder.k_HighLods + RegionImporter + SceneStats): the camera frustum
             (vfov from control_cameras.json, aspect 2340x1080 of the visual-QA runner, far clip 2500 m on High),
             one chunk LODGroup with switch distances (terrain_lods.suggested_switch_m + 0.7 chunk) x lodBias, the
             terrain band (fine 1 m grid only near roads, RegionImporter.TerrainBandM 15 m; fine fraction measured on
             C, WORKING_VALUE elsewhere), trees with treeCardLodScale 0.5 (LOD0 10 m, LOD1 30 m on High) and props /
             trees re-scaled from the legacy numbers (ESTIMATED, uniform density assumption).
Calibration: `artifacts/**/stats.txt` (visual-QA SceneStats, in git) of the same cameras - see `calibration()`.

Proposals (`PROPOSALS`) change per-layer distances (independent of the one chunk LOD switch); `merged_lod_table()`
turns a proposal into the LOD table (layers per level + switch distance) that one Unity LODGroup per chunk would need.
`building_probe()` runs the building generator (streetscape.buildings_mesh, flat ground) on a region's
buildings.geojson to measure the share of opening detail on LOD0 (-> LOD0b ratio) and builds the block HLOD rule
(`block_hlod_tris`) per chunk (-> HLOD / LOD1 ratio). Nothing here writes into Data/Regions or the generator output.
Every gain printed is ESTIMATED (CPU-side triangle count, not a GPU / phone measurement).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from dataclasses import dataclass, field, replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
REGIONS = REPO / "Data" / "Regions"
DENSE = ("bialystok-industrial-c", "bialystok-kleeberga", "bialystok-knyszynska", "bialystok-maczka")
BUDGET_HIGH_TRIS = 1_500_000      # docs/PERFORMANCE_BUDGETS.md "Budget: triangles in view" High (Ultra 2 M)
FUSE_HIGH_TRIS = 2_000_000        # frame_estimate fuse (docs/06 par. 6 hypothesis, budget-fix ADR 0221)
INF = 1e9

# --- legacy model (mirror of tools/worldgen/roads/build_world.py LOD_POLICY["High"] / mesh_budget) -------------------
LEGACY_HIGH = {"terrain": [[330, 0], [600, 1], [INF, 2]], "bld": 700, "forest_hlod_m": 120,
               "forest_hlod_cull_m": INF, "furn": INF, "far": 1600, "omni": 200, "wedge_cos": 0.5}

# --- runtime model (mirror of game/Assets/_Project/World/Import/WorldSceneBuilder.cs k_HighLods) ----------------------
HIGH_LODS = (
    ("terrain_band", "road", "bridge", "markings", "paved", "buildings", "furniture", "wires", "plot_ground", "plots",
     "water", "banks"),
    ("terrain_lod1", "road", "bridge", "markings", "paved", "buildings_lod1", "furniture", "wires", "plot_ground",
     "plots", "water", "banks"),
    ("terrain_lod2", "road", "bridge", "paved", "buildings_lod1", "wires", "water"),
    ("terrain_lod3", "bridge", "buildings_lod1", "water"),
)
NODE_CATEGORY = {"terrain_band": "terrain", "terrain_lod1": "terrain", "terrain_lod2": "terrain",
                 "terrain_lod3": "terrain", "road": "roads", "bridge": "roads", "markings": "roads", "paved": "roads",
                 "buildings": "buildings", "buildings_lod1": "buildings", "furniture": "furniture",
                 "wires": "furniture", "plot_ground": "furniture", "plots": "furniture", "water": "water",
                 "banks": "water"}
CHUNK_CATEGORIES = ("terrain", "roads", "furniture", "buildings", "water", "forest_hlod")
QA_ASPECT = 2340 / 1080            # VisualQaRunner default -qaWidth/-qaHeight
TREE_ENDS = (20.0, 60.0, 1000.0)   # InstanceImporter.Policy tree_ (m, x lodScale)


@dataclass(frozen=True)
class Runtime:
    """High tier as Unity selects it (QualityProfile.asset High; RegionImporter constants)."""
    lod_bias: float = 1.5
    far_clip: float = 2500.0
    aspect: float = QA_ASPECT
    band_fine: float = 0.407          # terrain_band_fine_fraction High, C import (artifacts/asphalt-r2/*-import.json)
    tree_card_scale: float = 0.5      # treeCardLodScale High
    hlod_m: float = 120.0             # forestHlodM High


@dataclass(frozen=True)
class Proposal:
    """Per-layer distance rules on top of the chunk LOD (m from the camera to the chunk reference point).
    None = unchanged. Ratios multiply the triangles of the layer in that distance band (ESTIMATED / measured
    by building_probe)."""
    name: str
    note: str = ""
    bld_lod0_m: float | None = None           # LOD0 buildings -> LOD1 prism beyond this
    bld_lod0b: tuple[float, float] | None = None   # (from m, ratio): LOD0 without opening detail ("LOD0b")
    bld_hlod: tuple[float, float] | None = None    # (from m, ratio): LOD1 -> block HLOD
    plots_cull_m: float | None = None         # plots + plot_ground
    furn_cull_m: float | None = None          # furniture (fences, posts, guard rails)
    markings_cull_m: float | None = None
    props_scale: float = 1.0                  # instanced props (lamps, signs, cars ...) - far-ring thinning
    tree_scale: float = 1.0
    terrain_band_fine: float | None = None    # runtime only: narrower band on dense tiles
    terrain_lod0_m: float | None = None       # 1 m terrain (legacy grid / runtime band) -> 2 m grid beyond this
    extra: dict = field(default_factory=dict)


BASE = Proposal("base", "stan obecny")
# Ratios measured by building_probe() on the 4 dense tiles (2026-11-16): LOD0b = LOD0 without reveals / sills / frames /
# downpipes 0.56-0.60 (max 0.60 used); flat block HLOD / LOD1 0.11-0.14 -> 0.30 WORKING_VALUE (keeps pitched roofs).
PROPOSALS = (
    BASE,
    Proposal("P1_bld_lod0_250", "LOD0 budynków do 250 m (LOD1 dalej)", bld_lod0_m=250),
    Proposal("P2_bld_lod0b_120", "LOD0b (otwory płaskie, bez rur/parapetów) od 120 m", bld_lod0b=(120, 0.60)),
    Proposal("P3_block_hlod_900", "HLOD kwartałów zamiast LOD1 od 900 m", bld_hlod=(900, 0.30)),
    Proposal("P4_plots_300", "działki (płoty, ogrody) do 300 m", plots_cull_m=300),
    Proposal("P5_furn_450_mark_450", "meble drogowe i oznakowanie poziome do 450 m", furn_cull_m=450,
             markings_cull_m=450),
    Proposal("P6_props_trees_far", "propsy -15 %, drzewa -10 % (dalekie pierścienie)", props_scale=0.85,
             tree_scale=0.9),
    Proposal("P7_terrain_lod0_250", "teren 1 m (pas) do 250 m, dalej siatka 2 m", terrain_lod0_m=250),
)


def combined(*ps: Proposal, name: str = "ALL") -> Proposal:
    out = replace(BASE, name=name, note="+".join(p.name for p in ps))
    for p in ps:
        for k in ("bld_lod0_m", "bld_lod0b", "bld_hlod", "plots_cull_m", "furn_cull_m", "markings_cull_m",
                  "terrain_band_fine", "terrain_lod0_m"):
            if getattr(p, k) is not None:
                out = replace(out, **{k: getattr(p, k)})
        out = replace(out, props_scale=out.props_scale * p.props_scale, tree_scale=out.tree_scale * p.tree_scale)
    return out


# ---------------------------------------------------------------------------------------------------- data access
def load_region(region: str) -> dict:
    gen = REGIONS / region / "generated"
    man = json.loads((gen / "world_manifest.json").read_text(encoding="utf-8"))
    cams = json.loads((gen / "control_cameras.json").read_text(encoding="utf-8"))["cameras"]
    qa = json.loads((gen / "streetscape_qa.json").read_text(encoding="utf-8"))["mesh_budget"]
    fe = {f["camera"]: f for f in qa["frame_estimate"]}
    return {"id": region, "manifest": man, "cameras": [c for c in cams if c["type"] == "persp" and c["id"] in fe],
            "frame_estimate": fe}


def _center(ch):
    b = ch["bounds_local_m"]
    return (b["e_min"] + b["e_max"]) / 2, (b["n_min"] + b["n_max"]) / 2


def _bbox_dist(b, p):
    dx = max(b[0] - p[0], 0.0, p[0] - b[2])
    dy = max(b[1] - p[1], 0.0, p[1] - b[3])
    return math.hypot(dx, dy)


def _look(cam):
    lx, ly = cam["look_at"][0] - cam["pos"][0], cam["look_at"][1] - cam["pos"][1]
    n = max(math.hypot(lx, ly), 1e-9)
    return lx / n, ly / n


# ---------------------------------------------------------------------------------------------------- legacy model
def legacy_chunk_categories(manifest: dict, cam: dict, prop: Proposal = BASE) -> dict:
    """build_world.mesh_budget, High, chunk part only (plus the proposal's per-layer rules)."""
    pol = LEGACY_HIGH
    px, py = cam["pos"][0], cam["pos"][1]
    lx, ly = _look(cam)
    cat = dict.fromkeys(CHUNK_CATEGORIES, 0)
    for ch in manifest["chunks"]:
        cx, cy = _center(ch)
        d = math.hypot(cx - px, cy - py)
        if d > pol["far"] or (d > pol["omni"] and ((cx - px) * lx + (cy - py) * ly) / d < pol["wedge_cos"]):
            continue
        t = ch["triangles"]
        lod = next(l for lim, l in pol["terrain"] if d < lim)
        if lod == 0 and prop.terrain_lod0_m is not None and d >= prop.terrain_lod0_m:
            lod = 1
        cat["terrain"] += t.get(f"terrain_lod{lod}", 0)
        mk = t.get("markings", 0) if prop.markings_cull_m is None or d < prop.markings_cull_m else 0
        cat["roads"] += t.get("road", 0) + t.get("bridge", 0) + t.get("paved", 0) + mk
        if t.get("water"):
            cat["water"] += t["water"]
        if t.get("banks"):
            cat["water"] += t["banks"] if d < 500 else 0
        if d < pol["furn"]:
            fu = t.get("furniture", 0) if prop.furn_cull_m is None or d < prop.furn_cull_m else 0
            pl = t.get("plots", 0) if prop.plots_cull_m is None or d < prop.plots_cull_m else 0
            cat["furniture"] += fu + pl + t.get("wires", 0)
        cat["buildings"] += _buildings({**t, "_id": ch["id"]}, d, pol["bld"], prop, fallback=False)
        for fc in ch.get("forest_cells", []):
            dfc = _bbox_dist(fc["bbox_local_m"], (px, py))
            if pol["forest_hlod_m"] < dfc < pol["forest_hlod_cull_m"]:
                cat["forest_hlod"] += fc["tris"]
    return cat


def _buildings(t: dict, d: float, lod0_end: float, prop: Proposal, fallback: bool = True) -> float:
    """Building triangles of one chunk at distance d: LOD0 / LOD0b / LOD1 / block HLOD. fallback: a chunk without LOD0
    buildings shows the LOD1 prisms on LOD0 (WorldSceneBuilder); the legacy estimate counts 0 there."""
    end = lod0_end if prop.bld_lod0_m is None else min(lod0_end, prop.bld_lod0_m)
    if d < end:
        n = t.get("buildings", 0) or (t.get("buildings_lod1", 0) if fallback else 0)
        if prop.bld_lod0b and d >= prop.bld_lod0b[0] and t.get("buildings"):
            n *= prop.bld_lod0b[1]
        return n
    n = t.get("buildings_lod1", 0)
    if prop.bld_hlod and d >= prop.bld_hlod[0]:
        n *= _hlod_ratio(prop, t)
    return n


def _hlod_ratio(prop: Proposal, t: dict) -> float:
    per_chunk = prop.extra.get("hlod_ratio_by_chunk")
    if per_chunk and t.get("_id") in per_chunk:
        return per_chunk[t["_id"]]
    return prop.bld_hlod[1]


# --------------------------------------------------------------------------------------------------- runtime model
def hfov_deg(vfov_deg: float, aspect: float) -> float:
    return math.degrees(2 * math.atan(math.tan(math.radians(vfov_deg) / 2) * aspect))


def lod_ends(switch_m, chunk_size: float, lod_bias: float, vfov_deg: float) -> list[float]:
    """Distances (camera -> chunk reference point) where the chunk LODGroup leaves LOD 0..n-2 (WorldSceneBuilder:
    h = size / (2 (switch + 0.7 size) tan 30); SceneStats / Unity: h_cam = size / (2 d tan(fov/2)) x lodBias)."""
    k = lod_bias * math.tan(math.radians(30)) / math.tan(math.radians(vfov_deg) / 2)
    return [(s + 0.7 * chunk_size) * k for s in switch_m[1:]]


def chunk_in_frustum(bounds, cam, hfov: float, far: float) -> bool:
    """2D frustum (horizontal fov wedge, far clip) against the chunk rectangle: corners, edges and the two side rays."""
    px, py = cam["pos"][0], cam["pos"][1]
    e0, e1, n0, n1 = bounds["e_min"], bounds["e_max"], bounds["n_min"], bounds["n_max"]
    if e0 <= px <= e1 and n0 <= py <= n1:
        return True
    lx, ly = _look(cam)
    half = math.radians(hfov) / 2
    cos_h = math.cos(half)

    def inside(x, y):
        dx, dy = x - px, y - py
        d = math.hypot(dx, dy)
        return d <= far and (d < 1e-6 or (dx * lx + dy * ly) / d >= cos_h)
    steps = 16
    for i in range(steps + 1):
        f = i / steps
        for x, y in ((e0 + f * (e1 - e0), n0), (e0 + f * (e1 - e0), n1), (e0, n0 + f * (n1 - n0)),
                     (e1, n0 + f * (n1 - n0))):
            if inside(x, y):
                return True
    for s in (-half, half):              # a side ray crossing the rectangle with no boundary sample inside
        rx, ry = lx * math.cos(s) - ly * math.sin(s), lx * math.sin(s) + ly * math.cos(s)
        r = 0.0
        while r <= far:
            x, y = px + rx * r, py + ry * r
            if e0 <= x <= e1 and n0 <= y <= n1:
                return True
            r += 8.0
    return False


def runtime_layers(d: float, ends: list[float]) -> tuple[int, tuple[str, ...]]:
    lod = next((i for i, e in enumerate(ends) if d < e), len(ends))
    return lod, HIGH_LODS[lod]


def runtime_chunk_categories(manifest: dict, cam: dict, rt: Runtime = Runtime(), prop: Proposal = BASE) -> dict:
    vfov = cam.get("fov_deg", 60.0)
    hf = hfov_deg(vfov, rt.aspect)
    size = manifest["chunk_size_m"]
    ends = lod_ends([l["suggested_switch_m"] for l in manifest["terrain_lods"]], size, rt.lod_bias, vfov)
    fine = rt.band_fine if prop.terrain_band_fine is None else prop.terrain_band_fine
    px, py, ph = cam["pos"]
    cat = dict.fromkeys(CHUNK_CATEGORIES, 0)
    for ch in manifest["chunks"]:
        b = ch["bounds_local_m"]
        if not chunk_in_frustum(b, cam, hf, rt.far_clip):
            continue
        cx, cy = _center(ch)
        cz = (b.get("z_min_evrf2007", ph) + b.get("z_max_evrf2007", ph)) / 2
        d = math.sqrt((cx - px) ** 2 + (cy - py) ** 2 + (cz - ph) ** 2)
        t = {**ch["triangles"], "_id": ch["id"]}
        lod, layers = runtime_layers(d, ends)
        for node in layers:
            c = NODE_CATEGORY[node]
            if node == "terrain_band" and prop.terrain_lod0_m is not None and d >= prop.terrain_lod0_m:
                n = t.get("terrain_lod1", 0)
            elif node == "terrain_band":
                n = t.get("terrain_lod0", 0) * (fine + (1 - fine) / 4)    # coarse blocks: 2 m step = 1/4
            elif node in ("buildings", "buildings_lod1"):
                continue
            elif node == "markings" and prop.markings_cull_m is not None and d >= prop.markings_cull_m:
                n = 0
            elif node == "furniture" and prop.furn_cull_m is not None and d >= prop.furn_cull_m:
                n = 0
            elif node in ("plots", "plot_ground") and prop.plots_cull_m is not None and d >= prop.plots_cull_m:
                n = 0
            else:
                n = t.get(node, 0)
            cat[c] += n
        lod0_end = ends[0] if "buildings" in layers else 0.0
        cat["buildings"] += _buildings(t, d, lod0_end, prop)
        for fc in ch.get("forest_cells", []):
            if _bbox_dist(fc["bbox_local_m"], (px, py)) > rt.hlod_m:
                cat["forest_hlod"] += fc["tris"]
    return cat


def far_field_tris(manifest: dict, cam: dict, rt: Runtime = Runtime()) -> int:
    """Far-field backdrop (ADR 0085) and skyline ring (ADR 0141) of the High manifest entry: a sector counts whole when
    its direction lies within hfov/2 + 45 deg of the view (SceneStats counts whole renderers)."""
    ff = (manifest.get("far_field") or {}).get("High")
    if not ff:
        return 0
    hf = hfov_deg(cam.get("fov_deg", 60.0), rt.aspect)
    lx, ly = _look(cam)
    dirs = {"far_east": (1, 0), "far_west": (-1, 0), "far_north": (0, 1), "far_south": (0, -1)}
    n = (ff.get("skyline") or {}).get("triangles", 0)
    for k, s in (ff.get("sectors") or {}).items():
        v = dirs.get(k)
        if v and math.degrees(math.acos(max(-1.0, min(1.0, v[0] * lx + v[1] * ly)))) <= hf / 2 + 45:
            n += s["triangles"]
    return n


def tree_means() -> dict:
    p = REPO / "art-source" / "world" / "vegetation" / "trees_meta.json"
    trees = json.loads(p.read_text(encoding="utf-8"))["trees"]
    return {k: statistics.mean(t.get(k, 0) for t in trees.values()) for k in ("tris_lod0", "tris_lod1", "tris_lod2")}


def runtime_instances(by_cat: dict, cam: dict, rt: Runtime = Runtime(), prop: Proposal = BASE,
                      means: dict | None = None) -> dict:
    """Props / trees re-scaled from the legacy estimate (ESTIMATED). Legacy trees: LOD0 < 35 m, LOD1 35-80 m in every
    direction; runtime High: LOD0 < 20 x 0.5 = 10 m, LOD1 < 60 x 0.5 = 30 m, frustum share hfov/360, uniform density
    of the 0-35 m disc. Props: legacy counts the 200 m disc in every direction -> frustum share hfov/360 (lower bound:
    lamps / gantries beyond 200 m are not scaled up)."""
    m = means or tree_means()
    f = hfov_deg(cam.get("fov_deg", 60.0), rt.aspect) / 360.0
    n0 = by_cat.get("trees_lod0", 0) / max(m["tris_lod0"], 1e-9)
    rho = n0 / (math.pi * 35.0 ** 2)
    e0, e1 = TREE_ENDS[0] * rt.tree_card_scale, TREE_ENDS[1] * rt.tree_card_scale
    trees = f * rho * math.pi * (e0 ** 2 * m["tris_lod0"] + (e1 ** 2 - e0 ** 2) * m["tris_lod1"])
    trees += by_cat.get("trees_lod2", 0)
    return {"trees": trees * prop.tree_scale, "props": by_cat.get("props", 0) * f * prop.props_scale}


# ---------------------------------------------------------------------------------------------------- camera totals
def camera_estimate(reg: dict, cam: dict, prop: Proposal = BASE, rt: Runtime = Runtime(), means=None) -> dict:
    fe = reg["frame_estimate"][cam["id"]]["by_category_high"]
    leg = legacy_chunk_categories(reg["manifest"], cam, prop)
    leg_inst = {"props": fe.get("props", 0) * prop.props_scale,
                "trees": sum(v for k, v in fe.items() if k.startswith("trees_")) * prop.tree_scale}
    run = runtime_chunk_categories(reg["manifest"], cam, rt, prop)
    run_inst = runtime_instances(fe, cam, rt, prop, means)
    ff = far_field_tris(reg["manifest"], cam, rt)
    return {"camera": cam["id"],
            "legacy": {**{k: round(v) for k, v in leg.items()}, **{k: round(v) for k, v in leg_inst.items()},
                       "total": round(sum(leg.values()) + sum(leg_inst.values())),
                       # P0 (estimator fix, not a content change): trees by the runtime tier policy, legacy elsewhere
                       "total_trees_runtime": round(sum(leg.values()) + leg_inst["props"] + run_inst["trees"])},
            "runtime": {**{k: round(v) for k, v in run.items()}, **{k: round(v) for k, v in run_inst.items()},
                        "far_field": ff, "total": round(sum(run.values()) + sum(run_inst.values()) + ff)}}


def region_table(region: str, proposals=PROPOSALS, rt: Runtime = Runtime()) -> dict:
    reg = load_region(region)
    means = tree_means()
    out = {"region": region, "cameras": len(reg["cameras"]), "proposals": {}}
    for p in proposals:
        rows = [camera_estimate(reg, c, p, rt, means) for c in reg["cameras"]]
        worst_l = max(rows, key=lambda r: r["legacy"]["total"])
        worst_r = max(rows, key=lambda r: r["runtime"]["total"])
        out["proposals"][p.name] = {
            "legacy_max": worst_l["legacy"]["total"], "legacy_max_camera": worst_l["camera"],
            "legacy_median": round(statistics.median(r["legacy"]["total"] for r in rows)),
            "legacy_trees_runtime_max": max(r["legacy"]["total_trees_runtime"] for r in rows),
            "runtime_max": worst_r["runtime"]["total"], "runtime_max_camera": worst_r["camera"],
            "runtime_median": round(statistics.median(r["runtime"]["total"] for r in rows)),
            "legacy_worst_categories": worst_l["legacy"], "runtime_worst_categories": worst_r["runtime"]}
    return out


# --------------------------------------------------------------------------------------- proposal -> one LOD table
def layer_ends(ends: list[float], prop: Proposal) -> dict:
    """Per-layer visibility as [(end m, variant)] for one chunk: the chunk LOD table + the proposal's distances."""
    out = {}
    for lod, layers in enumerate(HIGH_LODS):
        lo = 0.0 if lod == 0 else ends[lod - 1]
        hi = ends[lod] if lod < len(ends) else INF
        for node in layers:
            out.setdefault(node, []).append((lo, hi))
    cuts = {"markings": prop.markings_cull_m, "furniture": prop.furn_cull_m, "plots": prop.plots_cull_m,
            "plot_ground": prop.plots_cull_m}
    res = {}
    for node, spans in out.items():
        lo, hi = min(s[0] for s in spans), max(s[1] for s in spans)
        c = cuts.get(node)
        res[node] = (lo, min(hi, c) if c is not None else hi)
    if prop.terrain_lod0_m is not None and prop.terrain_lod0_m < res["terrain_band"][1]:
        t0 = prop.terrain_lod0_m
        res["terrain_lod1"] = (t0, res["terrain_lod1"][1])
        res["terrain_band"] = (0.0, t0)
    b0 = res.pop("buildings")[1]
    if prop.bld_lod0_m is not None:
        b0 = min(b0, prop.bld_lod0_m)
    bands = []
    if prop.bld_lod0b and prop.bld_lod0b[0] < b0:
        bands += [(0.0, prop.bld_lod0b[0], "buildings"), (prop.bld_lod0b[0], b0, "buildings_lod0b")]
    else:
        bands.append((0.0, b0, "buildings"))
    res.pop("buildings_lod1")
    if prop.bld_hlod and prop.bld_hlod[0] > b0:
        bands += [(b0, prop.bld_hlod[0], "buildings_lod1"), (prop.bld_hlod[0], INF, "buildings_hlod")]
    else:
        bands.append((b0, INF, "buildings_lod1"))
    for lo, hi, node in bands:
        res[node] = (lo, hi)
    return res


def merged_lod_table(ends: list[float], prop: Proposal) -> list[tuple[float, tuple[str, ...]]]:
    """One LODGroup per chunk: every distinct layer end becomes a LOD level. Returns [(end m, layers)], last end INF.
    This is the table WorldSceneBuilder would need (switch distance -> screen height as today)."""
    spans = layer_ends(ends, prop)
    cuts = sorted({hi for _, hi in spans.values() if hi < INF} | {lo for lo, _ in spans.values() if lo > 0})
    bounds = [0.0] + cuts + [INF]
    table = []
    for lo, hi in zip(bounds[:-1], bounds[1:]):
        mid = (lo + min(hi, lo * 2 + 1)) / 2 if hi == INF else (lo + hi) / 2
        layers = tuple(sorted(n for n, (a, b) in spans.items() if a <= mid < b))
        if table and table[-1][1] == layers:
            table[-1] = (hi, layers)
        else:
            table.append((hi, layers))
    return table


# ------------------------------------------------------------------------------------------- building probe (gen)
OPENING_DETAIL_MATS = ("reveal_plaster", "reveal_hall", "window_sill", "window_frame")
PIPE_MATS = ("downpipe",)


def block_hlod_tris(polys_heights, bin_m: float = 3.0, gap_m: float = 0.5, tol_m: float = 1.0) -> int:
    """Block HLOD rule (prototype, not wired into the generator): footprints grouped by height bin (round to bin_m),
    touching / closer than gap_m merged, outline simplified by tol_m, flat-roof prism (walls 2 tris per edge, roof
    n - 2 + 2 x holes). Returns triangles. Keeps the skyline steps between height classes (anti-slop: no blobs)."""
    import shapely
    from shapely.geometry import Polygon
    groups = {}
    for poly, h in polys_heights:
        groups.setdefault(round(h / bin_m), []).append(poly)
    n = 0
    for _, ps in sorted(groups.items()):
        u = shapely.union_all([p.buffer(gap_m / 2, join_style=2) for p in ps]).buffer(-gap_m / 2, join_style=2)
        u = u.simplify(tol_m, preserve_topology=True)
        for g in getattr(u, "geoms", [u]):
            if not isinstance(g, Polygon) or g.is_empty or g.area < 1.0:
                continue
            rings = [g.exterior, *g.interiors]
            edges = sum(len(r.coords) - 1 for r in rings)
            n += 2 * edges + (edges - 2 + 2 * len(g.interiors))
    return n


def building_probe(region: str, limit: int | None = None) -> dict:
    """Runs streetscape.buildings_mesh on the region's buildings.geojson (flat ground at 100 m, region overrides):
    LOD0 / LOD1 triangles per typology and material class, plus block HLOD triangles per chunk."""
    import sys
    from types import SimpleNamespace

    import numpy as np
    import yaml
    from shapely.geometry import box
    sys.path.insert(0, str(REPO / "tools" / "worldgen"))
    from streetscape import buildings_mesh as BM

    rdir = REGIONS / region
    meta = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
    origin = (meta["origin"]["x"], meta["origin"]["y"])
    fc = json.loads((rdir / "buildings.geojson").read_text(encoding="utf-8"))
    ovr = (yaml.safe_load((rdir / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides", []) \
        if (rdir / "overrides.yaml").exists() else []
    if limit:
        fc = {"features": fc["features"][:limit]}
    blds = BM.load(fc, origin, ovr)

    class Buf:
        def __init__(self):
            self.parts = []

        def add(self, layer, mat, V, UV, T, **kw):
            self.parts.append((layer, mat, int(np.asarray(T).size // 3)))
    hf = SimpleNamespace(sample=lambda x, y: np.full(np.shape(x), 100.0))
    far = box(-1e5, -1e5, -1e5 + 10, -1e5 + 10)
    by_typ, errors = {}, 0
    for b in blds:
        buf = Buf()
        try:
            BM.build(buf, [b], hf, None, None, far, {}, sign_out=[])
        except Exception:   # noqa: BLE001 - a footprint the generator rejects in isolation is counted, not fatal
            errors += 1
            continue
        d = by_typ.setdefault(b["typ"], {"n": 0, "lod0": 0, "lod1": 0, "opening_detail": 0, "pipes": 0})
        d["n"] += 1
        for layer, mat, n in buf.parts:
            if layer == "buildings":
                d["lod0"] += n
                d["opening_detail"] += n if mat in OPENING_DETAIL_MATS else 0
                d["pipes"] += n if mat in PIPE_MATS else 0
            elif layer == "buildings_low":
                d["lod1"] += n
    lod0 = sum(d["lod0"] for d in by_typ.values())
    det = sum(d["opening_detail"] for d in by_typ.values())
    pipes = sum(d["pipes"] for d in by_typ.values())
    lod1 = sum(d["lod1"] for d in by_typ.values())
    # block HLOD per chunk (chunk = manifest bounds containing the footprint centroid)
    man = json.loads((rdir / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
    per = {}
    for b in blds:
        if b["typ"] == "roof" or b["ovr"].get("hero_asset"):
            continue
        c = b["poly"].centroid
        for ch in man["chunks"]:
            bb = ch["bounds_local_m"]
            if bb["e_min"] <= c.x < bb["e_max"] and bb["n_min"] <= c.y < bb["n_max"]:
                per.setdefault(ch["id"], []).append((b["poly"], float(b["props"].get("height_m") or 6.0)))
                break
    hlod = {}
    for ch in man["chunks"]:
        l1 = ch["triangles"].get("buildings_lod1", 0)
        if ch["id"] in per and l1:
            hlod[ch["id"]] = round(min(1.0, block_hlod_tris(per[ch["id"]]) / l1), 3)
    hl_tris = sum(block_hlod_tris(v) for v in per.values())
    l1_man = sum(ch["triangles"].get("buildings_lod1", 0) for ch in man["chunks"] if ch["id"] in per)
    return {"region": region, "buildings": len(blds), "errors": errors, "by_typology": by_typ,
            "lod0": lod0, "lod1": lod1, "opening_detail_share": round(det / max(lod0, 1), 3),
            "pipes_share": round(pipes / max(lod0, 1), 3),
            "lod0b_ratio_min": round(1 - det / max(lod0, 1), 3),
            "lod0b_ratio": round(1 - (det + pipes) / max(lod0, 1), 3),
            "hlod_tris": hl_tris, "lod1_manifest_tris": l1_man, "hlod_ratio": round(hl_tris / max(l1_man, 1), 3),
            "hlod_ratio_by_chunk": hlod}


# ---------------------------------------------------------------------------------------------------- calibration
STATS = {  # visual-QA SceneStats in git, same control cameras as the frame_estimate (High); render size of that run
    "bialystok-kleeberga": ("artifacts/bialystok-dk65-t2-0206/vqa-r4/High-overcast/stats.txt", 1920 / 1080),  # vqa.ps1
    "bialystok-industrial-c": ("artifacts/dusk-cal-0199/final/High-dusk/stats.txt", 2340 / 1080),  # run.ps1 default
}
_RX = re.compile(r"^([a-z0-9-]+): objects=\d+ drawsEst=(\d+) shadowDrawsEst=\d+ trisK=\d+ trisExact=(\d+)", re.M)
_RXI = re.compile(r"^\s+([a-z0-9-]+) instanced \(props\+trees\): draws (\d+), .*trianglesExact (\d+)", re.M)


def parse_stats(text: str) -> dict:
    out = {m.group(1): {"draws": int(m.group(2)), "mesh": int(m.group(3)), "inst": 0} for m in _RX.finditer(text)}
    for m in _RXI.finditer(text):
        if m.group(1) in out:
            out[m.group(1)]["inst"] = int(m.group(3))
            out[m.group(1)]["inst_draws"] = int(m.group(2))
    return out


def calibration(region: str, stats_path: str, aspect: float = QA_ASPECT, rt: Runtime | None = None) -> list[dict]:
    rt = rt or Runtime(aspect=aspect)
    reg = load_region(region)
    st = parse_stats((REPO / stats_path).read_text(encoding="utf-8"))
    means = tree_means()
    rows = []
    for cam in reg["cameras"]:
        u = st.get(cam["id"].replace("_", "-"))
        if not u:
            continue
        e = camera_estimate(reg, cam, BASE, rt, means)
        unity = u["mesh"] + u["inst"]
        rows.append({"camera": cam["id"], "unity": unity, "unity_mesh": u["mesh"], "draws": u["draws"],
                     "legacy": e["legacy"]["total"], "runtime": e["runtime"]["total"],
                     "runtime_mesh": e["runtime"]["total"] - round(e["runtime"]["props"] + e["runtime"]["trees"])})
    return rows


# ---------------------------------------------------------------------------------------------------------- CLI
def _fmt(n):
    return f"{n / 1e6:.2f} M"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--regions", nargs="*", default=list(DENSE))
    ap.add_argument("--buildings", action="store_true", help="run the building generator probe (slow, ~1 min/tile)")
    ap.add_argument("--json", type=Path, help="write the full result (deterministic, sorted keys)")
    a = ap.parse_args(argv)
    result = {"adr": "0282", "status": "ESTIMATED (CPU-side triangle counts, not GPU / phone measurements)",
              "budget_high_tris": BUDGET_HIGH_TRIS, "fuse_high_tris": FUSE_HIGH_TRIS, "runtime": Runtime().__dict__,
              "calibration": {}, "probe": {}, "regions": {}}
    for r, (p, asp) in STATS.items():
        rows = calibration(r, p, asp)
        result["calibration"][r] = {"stats": p, "aspect": round(asp, 4), "rows": rows,
                                    "unity_over_legacy_median": round(statistics.median(x["unity"] / x["legacy"] for x in rows), 3),
                                    "unity_over_runtime_median": round(statistics.median(x["unity"] / x["runtime"] for x in rows), 3)}
        print(f"calibration {r}: unity/legacy {result['calibration'][r]['unity_over_legacy_median']}, "
              f"unity/runtime {result['calibration'][r]['unity_over_runtime_median']} ({len(rows)} cameras)")
    props = list(PROPOSALS)
    if a.buildings:
        for r in a.regions:
            pr = building_probe(r)
            result["probe"][r] = {k: v for k, v in pr.items() if k != "hlod_ratio_by_chunk"}
            print(f"probe {r}: LOD0 {pr['lod0']} LOD1 {pr['lod1']} opening detail {pr['opening_detail_share']} "
                  f"pipes {pr['pipes_share']} -> LOD0b {pr['lod0b_ratio']} (min {pr['lod0b_ratio_min']}), "
                  f"HLOD/LOD1 {pr['hlod_ratio']}")
        ratios = [result["probe"][r]["lod0b_ratio"] for r in a.regions]
        hl = [result["probe"][r]["hlod_ratio"] for r in a.regions]
        props = [replace(p, bld_lod0b=(120, round(max(ratios), 2))) if p.bld_lod0b else p for p in props]
        print(f"LOD0b ratio from the probe: {max(ratios):.3f}; flat block HLOD / LOD1 {min(hl):.3f}-{max(hl):.3f} "
              f"(P3 keeps {PROPOSALS[3].bld_hlod[1]} WORKING_VALUE for pitched roofs)")
    props.append(combined(*props[1:], name="ALL"))
    for r in a.regions:
        t = region_table(r, props)
        result["regions"][r] = t
        b = t["proposals"]["base"]
        print(f"\n{r} ({t['cameras']} cameras)  base legacy max {_fmt(b['legacy_max'])} ({b['legacy_max_camera']}), "
              f"runtime max {_fmt(b['runtime_max'])} ({b['runtime_max_camera']})")
        for name, v in t["proposals"].items():
            print(f"  {name:24s} legacy max {_fmt(v['legacy_max'])} (-{(b['legacy_max'] - v['legacy_max']) / 1e3:6.0f} k)"
                  f"  +P0 {_fmt(v['legacy_trees_runtime_max'])}"
                  f"  runtime max {_fmt(v['runtime_max'])} (-{(b['runtime_max'] - v['runtime_max']) / 1e3:6.0f} k)")
    if a.json:
        a.json.write_text(json.dumps(result, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8",
                          newline="\n")
        print("json", a.json)


if __name__ == "__main__":
    main()
