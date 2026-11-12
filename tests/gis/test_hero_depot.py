"""ADR 0071: hero depot hall (override kind `hero_depot`, streetscape.hero_depot, tools/blender/world/landmarks/make_depot.py).

Unit tests run on a synthetic footprint; the region tests need the committed spec / asset of Kwadrat Park.
Run: uv run --project tools/worldgen pytest tests/gis/test_hero_depot.py -q
"""

from __future__ import annotations

import hashlib
import json
import struct

import numpy as np
import pytest
from shapely.geometry import Polygon

from conftest import REGION_DIR, REPO, require_lfs

from roads import standards as S
from streetscape import hero_depot as HD
from streetscape import materials as MAT

ASSET = "kwadrat_park"
SPEC = REGION_DIR / "generated" / "landmarks" / f"{ASSET}.spec.json"
META = REPO / "art-source" / "world" / "landmarks" / ASSET / f"{ASSET}_meta.json"
GLB = REPO / "art-source" / "world" / "landmarks" / ASSET / f"{ASSET}.glb"

# LOD budgets of the whole hall (triangles). WORKING_VALUE: the generic hall it replaces drew ~19 k (LOD0) / 1.6 k (LOD1);
# Low shows LOD1 from 50 m (lodBias 0.5) and the silhouette from 200 m.
BUDGET = (60000, 6000, 1200)


def _synthetic():
    # 80 x 40 m hall, long south edge on y = 0, a 6 x 2.5 m protrusion on the south edge at x = 50..56
    ring = [(0, 0), (50, 0), (50, -2.5), (56, -2.5), (56, 0), (80, 0), (80, 40), (0, 40)]
    bld = {"id": "b1", "poly": Polygon(ring), "props": {"height_m": 10.0}, "ovr": {}}
    o = {"id": "h1", "kind": "hero_depot", "asset": "t", "building": "b1",
         "facades": [{"name": "S", "at": [40.0, 0.0], "tol_m": 5.0,
                      "docks": {"count": 8, "centre_on_len_m": 50.0}, "strips": [{"u0_m": 2.0, "u1_m": 48.0}],
                      "doors": [{"u_m": 60.0}]}],
         "annexes": [{"name": "v", "at": [53.0, -2.5], "h_m": 3.4, "style": "accent"}]}
    return o, bld


def _flat(e, n):
    return np.full(np.shape(e), 100.0)


def test_spec_annex_split_and_dock_rule():
    o, bld = _synthetic()
    spec, stale = HD.build_spec(o, bld, _flat, np.zeros(2))
    assert stale == []
    assert len(spec["ring"]) == 4, "the protrusion is split off the main wall ring"
    ax = spec["annexes"][0]
    e = spec["edges"][ax["edge"]]
    assert e["name"] == "S" and abs(e["L"] - 80.0) < 1e-6
    assert ax["u"] == [50.0, 56.0] and abs(ax["depth_m"] - 2.5) < 1e-6
    dk = e["features"]["docks"]
    # the rule of buildings_mesh.docks_for on the original 50 m edge: centred, pitch DOCK_PITCH
    assert abs(dk["first_u_m"] - (50.0 - 7 * S.DOCK_PITCH) / 2) < 1e-6
    assert abs(dk["yard_z"] - 100.0) < 1e-6
    rows = HD.dock_rows(spec)
    assert len(rows) == 1 and len(rows[0]["docks"]) == 8
    assert {"id", "edge", "docks", "yard_z", "apron"} <= set(rows[0])
    assert [d["num"] for d in rows[0]["docks"]] == list(range(1, 9))
    assert rows[0]["apron"].area == pytest.approx((7 * S.DOCK_PITCH + 5.0) * S.DOCK_APRON_L)


def test_segments_cover_edges_and_avoid_openings():
    o, bld = _synthetic()
    spec, _ = HD.build_spec(o, bld, _flat, np.zeros(2))
    prm = spec["params"]
    for e in spec["edges"]:
        segs = sorted((s for s in spec["segments"] if s["edge"] == e["i"]), key=lambda s: s["u"][0])
        assert segs[0]["u"][0] == 0.0 and abs(segs[-1]["u"][1] - e["L"]) < 1e-6
        for a, b in zip(segs[:-1], segs[1:]):
            assert a["u"][1] == b["u"][0]
        assert max(s["u"][1] - s["u"][0] for s in segs) <= prm["segment_max_m"] + 8.0
        busy = HD._busy(e, spec["annexes"], prm)
        for s in segs[:-1]:
            assert all(not (b0 < s["u"][1] < b1) for b0, b1 in busy), "a segment cut runs through a dock / door / annex"


