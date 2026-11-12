"""World C v3.3 (ADR 0022): PBR texture sets wired to the manifest, power-line supports and the `wires` node, overlap
removal of markings, yard stand lines and gullies, resurfaced asphalt."""

from __future__ import annotations

import json

import numpy as np
import pytest

from conftest import REGION_DIR, REPO
from route_corridor import read_glb, node_triangles

GEN = REGION_DIR / "generated"
WORLD = REPO / "Data" / "raw" / "derived" / "bialystok-industrial-c" / "world"
SPEC = REPO / "art-source" / "world" / "materials" / "materials_spec.json"
LUM = np.array([0.2126, 0.7152, 0.0722])


@pytest.fixture(scope="module")
def manifest():
    return json.loads((GEN / "world_manifest.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def spec():
    return json.loads(SPEC.read_text(encoding="utf-8"))["sets"]


@pytest.fixture(scope="module")
def sqa():
    return json.loads((GEN / "streetscape_qa.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rqa():
    return json.loads((GEN / "roads_qa.json").read_text(encoding="utf-8"))


def test_ground_materials_use_spec_sets(manifest, spec):
    """Every carriageway / yard / verge material names a generated set; calibrated sets have the set's mean albedo as
    manifest colour (engine tint ~1, ADR 0022)."""
    for mid in ("road_asphalt", "road_asphalt_new", "road_concrete", "curb_concrete", "sidewalk_paving",
                "verge_grass", "terrain_grass", "yard_asphalt", "yard_concrete", "yard_behaton", "yard_paving",
                "yard_slabs", "yard_gravel", "decal_patch", "decal_oil"):
        m = manifest["materials"][mid]
        assert m.get("texture_set") in spec, mid
        s = spec[m["texture_set"]]
        if s["kind"] == "tiling_set":
            lum = float(np.dot(m["color"], LUM))
            assert abs(lum / s["albedo"]["mean_lum_linear"] - 1.0) < 0.15, (mid, lum, s["albedo"]["mean_lum_linear"])
    assert manifest["materials"]["road_concrete"].get("uv1") == "along_m"


def test_facade_sets_are_modulation_maps(manifest, spec):
    used = {m.get("texture_set") for m in manifest["materials"].values()}
    for name in ("sandwich_ribbed", "trapezoid_sheet", "concrete_precast", "sectional_door", "plaster",
                 "large_panel_joints", "brick", "curtain_folds", "container_corrugation"):
        assert name in used, name
        s = spec[name]
        assert s["kind"] == "modulation_set" and s["uv"].startswith("mesh_uv0")
        assert abs(s["albedo"]["mean_lum_linear"] - 0.5) < 0.01


def test_resurfaced_share(manifest):
    mats = [set(ch["materials"]) for ch in manifest["chunks"]]
    assert any("road_asphalt_new" in m for m in mats)
    assert sum("road_asphalt" in m for m in mats) > sum("road_asphalt_new" in m for m in mats)


def test_power_lines_have_supports(sqa):
    """REVIEW r4 W-H2: every angle point of a BDOT10k power line carries a pole / tower (or the span runs past a
    carriageway); conductors live in their own `wires` node."""
    f = sqa["furniture"]
    assert f.get("power_supports_added", 0) > 0
    if not WORLD.exists() or not list(WORLD.glob("instances_*.json")):
        pytest.skip("world instances not built (Data/raw is gitignored)")
    src = json.loads((GEN / "streetscape_sources.json").read_text(encoding="utf-8"))
    import yaml
    reg = yaml.safe_load((REGION_DIR / "region.yaml").read_text(encoding="utf-8"))
    o = np.array([reg["origin"]["x"], reg["origin"]["y"]])
    poles = []
    for p in WORLD.glob("instances_*.json"):
        for it in json.loads(p.read_text(encoding="utf-8"))["instances"]:
            if it["p"] in ("power_pole", "pylon"):
                poles.append((it["e"], it["n"]))
    P = np.array(poles)
    total = far = 0
    for ln in src["bdot10k"]["OT_SULN_L"]:
        for q in np.asarray(ln["geometry"]["coordinates"], float) - o:
            total += 1
            far += np.min(np.hypot(*(P - q).T)) > 15.0
    assert far <= 0.1 * total, (far, total)       # the rest are angle points on a carriageway


def test_wires_node_separate_from_furniture():
    files = sorted(WORLD.glob("chunk_*.low.glb")) if WORLD.exists() else []
    if not files:
        pytest.skip("world chunks not built")
    n_wires = 0
    for f in files:
        doc, data, off = read_glb(f)
        names = {n["name"] for n in doc["nodes"]}
        if "wires" in names:
            n_wires += 1
            prims = [p for n in doc["nodes"] if n["name"] == "wires" for p in doc["meshes"][n["mesh"]]["primitives"]]
            assert all("COLOR_0" in p["attributes"] and "TEXCOORD_0" in p["attributes"] for p in prims)
        assert "wire" not in node_triangles(doc, data, off, "furniture")
    assert n_wires > 0


def test_markings_overlaps_removed_and_drains(rqa, sqa):
    s = rqa["summary"]
    assert s.get("markings_overlap_removed_tris", 0) > 0
    assert s["decals"].get("gullies", 0) > 100
    life = sqa["furniture"]["life"]
    assert life.get("stall_lines", 0) > 50
    assert life.get("yard_drains", 0) > 50


def test_lod1_window_zone_follows_accent_bands():
    """REVIEW r4 W-H4: banded insulated blocks have accent window rows on LOD0; LOD1 (Low/Medium, far on High) must
    draw the window zone in the same accent colour, not the base wall."""
    from streetscape import facade_kit as FK
    from streetscape.materials import M
    for a in FK.ACCENT_PLASTER:
        assert f"{a}__far_block" in M


def test_decals_face_up():
    """Every decal of the markings node faces up (a flipped strip is culled: the first stall lines were invisible)."""
    files = sorted(WORLD.glob("chunk_*.low.glb")) if WORLD.exists() else []
    if not files:
        pytest.skip("world chunks not built")
    for f in files:
        doc, data, off = read_glb(f)
        for mat, T in node_triangles(doc, data, off, "markings").items():
            n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
            big = np.linalg.norm(n, axis=1) > 1e-6
            assert (n[big, 2] > 0).mean() > 0.995, (f.name, mat, float((n[big, 2] > 0).mean()))
