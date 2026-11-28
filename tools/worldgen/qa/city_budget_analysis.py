"""City-tile triangle budget analysis for wave 14 (task codex-city-budget-s25).

Reads generated QA JSONs and manifests directly from git (default ref: `regen-wave-14-s25`)
without touching `Data/Regions/*/generated` or `Data/raw/derived`.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
TREES_META_PATH = REPO / "art-source" / "world" / "vegetation" / "trees_meta.json"

CHUNK_M = 256.0
MARGIN_M = 0.7 * CHUNK_M
INF = 1e9

# Mirror of tools/worldgen/roads/build_world.py LOD_POLICY
LEGACY_POLICY = {
    "High": {
        "terrain": [(330.0, 0), (600.0, 1), (INF, 2)],
        "bld": 700.0,
        "forest_hlod_m": 120.0,
        "forest_hlod_cull_m": INF,
        "furn": INF,
    },
    "Low": {
        "terrain": [(330.0, 1), (600.0, 2), (INF, 3)],
        "bld": 0.0,
        "forest_hlod_m": 70.0,
        "forest_hlod_cull_m": 1000.0,
        "furn": 400.0,
    },
}

# Mirror of game/Assets/_Project/World/Import/WorldSceneBuilder.cs
HIGH_LODS = (
    ("terrain_band", "road", "bridge", "markings", "paved", "buildings", "furniture", "wires", "plot_ground", "plots", "water", "banks"),
    ("terrain_lod1", "road", "bridge", "markings", "paved", "buildings_lod1", "furniture", "wires", "plot_ground", "plots", "water", "banks"),
    ("terrain_lod2", "road", "bridge", "paved", "buildings_lod1", "wires", "water"),
    ("terrain_lod3", "bridge", "buildings_lod1", "water"),
)
LOW_LODS = (
    ("terrain_band", "road", "bridge", "markings", "paved", "buildings", "furniture", "wires", "plot_ground", "plots_low", "water", "banks_low"),
    ("terrain_lod2", "road", "bridge", "markings", "paved", "buildings_lod1", "furniture", "wires", "plot_ground", "plots_low", "water", "banks_low"),
    ("terrain_lod2", "road", "bridge", "paved", "buildings_lod1", "wires", "water"),
    ("terrain_lod3", "bridge", "buildings_lod1", "water"),
)

NODE_CATEGORY = {
    "terrain_band": "terrain",
    "terrain_lod1": "terrain",
    "terrain_lod2": "terrain",
    "terrain_lod3": "terrain",
    "road": "roads",
    "bridge": "roads",
    "markings": "roads",
    "paved": "roads",
    "buildings": "buildings",
    "buildings_lod1": "buildings",
    "furniture": "furniture",
    "wires": "furniture",
    "plot_ground": "furniture",
    "plots": "furniture",
    "plots_low": "furniture",
    "water": "water",
    "banks": "water",
    "banks_low": "water",
}


@dataclass(frozen=True)
class RuntimeProfile:
    name: str
    tier: str  # "High" or "Low"
    lod_bias: float
    far_clip: float
    aspect: float
    band_fine: float
    tree_card_scale: float
    tree_ends_base: tuple[float, float, float]
    tree_cull_cap: float
    hlod_m: float
    hlod_cull_m: float
    high_only_trees: bool
    low_prop_cull_factor: float  # approximate WorldPropTierPolicy reduction on PC Low


PROFILES = {
    "vqa_high": RuntimeProfile(
        name="VQA/Editor High (QualityProfile)",
        tier="High",
        lod_bias=1.5,
        far_clip=2500.0,
        aspect=1920 / 1080,
        band_fine=0.407,
        tree_card_scale=0.5,
        tree_ends_base=(20.0, 60.0, 1000.0),
        tree_cull_cap=600.0,
        hlod_m=120.0,
        hlod_cull_m=INF,
        high_only_trees=True,
        low_prop_cull_factor=1.0,
    ),
    "pc_high": RuntimeProfile(
        name="PC Player High (PcTierTable)",
        tier="High",
        lod_bias=1.5,
        far_clip=3000.0,
        aspect=1920 / 1080,
        band_fine=0.407,
        tree_card_scale=1.5,
        tree_ends_base=(20.0, 60.0, 1000.0),
        tree_cull_cap=1000.0,
        hlod_m=150.0,
        hlod_cull_m=INF,
        high_only_trees=True,
        low_prop_cull_factor=1.0,
    ),
    "vqa_low": RuntimeProfile(
        name="VQA/Editor Low (QualityProfile)",
        tier="Low",
        lod_bias=0.5,
        far_clip=900.0,
        aspect=1920 / 1080,
        band_fine=0.30,  # WORKING_VALUE: TerrainBandLowM=10 m (vs 15 m + dilation on High -> 0.407)
        tree_card_scale=0.5,
        tree_ends_base=(20.0, 60.0, 1000.0),
        tree_cull_cap=600.0,
        hlod_m=70.0,
        hlod_cull_m=1000.0,
        high_only_trees=False,
        low_prop_cull_factor=1.0,
    ),
    "pc_low": RuntimeProfile(
        name="PC Player Low (PcTierTable)",
        tier="Low",
        lod_bias=1.0,
        far_clip=1500.0,
        aspect=1920 / 1080,
        band_fine=0.30,
        tree_card_scale=0.5,
        tree_ends_base=(20.0, 60.0, 1000.0),
        tree_cull_cap=600.0,
        hlod_m=70.0,
        hlod_cull_m=1500.0,
        high_only_trees=False,
        low_prop_cull_factor=0.75,  # WORKING_VALUE: WorldPropTierPolicy car/van 150 m vs 200 m vehicleCullM, fab 50 m
    ),
}


def git_read_blobs(ref: str, paths: list[str]) -> dict[str, bytes]:
    if not paths:
        return {}
    query = "".join(f"{ref}:{p}\n" for p in paths).encode("utf-8")
    res = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=REPO,
        input=query,
        capture_output=True,
        check=True,
    )
    raw = res.stdout
    out: dict[str, bytes] = {}
    pos = 0
    for p in paths:
        nl = raw.find(b"\n", pos)
        if nl < 0:
            break
        header = raw[pos:nl].decode("utf-8", errors="replace").strip()
        pos = nl + 1
        if header.endswith("missing") or not header:
            continue
        size = int(header.split()[2])
        out[p] = raw[pos:pos + size]
        pos += size + 1  # skip trailing LF
    return out


def list_regions_in_ref(ref: str) -> list[str]:
    out = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", ref, "Data/Regions"],
        cwd=REPO,
        text=True,
    ).splitlines()
    return sorted({p.split("/")[2] for p in out if p.endswith("/generated/streetscape_qa.json")})


def changed_regions(base_ref: str, target_ref: str) -> set[str]:
    out = subprocess.check_output(
        ["git", "diff", "--name-only", base_ref, target_ref, "--", "Data/Regions"],
        cwd=REPO,
        text=True,
    ).splitlines()
    return {p.split("/")[2] for p in out if len(p.split("/")) > 2}


def _center(ch: dict[str, Any]) -> tuple[float, float]:
    b = ch["bounds_local_m"]
    return (b["e_min"] + b["e_max"]) / 2.0, (b["n_min"] + b["n_max"]) / 2.0


def _bbox_dist(b: list[float], p: tuple[float, float]) -> float:
    dx = max(b[0] - p[0], 0.0, p[0] - b[2])
    dy = max(b[1] - p[1], 0.0, p[1] - b[3])
    return math.hypot(dx, dy)


def _look(cam: dict[str, Any]) -> tuple[float, float]:
    lx = cam["look_at"][0] - cam["pos"][0]
    ly = cam["look_at"][1] - cam["pos"][1]
    n = max(math.hypot(lx, ly), 1e-9)
    return lx / n, ly / n


def _hfov_deg(vfov_deg: float, aspect: float) -> float:
    return math.degrees(2.0 * math.atan(math.tan(math.radians(vfov_deg) / 2.0) * aspect))


def _lod_ends(switch_m: list[float], chunk_size: float, lod_bias: float, vfov_deg: float) -> list[float]:
    k = lod_bias * math.tan(math.radians(30.0)) / math.tan(math.radians(vfov_deg) / 2.0)
    return [(s + 0.7 * chunk_size) * k for s in switch_m[1:]]


def _chunk_in_frustum(bounds: dict[str, Any], cam: dict[str, Any], hfov: float, far: float) -> bool:
    px, py = cam["pos"][0], cam["pos"][1]
    e0, e1, n0, n1 = bounds["e_min"], bounds["e_max"], bounds["n_min"], bounds["n_max"]
    if e0 <= px <= e1 and n0 <= py <= n1:
        return True
    lx, ly = _look(cam)
    half = math.radians(hfov) / 2.0
    cos_h = math.cos(half)

    def inside(x: float, y: float) -> bool:
        dx, dy = x - px, y - py
        d = math.hypot(dx, dy)
        return d <= far and (d < 1e-6 or (dx * lx + dy * ly) / d >= cos_h)

    steps = 16
    for i in range(steps + 1):
        f = i / steps
        for x, y in (
            (e0 + f * (e1 - e0), n0),
            (e0 + f * (e1 - e0), n1),
            (e0, n0 + f * (n1 - n0)),
            (e1, n0 + f * (n1 - n0)),
        ):
            if inside(x, y):
                return True
    for s in (-half, half):
        rx = lx * math.cos(s) - ly * math.sin(s)
        ry = lx * math.sin(s) + ly * math.cos(s)
        r = 0.0
        while r <= far:
            x, y = px + rx * r, py + ry * r
            if e0 <= x <= e1 and n0 <= y <= n1:
                return True
            r += 8.0
    return False


def legacy_subbreakdown(
    manifest: dict[str, Any],
    cam: dict[str, Any],
    tier: str,
    qa_cat: dict[str, int],
) -> dict[str, int]:
    """Exact subcategory breakdown of build_world.mesh_budget for High or Low."""
    pol = LEGACY_POLICY[tier]
    px, py = cam["pos"][0], cam["pos"][1]
    lx, ly = _look(cam)
    sub = {
        "buildings_lod0": 0,
        "buildings_lod1": 0,
        "terrain_lod0": 0,
        "terrain_lod1": 0,
        "terrain_lod2": 0,
        "terrain_lod3": 0,
        "roads_road": 0,
        "roads_bridge": 0,
        "roads_markings": 0,
        "roads_paved": 0,
        "furn_furniture": 0,
        "furn_plots": 0,
        "furn_wires": 0,
        "water_surface": 0,
        "water_banks": 0,
        "forest_hlod": 0,
    }
    for ch in manifest["chunks"]:
        b = ch["bounds_local_m"]
        cx = (b["e_min"] + b["e_max"]) / 2.0
        cy = (b["n_min"] + b["n_max"]) / 2.0
        d = math.hypot(cx - px, cy - py)
        if d > 1600.0 or (d > 200.0 and ((cx - px) * lx + (cy - py) * ly) / d < 0.5):
            continue
        t = ch["triangles"]
        lod = next(lv for lim, lv in pol["terrain"] if d < lim)
        sub[f"terrain_lod{lod}"] += t.get(f"terrain_lod{lod}", 0)

        sub["roads_road"] += t.get("road", 0)
        sub["roads_bridge"] += t.get("bridge", 0)
        sub["roads_markings"] += t.get("markings", 0)
        sub["roads_paved"] += t.get("paved", 0)

        if t.get("water"):
            sub["water_surface"] += t["water"]
        if t.get("banks"):
            if d < 500.0:
                sub["water_banks"] += t["banks"] if tier == "High" else t.get("banks_low", 0)

        if d < pol["furn"]:
            sub["furn_furniture"] += t.get("furniture", 0)
            sub["furn_plots"] += t.get("plots", 0) if tier == "High" else t.get("plots_low", t.get("plots", 0))
            sub["furn_wires"] += t.get("wires", 0)

        if d < pol["bld"]:
            sub["buildings_lod0"] += t.get("buildings", 0)
        else:
            sub["buildings_lod1"] += t.get("buildings_lod1", 0)

        for fc in ch.get("forest_cells", []):
            dfc = _bbox_dist(fc["bbox_local_m"], (px, py))
            if pol["forest_hlod_m"] < dfc < pol["forest_hlod_cull_m"]:
                sub["forest_hlod"] += fc["tris"]

    # Verify exact match with streetscape_qa.json
    assert sub["buildings_lod0"] + sub["buildings_lod1"] == qa_cat.get("buildings", 0), (tier, cam["id"], sub, qa_cat)
    assert (
        sub["terrain_lod0"] + sub["terrain_lod1"] + sub["terrain_lod2"] + sub["terrain_lod3"]
        == qa_cat.get("terrain", 0)
    ), (tier, cam["id"])
    assert (
        sub["roads_road"] + sub["roads_bridge"] + sub["roads_markings"] + sub["roads_paved"]
        == qa_cat.get("roads", 0)
    ), (tier, cam["id"])
    assert sub["furn_furniture"] + sub["furn_plots"] + sub["furn_wires"] == qa_cat.get("furniture", 0), (tier, cam["id"])
    assert sub["water_surface"] + sub["water_banks"] == qa_cat.get("water", 0), (tier, cam["id"])
    assert sub["forest_hlod"] == qa_cat.get("forest_hlod", 0), (tier, cam["id"])

    sub["trees_lod0"] = qa_cat.get("trees_lod0", 0)
    sub["trees_lod1"] = qa_cat.get("trees_lod1", 0)
    sub["trees_lod2"] = qa_cat.get("trees_lod2", 0)
    sub["props"] = qa_cat.get("props", 0)
    return sub


def far_field_in_view(manifest: dict[str, Any], ff_qa: dict[str, Any], cam: dict[str, Any], tier: str, aspect: float) -> tuple[int, int]:
    """Returns (far_field_in_view_tris, far_field_total_tris) for High or Low."""
    ff_man = (manifest.get("far_field") or {}).get(tier) or {}
    ff_t = (ff_qa.get("tiers") or {}).get(tier) or {}
    total = int(ff_t.get("total_triangles", 0))
    if not ff_man:
        return 0, total
    hfov = _hfov_deg(cam.get("fov_deg", 60.0), aspect)
    lx, ly = _look(cam)
    dirs = {"far_east": (1, 0), "far_west": (-1, 0), "far_north": (0, 1), "far_south": (0, -1)}
    vis = int((ff_man.get("skyline") or {}).get("triangles", 0))
    for k, s in (ff_man.get("sectors") or {}).items():
        v = dirs.get(k)
        if v and math.degrees(math.acos(max(-1.0, min(1.0, v[0] * lx + v[1] * ly)))) <= hfov / 2.0 + 45.0:
            vis += int(s.get("triangles", 0))
    return vis, total


def tree_means() -> dict[str, float]:
    trees = json.loads(TREES_META_PATH.read_text(encoding="utf-8"))["trees"]
    return {k: statistics.mean(t.get(k, 0) for t in trees.values()) for k in ("tris_lod0", "tris_lod1", "tris_lod2")}


def runtime_estimate(
    manifest: dict[str, Any],
    ff_qa: dict[str, Any],
    cam: dict[str, Any],
    qa_cat_high: dict[str, int],
    qa_cat_low: dict[str, int],
    prof: RuntimeProfile,
    means: dict[str, float],
) -> dict[str, int]:
    """Runtime triangle estimate matching WorldSceneBuilder + RegionImporter + WorldInstances."""
    vfov = cam.get("fov_deg", 60.0)
    hfov = _hfov_deg(vfov, prof.aspect)
    size = manifest["chunk_size_m"]
    ends = _lod_ends([t["suggested_switch_m"] for t in manifest["terrain_lods"]], size, prof.lod_bias, vfov)
    lod_table = HIGH_LODS if prof.tier == "High" else LOW_LODS
    px, py, ph = cam["pos"]
    cat = {
        "terrain": 0.0,
        "roads": 0.0,
        "furniture": 0.0,
        "buildings": 0.0,
        "water": 0.0,
        "forest_hlod": 0.0,
        "trees": 0.0,
        "props": 0.0,
        "far_field": 0.0,
    }
    for ch in manifest["chunks"]:
        b = ch["bounds_local_m"]
        if not _chunk_in_frustum(b, cam, hfov, prof.far_clip):
            continue
        cx, cy = _center(ch)
        cz = (b.get("z_min_evrf2007", ph) + b.get("z_max_evrf2007", ph)) / 2.0
        d = math.sqrt((cx - px) ** 2 + (cy - py) ** 2 + (cz - ph) ** 2)
        lod = next((i for i, e in enumerate(ends) if d < e), len(ends))
        layers = lod_table[lod]
        t = ch["triangles"]
        for node in layers:
            c = NODE_CATEGORY[node]
            if node == "terrain_band":
                if prof.tier == "High":
                    n = t.get("terrain_lod0", 0) * (prof.band_fine + (1.0 - prof.band_fine) / 4.0)
                else:
                    n = t.get("terrain_lod1", 0) * (prof.band_fine + (1.0 - prof.band_fine) / 4.0)
            elif node == "buildings":
                n = t.get("buildings", 0) or t.get("buildings_lod1", 0)
            else:
                n = t.get(node, 0)
            cat[c] += n
        for fc in ch.get("forest_cells", []):
            dfc = _bbox_dist(fc["bbox_local_m"], (px, py))
            if prof.hlod_m < dfc < prof.hlod_cull_m and dfc <= prof.far_clip:
                cat["forest_hlod"] += fc["tris"]

    # Rescale instanced props & trees from legacy frame_estimate
    f_frustum = hfov / 360.0
    # Legacy High trees_lod0 covers disc r=35 m in all directions (on High trees_lod0 exists)
    n0 = qa_cat_high.get("trees_lod0", 0) / max(means["tris_lod0"], 1e-9)
    rho = n0 / (math.pi * 35.0 ** 2)
    if not prof.high_only_trees:
        # Rough share on Low: highOnly garden trees skipped (~20-35% in cities); approximate via Low/High trees_lod1+lod2 ratio
        hi_12 = max(qa_cat_high.get("trees_lod1", 0) + qa_cat_high.get("trees_lod2", 0), 1)
        lo_12 = qa_cat_low.get("trees_lod1", 0) + qa_cat_low.get("trees_lod2", 0)
        # Note: legacy Low trees_lod1 goes 0-35m (vs High 35-80m), so use simple tree_scale 0.75 WORKING_VALUE for garden skip
        rho *= 0.75
        _ = hi_12, lo_12
    e0 = prof.tree_ends_base[0] * min(prof.lod_bias, prof.tree_card_scale)
    e1 = prof.tree_ends_base[1] * min(prof.lod_bias, prof.tree_card_scale)
    e2 = min(prof.tree_ends_base[2] * prof.lod_bias, prof.tree_cull_cap * prof.lod_bias, prof.far_clip)
    trees_near = f_frustum * rho * math.pi * (e0 ** 2 * means["tris_lod0"] + max(0.0, e1 ** 2 - e0 ** 2) * means["tris_lod1"])
    # Legacy trees_lod2 extends 80..1500 (High) or 35..400 (Low) in 120 deg wedge (1/3 circle) + 200 m disc
    # Scale by frustum ratio and cull range ratio
    if prof.tier == "High":
        trees_lod2 = qa_cat_high.get("trees_lod2", 0) * (hfov / 120.0) * min(1.0, (e2 / 1500.0))
        props_base = qa_cat_high.get("props", 0) * f_frustum
    else:
        # In legacy Low, trees_lod2 is 35..400 m; if runtime tree_cull_cap * lod_bias > 400 m, scale proportionally (capped)
        trees_lod2 = qa_cat_low.get("trees_lod2", 0) * (hfov / 120.0) * (min(e2, 900.0) / 400.0)
        props_base = qa_cat_low.get("props", 0) * f_frustum * prof.low_prop_cull_factor

    cat["trees"] = trees_near + trees_lod2
    cat["props"] = props_base
    ff_vis, _ = far_field_in_view(manifest, ff_qa, cam, prof.tier, prof.aspect)
    cat["far_field"] = ff_vis
    out = {k: round(v) for k, v in cat.items()}
    out["total"] = sum(out.values())
    return out


# ---------------------------------------------------------------------------- Variant B simulations
def simulate_variant_legacy(
    manifest: dict[str, Any],
    cam: dict[str, Any],
    qa_cat: dict[str, int],
    tier: str,
    *,
    bld_lod0_m: float | None = None,
    bld_lod0b_ratio: float = 1.0,
    bld_hlod_from_m: float | None = None,
    bld_hlod_ratio: float = 0.30,
    plots_cull_m: float | None = None,
    furn_cull_m: float | None = None,
    markings_cull_m: float | None = None,
    paved_cull_m: float | None = None,
    terrain_lod0_m: float | None = None,
    terrain_lod1_m: float | None = None,
    tree_scale: float = 1.0,
    tree_card_scale: float | None = None,
    forest_hlod_m: float | None = None,
    props_scale: float = 1.0,
    means: dict[str, float] | None = None,
) -> dict[str, int]:
    """Simulate Variant B reductions on build_world.mesh_budget (legacy frame_estimate)."""
    pol = LEGACY_POLICY[tier]
    px, py = cam["pos"][0], cam["pos"][1]
    lx, ly = _look(cam)
    res = {"buildings": 0.0, "terrain": 0.0, "roads": 0.0, "furniture": 0.0, "water": 0.0, "forest_hlod": 0.0, "trees": 0.0, "props": 0.0}
    for ch in manifest["chunks"]:
        b = ch["bounds_local_m"]
        cx = (b["e_min"] + b["e_max"]) / 2.0
        cy = (b["n_min"] + b["n_max"]) / 2.0
        d = math.hypot(cx - px, cy - py)
        if d > 1600.0 or (d > 200.0 and ((cx - px) * lx + (cy - py) * ly) / d < 0.5):
            continue
        t = ch["triangles"]
        # Terrain
        lod = next(lv for lim, lv in pol["terrain"] if d < lim)
        if tier == "High" and terrain_lod0_m is not None and lod == 0 and d >= terrain_lod0_m + MARGIN_M:
            lod = 1
        if tier == "Low" and terrain_lod1_m is not None and lod == 1 and d >= terrain_lod1_m + MARGIN_M:
            lod = 2
        res["terrain"] += t.get(f"terrain_lod{lod}", 0)

        # Roads
        mk = 0 if (markings_cull_m is not None and d >= markings_cull_m + MARGIN_M) else t.get("markings", 0)
        pv = 0 if (paved_cull_m is not None and d >= paved_cull_m + MARGIN_M) else t.get("paved", 0)
        res["roads"] += t.get("road", 0) + t.get("bridge", 0) + mk + pv

        # Water
        if t.get("water"):
            res["water"] += t["water"]
        if t.get("banks") and d < 500.0:
            res["water"] += t["banks"] if tier == "High" else t.get("banks_low", 0)

        # Furniture & plots
        if d < pol["furn"]:
            fu = 0 if (furn_cull_m is not None and d >= furn_cull_m + MARGIN_M) else t.get("furniture", 0)
            pl_raw = t.get("plots", 0) if tier == "High" else t.get("plots_low", t.get("plots", 0))
            pl = 0 if (plots_cull_m is not None and d >= plots_cull_m + MARGIN_M) else pl_raw
            res["furniture"] += fu + pl + t.get("wires", 0)

        # Buildings
        bld_end = pol["bld"] if bld_lod0_m is None else min(pol["bld"], bld_lod0_m + MARGIN_M)
        if d < bld_end:
            nb = t.get("buildings", 0)
            if bld_lod0b_ratio < 1.0 and d >= 100.0 + MARGIN_M:
                nb *= bld_lod0b_ratio
            res["buildings"] += nb
        else:
            nl1 = t.get("buildings_lod1", 0)
            if bld_hlod_from_m is not None and d >= bld_hlod_from_m + MARGIN_M:
                nl1 *= bld_hlod_ratio
            res["buildings"] += nl1

        # Forest HLOD
        hlod_m = pol["forest_hlod_m"] if forest_hlod_m is None else forest_hlod_m
        for fc in ch.get("forest_cells", []):
            dfc = _bbox_dist(fc["bbox_local_m"], (px, py))
            if hlod_m < dfc < pol["forest_hlod_cull_m"]:
                res["forest_hlod"] += fc["tris"]

    # Trees
    t_legacy = qa_cat.get("trees_lod0", 0) + qa_cat.get("trees_lod1", 0) + qa_cat.get("trees_lod2", 0)
    if tree_card_scale is not None and tier == "High" and means is not None:
        # Replace legacy 35/80m disc with treeCardLodScale (e.g. 0.5 -> 10/30m in all directions for legacy model, or 20/60 * 0.5)
        n0 = qa_cat.get("trees_lod0", 0) / max(means["tris_lod0"], 1e-9)
        rho = n0 / (math.pi * 35.0 ** 2)
        e0, e1 = 20.0 * tree_card_scale, 60.0 * tree_card_scale
        t_new = rho * math.pi * (e0 ** 2 * means["tris_lod0"] + max(0.0, e1 ** 2 - e0 ** 2) * means["tris_lod1"])
        t_legacy = t_new + qa_cat.get("trees_lod2", 0)
    res["trees"] = t_legacy * tree_scale
    res["props"] = qa_cat.get("props", 0) * props_scale
    out = {k: round(v) for k, v in res.items()}
    out["total"] = sum(out.values())
    return out


def classify_tile(region_id: str, total_buildings: int) -> str:
    if region_id.startswith("bialystok-"):
        if total_buildings >= 1500:
            return "city_dense"
        return "city_outer"
    if region_id in ("knyszyn", "monki", "monki-e", "tykocin"):
        return "town"
    return "rural_corridor"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", default="regen-wave-14-s25", help="Git ref with Data/Regions/*/generated")
    ap.add_argument("--base-ref", default="main", help="Base git ref to detect wave-14 rebuilt tiles")
    ap.add_argument("--json", type=Path, help="Optional output JSON path")
    args = ap.parse_args()

    ref_sha = subprocess.check_output(["git", "rev-parse", "--short", args.ref], cwd=REPO, text=True).strip()
    regions = list_regions_in_ref(args.ref)
    rebuilt = changed_regions(args.base_ref, args.ref)
    means = tree_means()

    # Batch-load all required files from git
    paths: list[str] = []
    for r in regions:
        paths.extend([
            f"Data/Regions/{r}/generated/streetscape_qa.json",
            f"Data/Regions/{r}/generated/world_manifest.json",
            f"Data/Regions/{r}/generated/control_cameras.json",
            f"Data/Regions/{r}/generated/far_field_qa.json",
        ])
    blobs = git_read_blobs(args.ref, paths)

    records = []
    for r in regions:
        sq_b = blobs.get(f"Data/Regions/{r}/generated/streetscape_qa.json")
        wm_b = blobs.get(f"Data/Regions/{r}/generated/world_manifest.json")
        cc_b = blobs.get(f"Data/Regions/{r}/generated/control_cameras.json")
        ff_b = blobs.get(f"Data/Regions/{r}/generated/far_field_qa.json")
        if not (sq_b and wm_b and cc_b and ff_b):
            continue
        sq = json.loads(sq_b)
        wm = json.loads(wm_b)
        cc = json.loads(cc_b)
        ff = json.loads(ff_b)
        fe_list = sq["mesh_budget"]["frame_estimate"]
        cams = {c["id"]: c for c in cc["cameras"] if c["type"] == "persp"}
        worst_h = max(fe_list, key=lambda x: x["tris_high"])
        worst_l = max(fe_list, key=lambda x: x["tris_low"])
        cam_h = cams[worst_h["camera"]]
        cam_l = cams[worst_l["camera"]]

        sub_h = legacy_subbreakdown(wm, cam_h, "High", worst_h["by_category_high"])
        sub_l = legacy_subbreakdown(wm, cam_l, "Low", worst_l["by_category_low"])
        ff_vis_h, ff_tot_h = far_field_in_view(wm, ff, cam_h, "High", 1920 / 1080)
        ff_vis_l, ff_tot_l = far_field_in_view(wm, ff, cam_l, "Low", 1920 / 1080)

        # Runtime estimates on worst legacy High & Low cameras
        rt_vqa_h = runtime_estimate(wm, ff, cam_h, worst_h["by_category_high"], worst_h["by_category_low"], PROFILES["vqa_high"], means)
        rt_pc_h = runtime_estimate(wm, ff, cam_h, worst_h["by_category_high"], worst_h["by_category_low"], PROFILES["pc_high"], means)
        rt_vqa_l = runtime_estimate(wm, ff, cam_l, worst_l["by_category_high"], worst_l["by_category_low"], PROFILES["vqa_low"], means)
        rt_pc_l = runtime_estimate(wm, ff, cam_l, worst_l["by_category_high"], worst_l["by_category_low"], PROFILES["pc_low"], means)

        # Also find max runtime across all persp cameras for PC High & PC Low
        all_rt_pc_h = [
            (f["camera"], runtime_estimate(wm, ff, cams[f["camera"]], f["by_category_high"], f["by_category_low"], PROFILES["pc_high"], means)["total"])
            for f in fe_list if f["camera"] in cams
        ]
        all_rt_pc_l = [
            (f["camera"], runtime_estimate(wm, ff, cams[f["camera"]], f["by_category_high"], f["by_category_low"], PROFILES["pc_low"], means)["total"])
            for f in fe_list if f["camera"] in cams
        ]
        max_rt_pc_h = max(all_rt_pc_h, key=lambda x: x[1])
        max_rt_pc_l = max(all_rt_pc_l, key=lambda x: x[1])

        bld_count = sum(sq["buildings"].get("subtypes", {}).values())
        ttype = classify_tile(r, bld_count)

        # Variant B simulations on worst High and worst Low cameras
        var_b = {
            "base_high": worst_h["tris_high"],
            "base_low": worst_l["tris_low"],
            "B0_tree_card_05_high": simulate_variant_legacy(wm, cam_h, worst_h["by_category_high"], "High", tree_card_scale=0.5, means=means)["total"],
            "B1_bld200_lod0b_hlod_high": simulate_variant_legacy(wm, cam_h, worst_h["by_category_high"], "High", bld_lod0_m=200.0, bld_lod0b_ratio=0.60, bld_hlod_from_m=700.0, bld_hlod_ratio=0.30)["total"],
            "B2_trees_minus30_high": simulate_variant_legacy(wm, cam_h, worst_h["by_category_high"], "High", tree_scale=0.70, forest_hlod_m=80.0)["total"],
            "B3_plots200_furn300_high": simulate_variant_legacy(wm, cam_h, worst_h["by_category_high"], "High", plots_cull_m=200.0, furn_cull_m=300.0)["total"],
            "B4_markings300_high": simulate_variant_legacy(wm, cam_h, worst_h["by_category_high"], "High", markings_cull_m=300.0)["total"],
            "B5_terrain150_high": simulate_variant_legacy(wm, cam_h, worst_h["by_category_high"], "High", terrain_lod0_m=150.0)["total"],
            "B_all_content_high": simulate_variant_legacy(
                wm, cam_h, worst_h["by_category_high"], "High",
                bld_lod0_m=200.0, bld_lod0b_ratio=0.60, bld_hlod_from_m=700.0, bld_hlod_ratio=0.30,
                plots_cull_m=200.0, furn_cull_m=300.0, markings_cull_m=300.0,
                terrain_lod0_m=150.0, tree_scale=0.70, forest_hlod_m=80.0, props_scale=0.85,
            )["total"],
            "B_all_plus_treecard05_high": simulate_variant_legacy(
                wm, cam_h, worst_h["by_category_high"], "High",
                bld_lod0_m=200.0, bld_lod0b_ratio=0.60, bld_hlod_from_m=700.0, bld_hlod_ratio=0.30,
                plots_cull_m=200.0, furn_cull_m=300.0, markings_cull_m=300.0,
                terrain_lod0_m=150.0, tree_scale=0.70, tree_card_scale=0.5, forest_hlod_m=80.0, props_scale=0.85, means=means,
            )["total"],
            "B1_bld_hlod500_low": simulate_variant_legacy(wm, cam_l, worst_l["by_category_low"], "Low", bld_hlod_from_m=500.0, bld_hlod_ratio=0.30)["total"],
            "B3_plots120_furn200_low": simulate_variant_legacy(wm, cam_l, worst_l["by_category_low"], "Low", plots_cull_m=120.0, furn_cull_m=200.0)["total"],
            "B4_mark200_paved400_low": simulate_variant_legacy(wm, cam_l, worst_l["by_category_low"], "Low", markings_cull_m=200.0, paved_cull_m=400.0)["total"],
            "B5_terrain_lod2_150_low": simulate_variant_legacy(wm, cam_l, worst_l["by_category_low"], "Low", terrain_lod1_m=150.0)["total"],
            "B_all_low": simulate_variant_legacy(
                wm, cam_l, worst_l["by_category_low"], "Low",
                bld_hlod_from_m=500.0, bld_hlod_ratio=0.30,
                plots_cull_m=120.0, furn_cull_m=200.0,
                markings_cull_m=200.0, paved_cull_m=400.0,
                terrain_lod1_m=150.0, tree_scale=0.75, props_scale=0.75,
            )["total"],
        }

        records.append({
            "region": r,
            "rebuilt_w14": r in rebuilt,
            "type": ttype,
            "buildings_count": bld_count,
            "worst_high": {
                "camera": worst_h["camera"],
                "tris": worst_h["tris_high"],
                "materials": worst_h["materials_high"],
                "by_category": worst_h["by_category_high"],
                "sub": sub_h,
                "far_field_in_view": ff_vis_h,
                "far_field_total": ff_tot_h,
                "rt_vqa": rt_vqa_h,
                "rt_pc": rt_pc_h,
            },
            "worst_low": {
                "camera": worst_l["camera"],
                "tris": worst_l["tris_low"],
                "materials": worst_l["materials_low"],
                "by_category": worst_l["by_category_low"],
                "sub": sub_l,
                "far_field_in_view": ff_vis_l,
                "far_field_total": ff_tot_l,
                "rt_vqa": rt_vqa_l,
                "rt_pc": rt_pc_l,
            },
            "max_rt_pc_high": {"camera": max_rt_pc_h[0], "tris": max_rt_pc_h[1]},
            "max_rt_pc_low": {"camera": max_rt_pc_l[0], "tris": max_rt_pc_l[1]},
            "variant_b": var_b,
        })

    over_h = sorted([x for x in records if x["worst_high"]["tris"] > 2_000_000], key=lambda x: -x["worst_high"]["tris"])
    over_l = sorted([x for x in records if x["worst_low"]["tris"] > 600_000], key=lambda x: -x["worst_low"]["tris"])

    print(f"Ref: {args.ref} ({ref_sha}) | total regions with QA: {len(records)} | rebuilt vs {args.base_ref}: {sum(1 for x in records if x['rebuilt_w14'])}")
    print(f"High > 2.0M: {len(over_h)} | Low > 600k: {len(over_l)}")
    print("\n--- HIGH > 2.0M (+ bialystok-industrial-c) ---")
    c_rec = next(x for x in records if x["region"] == "bialystok-industrial-c")
    for x in [*over_h, c_rec]:
        w = x["worst_high"]
        s = w["sub"]
        trees = s["trees_lod0"] + s["trees_lod1"] + s["trees_lod2"] + s["forest_hlod"]
        print(
            f"{x['region']:24s} {w['camera']:24s} tot={w['tris']:9,d} | "
            f"bld={s['buildings_lod0']+s['buildings_lod1']:7,d}({s['buildings_lod0']:,d}+{s['buildings_lod1']:,d}) "
            f"furn={s['furn_furniture']+s['furn_plots']+s['furn_wires']:7,d}({s['furn_furniture']:,d}/{s['furn_plots']:,d}/{s['furn_wires']:,d}) "
            f"trn={w['by_category']['terrain']:7,d} rds={w['by_category']['roads']:7,d} "
            f"tre={trees:7,d} prp={s['props']:6,d} ff={w['far_field_in_view']:6,d} | "
            f"rt_pc={w['rt_pc']['total']:9,d} rt_vqa={w['rt_vqa']['total']:9,d}"
        )

    print("\n--- LOW > 600k (top 14) ---")
    for x in over_l:
        w = x["worst_low"]
        s = w["sub"]
        trees = s["trees_lod0"] + s["trees_lod1"] + s["trees_lod2"] + s["forest_hlod"]
        print(
            f"{x['region']:24s} {w['camera']:24s} tot={w['tris']:9,d} | "
            f"rds={w['by_category']['roads']:7,d}({s['roads_road']:,d}/{s['roads_paved']:,d}/{s['roads_markings']:,d}) "
            f"bld1={s['buildings_lod1']:7,d} trn={w['by_category']['terrain']:7,d} "
            f"furn={w['by_category']['furniture']:7,d} tre={trees:6,d} prp={s['props']:6,d} ff={w['far_field_in_view']:5,d} | "
            f"rt_pc={w['rt_pc']['total']:9,d} rt_vqa={w['rt_vqa']['total']:9,d}"
        )

    print("\n--- BY TILE TYPE ---")
    for tt in ("city_dense", "city_outer", "town", "rural_corridor"):
        grp = [x for x in records if x["type"] == tt]
        hs = sorted(x["worst_high"]["tris"] for x in grp)
        ls = sorted(x["worst_low"]["tris"] for x in grp)
        rths = sorted(x["max_rt_pc_high"]["tris"] for x in grp)
        rtls = sorted(x["max_rt_pc_low"]["tris"] for x in grp)
        print(
            f"{tt:15s} n={len(grp):2d} | "
            f"leg_H med={statistics.median(hs):,.0f} max={hs[-1]:,.0f} | "
            f"leg_L med={statistics.median(ls):,.0f} max={ls[-1]:,.0f} | "
            f"rt_pc_H max={rths[-1]:,.0f} | rt_pc_L max={rtls[-1]:,.0f}"
        )

    if args.json:
        payload = {
            "ref": args.ref,
            "ref_sha": ref_sha,
            "base_ref": args.base_ref,
            "regions_count": len(records),
            "records": records,
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    main()
