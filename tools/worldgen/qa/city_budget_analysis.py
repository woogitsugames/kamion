"""City-tile triangle budget analysis for wave 14 (task codex-city-budget-s25).

Reads generated QA JSONs and manifests directly from git (default ref: `regen-wave-14-s25`)
without modifying `Data/Regions/*/generated` or `Data/raw/derived`.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[3]
MAIN_REPO = Path(r"C:\Users\matma\Documents\Claude\kamion")
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
    low_prop_cull_factor: float


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
        band_fine=0.30,
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
        low_prop_cull_factor=0.75,
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
        pos += size + 1
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
        if t.get("banks") and d < 500.0:
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

    assert sub["buildings_lod0"] + sub["buildings_lod1"] == qa_cat.get("buildings", 0), (tier, cam["id"])
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
    props_scale: float = 1.0,
    hlod_m_override: float | None = None,
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
    hlod_m = prof.hlod_m if hlod_m_override is None else hlod_m_override
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
                    if terrain_lod0_m is not None and d >= terrain_lod0_m + MARGIN_M:
                        n = t.get("terrain_lod1", 0)
                    else:
                        n = t.get("terrain_lod0", 0) * (prof.band_fine + (1.0 - prof.band_fine) / 4.0)
                else:
                    if terrain_lod1_m is not None and d >= terrain_lod1_m + MARGIN_M:
                        n = t.get("terrain_lod2", 0)
                    else:
                        n = t.get("terrain_lod1", 0) * (prof.band_fine + (1.0 - prof.band_fine) / 4.0)
            elif node == "terrain_lod1" and prof.tier == "Low" and terrain_lod1_m is not None and d >= terrain_lod1_m + MARGIN_M:
                n = t.get("terrain_lod2", 0)
            elif node == "buildings":
                if bld_lod0_m is not None and d >= bld_lod0_m + MARGIN_M:
                    n = t.get("buildings_lod1", 0)
                else:
                    n = t.get("buildings", 0) or t.get("buildings_lod1", 0)
                    if bld_lod0b_ratio < 1.0 and d >= 100.0 + MARGIN_M and t.get("buildings"):
                        n *= bld_lod0b_ratio
            elif node == "buildings_lod1":
                n = t.get("buildings_lod1", 0)
                if bld_hlod_from_m is not None and d >= bld_hlod_from_m + MARGIN_M:
                    n *= bld_hlod_ratio
            elif node == "markings" and markings_cull_m is not None and d >= markings_cull_m + MARGIN_M:
                n = 0.0
            elif node == "paved" and paved_cull_m is not None and d >= paved_cull_m + MARGIN_M:
                n = 0.0
            elif node == "furniture" and furn_cull_m is not None and d >= furn_cull_m + MARGIN_M:
                n = 0.0
            elif node in ("plots", "plots_low") and plots_cull_m is not None and d >= plots_cull_m + MARGIN_M:
                n = 0.0
            else:
                n = t.get(node, 0)
            cat[c] += n
        for fc in ch.get("forest_cells", []):
            dfc = _bbox_dist(fc["bbox_local_m"], (px, py))
            if hlod_m < dfc < prof.hlod_cull_m and dfc <= prof.far_clip:
                cat["forest_hlod"] += fc["tris"]

    f_frustum = hfov / 360.0
    n0 = qa_cat_high.get("trees_lod0", 0) / max(means["tris_lod0"], 1e-9)
    rho = n0 / (math.pi * 35.0 ** 2)
    if not prof.high_only_trees:
        rho *= 0.75
    e0 = prof.tree_ends_base[0] * min(prof.lod_bias, prof.tree_card_scale)
    e1 = prof.tree_ends_base[1] * min(prof.lod_bias, prof.tree_card_scale)
    e2 = min(prof.tree_ends_base[2] * prof.lod_bias, prof.tree_cull_cap * prof.lod_bias, prof.far_clip)
    trees_near = f_frustum * rho * math.pi * (e0 ** 2 * means["tris_lod0"] + max(0.0, e1 ** 2 - e0 ** 2) * means["tris_lod1"])
    if prof.tier == "High":
        trees_lod2 = qa_cat_high.get("trees_lod2", 0) * (hfov / 120.0) * min(1.0, (e2 / 1500.0))
        props_base = qa_cat_high.get("props", 0) * f_frustum
    else:
        trees_lod2 = qa_cat_low.get("trees_lod2", 0) * (hfov / 120.0) * (min(e2, 900.0) / 400.0)
        props_base = qa_cat_low.get("props", 0) * f_frustum * prof.low_prop_cull_factor

    cat["trees"] = (trees_near + trees_lod2) * tree_scale
    cat["props"] = props_base * props_scale
    ff_vis, _ = far_field_in_view(manifest, ff_qa, cam, prof.tier, prof.aspect)
    cat["far_field"] = ff_vis
    out = {k: round(v) for k, v in cat.items()}
    out["total"] = sum(out.values())
    return out


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
        lod = next(lv for lim, lv in pol["terrain"] if d < lim)
        if tier == "High" and terrain_lod0_m is not None and lod == 0 and d >= terrain_lod0_m + MARGIN_M:
            lod = 1
        if tier == "Low" and terrain_lod1_m is not None and lod == 1 and d >= terrain_lod1_m + MARGIN_M:
            lod = 2
        res["terrain"] += t.get(f"terrain_lod{lod}", 0)

        mk = 0 if (markings_cull_m is not None and d >= markings_cull_m + MARGIN_M) else t.get("markings", 0)
        pv = 0 if (paved_cull_m is not None and d >= paved_cull_m + MARGIN_M) else t.get("paved", 0)
        res["roads"] += t.get("road", 0) + t.get("bridge", 0) + mk + pv

        if t.get("water"):
            res["water"] += t["water"]
        if t.get("banks") and d < 500.0:
            res["water"] += t["banks"] if tier == "High" else t.get("banks_low", 0)

        if d < pol["furn"]:
            fu = 0 if (furn_cull_m is not None and d >= furn_cull_m + MARGIN_M) else t.get("furniture", 0)
            pl_raw = t.get("plots", 0) if tier == "High" else t.get("plots_low", t.get("plots", 0))
            pl = 0 if (plots_cull_m is not None and d >= plots_cull_m + MARGIN_M) else pl_raw
            res["furniture"] += fu + pl + t.get("wires", 0)

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

        hlod_m = pol["forest_hlod_m"] if forest_hlod_m is None else forest_hlod_m
        for fc in ch.get("forest_cells", []):
            dfc = _bbox_dist(fc["bbox_local_m"], (px, py))
            if hlod_m < dfc < pol["forest_hlod_cull_m"]:
                res["forest_hlod"] += fc["tris"]

    t_legacy = qa_cat.get("trees_lod0", 0) + qa_cat.get("trees_lod1", 0) + qa_cat.get("trees_lod2", 0)
    if tree_card_scale is not None and tier == "High" and means is not None:
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


def parse_vqa_stats(path: Path) -> dict[str, dict[str, int]]:
    txt = path.read_text(encoding="utf-8")
    rx = re.compile(r"^([a-z0-9-]+): objects=\d+ drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=\d+ trisExact=(\d+)", re.M)
    rxi = re.compile(r"^\s+([a-z0-9-]+) instanced \(props\+trees\): draws (\d+), instances (\d+), .*trianglesExact (\d+)", re.M)
    out = {m.group(1): {"draws": int(m.group(2)), "shadow_draws": int(m.group(3)), "mesh": int(m.group(4)), "inst": 0, "inst_draws": 0, "instances": 0} for m in rx.finditer(txt)}
    for m in rxi.finditer(txt):
        if m.group(1) in out:
            out[m.group(1)]["inst_draws"] = int(m.group(2))
            out[m.group(1)]["instances"] = int(m.group(3))
            out[m.group(1)]["inst"] = int(m.group(4))
    return out


def analyze_prop_families(region: str, cam: dict[str, Any], tier: str) -> dict[str, Any] | None:
    """Read-only inspection of Data/raw/derived/<region>/world/instances_*.json to measure WorldPropTierPolicy impact."""
    wdir = REPO / "Data" / "raw" / "derived" / region / "world"
    if not wdir.exists():
        return None
    files = sorted(wdir.glob("instances_*.json"))
    if not files:
        return None
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen"))
    from roads import build_world as BW
    pm_path = BW.props_meta_path(region, wdir)
    if not pm_path.exists():
        return None
    pm = {**json.loads(pm_path.read_text(encoding="utf-8"))["prototypes"], **BW.FD.prototype_stats()}
    px, py = cam["pos"][0], cam["pos"][1]
    lx, ly = _look(cam)
    bias = 1.5 if tier == "High" else 0.5
    families: dict[str, dict[str, int]] = {}
    for f in files:
        for it in json.loads(f.read_text(encoding="utf-8"))["instances"]:
            p = it["p"]
            if p.startswith("tree_"):
                continue
            d = math.hypot(it["e"] - px, it["n"] - py)
            if d > 1600.0 or (d > 200.0 and ((it["e"] - px) * lx + (it["n"] - py) * ly) / max(d, 1e-9) < 0.5):
                continue
            meta = pm.get(p) or {}
            rule = BW.instance_rule(p, 3 if "tris_lod2" in meta else 2, bias)
            key = next((k for lim, k in rule if d < lim), None)
            if not key:
                continue
            tris = int(meta.get(key, meta.get("tris_lod1", 0)))
            fam = p.split("_", 1)[0]
            slot = families.setdefault(fam, {"count": 0, "tris": 0, "tris_pc_low_cull": 0})
            slot["count"] += 1
            slot["tris"] += tris
            if p.startswith(("car_", "van_", "tractor_", "trailer_", "contact_")) and d >= 150.0:
                slot["tris_pc_low_cull"] += tris
            elif p.startswith("fab_") and d >= 50.0:
                slot["tris_pc_low_cull"] += tris
    return families


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", default="regen-wave-14-s25")
    ap.add_argument("--base-ref", default="main")
    ap.add_argument("--json", type=Path)
    ap.add_argument("--extra-report", action="store_true", help="Print calibration, build#10, prop families, variants B & C")
    args = ap.parse_args()

    ref_sha = subprocess.check_output(["git", "rev-parse", "--short", args.ref], cwd=REPO, text=True).strip()
    regions = list_regions_in_ref(args.ref)
    rebuilt = changed_regions(args.base_ref, args.ref)
    means = tree_means()

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
    by_region: dict[str, Any] = {}
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

        rt_vqa_h = runtime_estimate(wm, ff, cam_h, worst_h["by_category_high"], worst_h["by_category_low"], PROFILES["vqa_high"], means)
        rt_pc_h = runtime_estimate(wm, ff, cam_h, worst_h["by_category_high"], worst_h["by_category_low"], PROFILES["pc_high"], means)
        rt_vqa_l = runtime_estimate(wm, ff, cam_l, worst_l["by_category_high"], worst_l["by_category_low"], PROFILES["vqa_low"], means)
        rt_pc_l = runtime_estimate(wm, ff, cam_l, worst_l["by_category_high"], worst_l["by_category_low"], PROFILES["pc_low"], means)

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

        # Legacy Variant B
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
            # Runtime PC High & Low combined reductions
            "rt_pc_high_base": rt_pc_h["total"],
            "rt_pc_high_B": runtime_estimate(
                wm, ff, cam_h, worst_h["by_category_high"], worst_h["by_category_low"], PROFILES["pc_high"], means,
                bld_lod0_m=200.0, bld_lod0b_ratio=0.60, bld_hlod_from_m=700.0, bld_hlod_ratio=0.30,
                plots_cull_m=200.0, furn_cull_m=300.0, markings_cull_m=300.0, terrain_lod0_m=150.0,
                tree_scale=0.70, props_scale=0.85, hlod_m_override=80.0,
            )["total"],
            "rt_pc_low_base": rt_pc_l["total"],
            "rt_pc_low_B": runtime_estimate(
                wm, ff, cam_l, worst_l["by_category_high"], worst_l["by_category_low"], PROFILES["pc_low"], means,
                bld_hlod_from_m=500.0, bld_hlod_ratio=0.30,
                plots_cull_m=120.0, furn_cull_m=200.0, markings_cull_m=200.0, paved_cull_m=400.0,
                terrain_lod1_m=150.0, tree_scale=0.75, props_scale=0.75,
            )["total"],
        }

        rec = {
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
        }
        records.append(rec)
        by_region[r] = (rec, wm, cc, ff, sq)

    over_h = sorted([x for x in records if x["worst_high"]["tris"] > 2_000_000], key=lambda x: -x["worst_high"]["tris"])
    over_l = sorted([x for x in records if x["worst_low"]["tris"] > 600_000], key=lambda x: -x["worst_low"]["tris"])
    c_rec = by_region["bialystok-industrial-c"][0]

    if args.extra_report:
        print(f"=== WAVE 14 REF {args.ref} ({ref_sha}) | {len(records)} regions ===")

        print("\n--- 1. VARIANT B (LEGACY & RUNTIME PC) ON 8 HIGH > 2M + C ---")
        for x in [*over_h, c_rec]:
            v = x["variant_b"]
            print(
                f"{x['region']:22s} base={v['base_high']:9,d} | "
                f"B0(tc0.5)={v['B0_tree_card_05_high']:9,d} B1(bld)={v['B1_bld200_lod0b_hlod_high']:9,d} "
                f"B2(tre)={v['B2_trees_minus30_high']:9,d} B3(plt+frn)={v['B3_plots200_furn300_high']:9,d} "
                f"B4(mrk)={v['B4_markings300_high']:9,d} B5(trn)={v['B5_terrain150_high']:9,d} | "
                f"ALL={v['B_all_content_high']:9,d} ALL+tc0.5={v['B_all_plus_treecard05_high']:9,d} | "
                f"rtPC={v['rt_pc_high_base']:9,d}->{v['rt_pc_high_B']:9,d}"
            )

        print("\n--- 2. VARIANT B ON TOP 5 LOW (+ C) ---")
        for x in [*over_l[:5], c_rec]:
            v = x["variant_b"]
            print(
                f"{x['region']:22s} baseL={v['base_low']:9,d} | "
                f"B1(hlod)={v['B1_bld_hlod500_low']:9,d} B3(plt+frn)={v['B3_plots120_furn200_low']:9,d} "
                f"B4(mrk+pvd)={v['B4_mark200_paved400_low']:9,d} B5(trn)={v['B5_terrain_lod2_150_low']:9,d} | "
                f"ALL_L={v['B_all_low']:9,d} | rtPCL={v['rt_pc_low_base']:9,d}->{v['rt_pc_low_B']:9,d}"
            )

        print("\n--- 3. CALIBRATION: C WAVE14 VQA BEFORE STATS.TXT ---")
        c_st_path = MAIN_REPO / "artifacts/regen-wave-14-s24/vqa/before/bialystok-industrial-c/High-clear/stats.txt"
        if c_st_path.exists():
            st = parse_vqa_stats(c_st_path)
            _, wm, cc, ff, sq = by_region["bialystok-industrial-c"]
            cams = {c["id"]: c for c in cc["cameras"] if c["type"] == "persp"}
            for f in sq["mesh_budget"]["frame_estimate"]:
                cid = f["camera"]
                u = st.get(cid.replace("_", "-"))
                if not u or cid not in cams:
                    continue
                rt_v = runtime_estimate(wm, ff, cams[cid], f["by_category_high"], f["by_category_low"], PROFILES["vqa_high"], means)
                utot = u["mesh"] + u["inst"]
                print(
                    f"  {cid:28s} leg={f['tris_high']:9,d} rt_vqa={rt_v['total']:9,d} "
                    f"unity={utot:9,d} (mesh={u['mesh']:,d} inst={u['inst']:,d}) "
                    f"U/leg={utot/f['tris_high']:.2f} U/rt={utot/rt_v['total']:.2f} drawsEst={u['draws']+u['inst_draws']}"
                )

        print("\n--- 4. BUILD #10 PC-METRICS & SWEEP D83 ---")
        for p in sorted((MAIN_REPO / "artifacts/full-build-10-s24/evidence").glob("pc-*/pc-report.json")):
            d = json.loads(p.read_text(encoding="utf-8"))
            m = d["metrics"]
            print(
                f"  {p.parent.name:18s} build={d['run']['buildLabel']:18s} tier={d['display']['qualityName']:5s} "
                f"gpu={d['system']['gpu']} f_p95={m['frame_ms']['p95']:.2f}ms "
                f"cpu_p95={m['cpu_main_ms']['p95']:.2f}ms gpu_p95={m['gpu_ms']['p95']:.2f}ms "
                f"dc_p95={m['draw_calls']['p95']:.0f} tris_p95={m['tris']['p95']:,.0f}"
            )
        # Also knyszyn-w and dk65-07 in wave 14 frame_estimate / rt_pc
        for rn in ("knyszyn-w", "dk65-07"):
            rx = by_region[rn][0]
            print(
                f"  wave14 {rn:14s} max_leg_H={rx['worst_high']['tris']:,d} ({rx['worst_high']['camera']}) "
                f"max_rt_pc_H={rx['max_rt_pc_high']['tris']:,d} ({rx['max_rt_pc_high']['camera']})"
            )

        print("\n--- 5. PROPS FAMILY BREAKDOWN (Data/raw/derived read-only, worst High cam) ---")
        for x in [*over_h[:4], c_rec]:
            cam_h = {c["id"]: c for c in by_region[x["region"]][2]["cameras"]}[x["worst_high"]["camera"]]
            fams = analyze_prop_families(x["region"], cam_h, "High")
            if fams:
                tot_p = sum(v["tris"] for v in fams.values())
                top_f = sorted(fams.items(), key=lambda kv: -kv[1]["tris"])[:6]
                summary = ", ".join(f"{k}:{v['tris']:,d}({v['count']})" for k, v in top_f)
                print(f"  {x['region']:22s} sum={tot_p:7,d} (qa={x['worst_high']['by_category']['props']:7,d}) | {summary}")
            # Also Low cull check
            cam_l = {c["id"]: c for c in by_region[x["region"]][2]["cameras"]}[x["worst_low"]["camera"]]
            fams_l = analyze_prop_families(x["region"], cam_l, "Low")
            if fams_l:
                tot_pl = sum(v["tris"] for v in fams_l.values())
                cull_pl = sum(v["tris_pc_low_cull"] for v in fams_l.values())
                print(f"    Low props sum={tot_pl:6,d} (qa={x['worst_low']['by_category']['props']:6,d}) | WorldPropTierPolicy cull={cull_pl:6,d} ({100*cull_pl/max(tot_pl,1):.1f}%)")

        print("\n--- 6. TILE TYPE DISTRIBUTION (ALL 54 WAVE14 TILES) ---")
        for tt in ("city_dense", "city_outer", "town", "rural_corridor"):
            grp = sorted([x for x in records if x["type"] == tt], key=lambda z: -z["worst_high"]["tris"])
            hs = [z["worst_high"]["tris"] for z in grp]
            ls = [z["worst_low"]["tris"] for z in grp]
            rths = [z["max_rt_pc_high"]["tris"] for z in grp]
            rtls = [z["max_rt_pc_low"]["tris"] for z in grp]
            print(
                f"  {tt:15s} n={len(grp):2d} blds={min(z['buildings_count'] for z in grp)}..{max(z['buildings_count'] for z in grp)} | "
                f"legH {min(hs):,d}..{max(hs):,d} (med {statistics.median(hs):,.0f}) | "
                f"legL {min(ls):,d}..{max(ls):,d} (med {statistics.median(ls):,.0f}) | "
                f"rtPCH max {max(rths):,d} | rtPCL max {max(rtls):,d}"
            )
            print("    tiles:", ", ".join(f"{z['region']}({z['worst_high']['tris']//1000}k/{z['worst_low']['tris']//1000}k)" for z in grp))

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


if __name__ == "__main__":
    main()
