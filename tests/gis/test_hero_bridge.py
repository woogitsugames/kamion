"""Hero viaduct at Rondo Bieżeństwa (override kind: hero_bridge, ADR 0067).

Checks the versioned outputs of the last generator run (spec, asset meta, QA, manifest), like the other world tests:
the override survives a regeneration only when the asset was built from exactly the current spec.
"""
import hashlib
import json
import struct
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
REGION = "bialystok-industrial-c"
GEN = REPO / "Data" / "Regions" / REGION / "generated"
ASSET = "viaduct_biezenstwa"
ADIR = REPO / "art-source" / "world" / "landmarks" / ASSET
OID = "andersa-viaduct-biezenstwa-hero"


def _json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def spec():
    return _json(GEN / "landmarks" / f"{ASSET}.spec.json")


@pytest.fixture(scope="module")
def meta():
    return _json(ADIR / f"{ASSET}_meta.json")


@pytest.fixture(scope="module")
def qa():
    return _json(GEN / "streetscape_qa.json")


def test_asset_matches_spec(spec, meta):
    assert meta["spec_sha256"] == _sha(spec), "asset is stale: rerun tools/blender/world/landmarks/make_viaduct.py"
    glb = (ADIR / f"{ASSET}.glb").read_bytes()
    assert meta["glb_sha256"] == hashlib.sha256(glb).hexdigest()


def test_override_applied_not_stale(qa):
    hb = qa["hero_bridges"]
    assert [a["id"] for a in hb["applied"]] == [OID], hb
    assert hb["stale"] == []
    man = _json(GEN / "world_manifest.json")
    assert OID in [o["id"] for o in man["overrides_applied"]]
    assert OID not in man["overrides_stale"]
    a = hb["applied"][0]
    assert a["generic_tris_removed"]["parapet"] > 10000 and a["generic_tris_removed"]["soffit"] > 0
    assert a["collision_boxes"] >= 2 * a["pier_lines"] * 2


def test_spec_follows_the_generated_road(spec):
    assert spec["osm_ways"] == ["175157461", "177895177"]
    assert len(spec["decks"]) == 2
    for dk in spec["decks"]:
        so = dk["s_open"]
        assert 150.0 < so[1] - so[0] < 260.0, so                      # part on piers (WORLD_GENERATION.md, mosty)
        ss = [s["s"] for s in dk["stations"]]
        assert ss == sorted(ss) and max(b - a for a, b in zip(ss, ss[1:])) <= spec["params"]["station_step_m"] * 1.25  # chain vertices are kept, measured max 4.565 m
        for s in dk["stations"][1:-1]:                                 # chain end stations taper to the road (9.95 m)
            w = ((s["l"][0] - s["r"][0]) ** 2 + (s["l"][1] - s["r"][1]) ** 2) ** 0.5
            assert 11.0 < w < 11.6, w                                  # 8.0 m carriageway + 2 x (0.15 + 1.50) m
            if s["open"] and so[0] + 45 < s["s"] < so[1] - 45:
                # middle of the open range (ring + island); the ends run down to the abutments. Measured 3.27-4.99 m:
                # 4.5 m + margin over the ring carriageways, less over the island mound of the generated terrain.
                low = min(s["l"][2], s["r"][2]) - spec["params"]["girder_depth_m"]
                assert low - max(s["zc"], s["zl"], s["zr"]) > 3.0, s
        assert 5 <= len(dk["piers"]) <= 9
        gaps = [b["s"] - a["s"] for a, b in zip(dk["piers"], dk["piers"][1:])]
        assert all(8.0 <= g <= 46.0 for g in gaps), gaps
        for p in dk["piers"]:
            assert all(p["top"] - c[2] > 2.0 for c in p["cols"])


def test_asset_lods_and_budget(meta, qa):
    t0, t1, t2 = meta["tris_total"]
    assert t0 > t1 > t2 > 0
    assert t1 <= 0.6 * t0 and t2 <= 0.25 * t0
    assert meta["materials"] == ["viaduct_concrete", "viaduct_steel"]
    removed = sum(qa["hero_bridges"]["applied"][0]["generic_tris_removed"].values())
    assert t0 <= removed + 2400, (t0, removed)          # never more triangles than the dressing it replaces (+ headroom)
    fr = {f["camera"]: f for f in qa["mesh_budget"]["frame_estimate"]}
    assert fr["stretch_04"]["tris_high"] <= 2_000_000, fr["stretch_04"]
    for s in meta["segments"]:
        assert s["name"].startswith("landmark_viaduct_biezenstwa_") and len(s["tris"]) == 3


def test_glb_nodes(meta):
    data = (ADIR / f"{ASSET}.glb").read_bytes()
    magic, _, _ = struct.unpack_from("<III", data, 0)
    assert magic == 0x46546C67
    n, _ = struct.unpack_from("<II", data, 12)
    doc = json.loads(data[20:20 + n])
    names = {nd["name"] for nd in doc["nodes"]}
    for s in meta["segments"]:
        assert {s["name"], s["name"] + ".lod1", s["name"] + ".lod2"} <= names
    assert f"{ASSET}.collision" in names
    assert not any(nm.endswith(".col") for nm in names)      # InstanceImporter would box it across the road
    assert {m["name"] for m in doc["materials"]} == {"viaduct_concrete", "viaduct_steel"}
    assert not doc.get("images")                             # material names only: textures come from the sets


def test_instances_emitted(meta):
    world = REPO / "Data" / "raw" / "derived" / REGION / "world"
    if not world.exists():
        pytest.skip("world chunks not generated here")
    found = {}
    for f in world.glob("instances_*.json"):
        for it in _json(f)["instances"]:
            if it["p"].startswith("landmark_viaduct_biezenstwa_"):
                found[it["p"]] = it
    assert set(found) == {s["name"] for s in meta["segments"]}
    for s in meta["segments"]:
        it = found[s["name"]]
        assert [it["e"], it["n"], it["z"]] == pytest.approx(s["anchor"], abs=2e-3) and it["yaw"] == 0.0


def test_materials_and_island(qa):
    man = _json(GEN / "world_manifest.json")
    m = man["materials"]
    assert m["viaduct_concrete"]["texture_set"] == "viaduct_concrete"
    assert m["viaduct_steel"]["texture"] == "viaduct_steel" and m["viaduct_steel"]["alpha_cutoff"] == 0.5
    sets = _json(REPO / "art-source" / "world" / "materials" / "materials_spec.json")["sets"]
    vc = sets["viaduct_concrete"]
    assert vc["uv"].startswith("mesh_uv0_metres") and vc["kind"] == "tiling_set"
    assert m["viaduct_concrete"]["color"] == pytest.approx(vc["albedo"]["mean_rgb_linear"], abs=2e-3)   # tint 1
    lum = sum(a * b for a, b in zip(vc["concrete_mean_rgb_linear"], (0.2126, 0.7152, 0.0722)))
    assert 0.30 <= lum <= 0.42, lum
    isl = [i for i in qa["plantings"]["islands"] if i["id"].endswith("island1") and i["fill"] == "gravel"]
    assert isl, qa["plantings"]["islands"]