def test_spec_is_deterministic_and_stale_features_are_reported():
    o, bld = _synthetic()
    a, _ = HD.build_spec(o, bld, _flat, np.zeros(2))
    b, _ = HD.build_spec(o, bld, _flat, np.zeros(2))
    assert HD._sha(a) == HD._sha(b)
    assert HD._sha(json.loads(json.dumps(a))) == HD._sha(a), "sha survives the JSON round trip (Blender reads the file)"
    o["facades"].append({"name": "nowhere", "at": [500.0, 500.0]})
    o["annexes"].append({"name": "ghost", "at": [10.0, 60.0]})
    _, stale = HD.build_spec(o, bld, _flat, np.zeros(2))
    assert set(stale) == {"facade:nowhere", "annex:ghost"}


# ------------------------------------------------------------------------------------------- region asset
@pytest.fixture(scope="module")
def spec():
    if not SPEC.exists():
        pytest.skip("hero depot spec not generated")
    return json.loads(SPEC.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def meta():
    if not (META.exists() and GLB.exists()):
        pytest.skip("hero depot asset not built")
    require_lfs(GLB)
    return json.loads(META.read_text(encoding="utf-8"))


def test_kwadrat_docks_keep_the_generic_positions(spec):
    """The dock row must not move (ADR 0071): 11 docks, standard pitch / floor height, first door where the generic rule
    put it on the first SE footprint edge (55.63 m): u0 = (55.63 - 10 * 4.0) / 2."""
    rows = [e for e in spec["edges"] if "docks" in e["features"]]
    assert len(rows) == 1 and rows[0]["name"] == "SE-yard"
    dk = rows[0]["features"]["docks"]
    assert dk["count"] == 11 and dk["pitch_m"] == S.DOCK_PITCH
    assert abs(dk["first_u_m"] - 7.815) < 0.02
    assert spec["params"]["dock_floor_h_m"] == S.DOCK_FLOOR_H == 1.20
    assert spec["params"]["dock_door_w_m"] == S.DOCK_DOOR_W
    g = [z for _, z in rows[0]["ground"] if _ <= 60.0]
    assert max(g) - min(g) < 0.30, "yard along the dock row is level within 0.3 m (trailer bed vs dock floor)"


def test_kwadrat_asset_matches_spec_and_budget(spec, meta):
    assert meta["spec_sha256"] == HD._sha(spec), "asset built from another spec: rerun make_depot.py"
    assert meta["glb_sha256"] == hashlib.sha256(GLB.read_bytes()).hexdigest()
    tot = meta["tris_total"]
    assert tot[0] > tot[1] > tot[2] > 0
    for k in range(3):
        assert tot[k] <= BUDGET[k], f"LOD{k} {tot[k]} triangles over the budget {BUDGET[k]}"
    assert len(meta["segments"]) == len(spec["segments"]) + 1          # + roof
    for s in meta["segments"]:
        assert s["name"].startswith(HD.PROTO_PREFIX)
        assert s["tris"][0] >= s["tris"][1] >= s["tris"][2] > 0
    unknown = [m for m in meta["materials"] if m not in MAT.M]
    assert not unknown, f"materials without a world definition: {unknown}"


def test_kwadrat_glb_has_all_lod_nodes(meta):
    raw = GLB.read_bytes()
    assert raw[:4] == b"glTF"
    n = struct.unpack_from("<I", raw, 12)[0]
    doc = json.loads(raw[20:20 + n].decode("utf-8"))
    names = {nd["name"] for nd in doc["nodes"]}
    for s in meta["segments"]:
        for suf in ("", ".lod1", ".lod2"):
            assert s["name"] + suf in names
    assert {m["name"] for m in doc["materials"]} == set(meta["materials"])


def test_instance_policy_in_sync():
    """build_world.instance_ends (frame estimate) and InstanceImporter.Policy (engine) use the same LOD ends."""
    from roads import build_world as BW
    ends, _ = BW.instance_ends("landmark_depot_kwadrat_park_04", 3)
    assert list(ends) == HD.DEFAULTS["lod_ends_m"]
    cs = (REPO / "game/Assets/_Project/World/Import/InstanceImporter.cs").read_text(encoding="utf-8")
    assert 'proto.StartsWith("landmark_depot")) e = new[] { 100f, 400f, 20000f }' in cs
