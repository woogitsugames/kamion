"""ADR 0282 (D28): dense-tile LOD budget estimate - prototype tool tools/worldgen/qa/dense_lod_estimate.py.
Data in git only (generated/* of the 4 dense tiles read, never written; no Data/raw, no Unity): the legacy model
reproduces build_world.mesh_budget exactly, the runtime model mirrors the Unity LOD table, proposals never add
triangles, the merged one-LODGroup table selects the same layers as the per-layer rules, the block HLOD rule merges
equal-height neighbours only, the visual-QA SceneStats calibration in git stays below the legacy estimate."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
from shapely.geometry import box

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
import dense_lod_estimate as D  # noqa: E402

REGIONS = [r for r in D.DENSE if (D.REGIONS / r / "generated" / "world_manifest.json").exists()]


@pytest.fixture(scope="module", params=REGIONS)
def reg(request):
    return D.load_region(request.param)


def test_legacy_model_reproduces_stored_frame_estimate(reg):
    assert reg["cameras"]
    for cam in reg["cameras"]:
        got = D.legacy_chunk_categories(reg["manifest"], cam)
        fe = reg["frame_estimate"][cam["id"]]["by_category_high"]
        for k in D.CHUNK_CATEGORIES:
            assert got[k] == fe.get(k, 0), (reg["id"], cam["id"], k, got[k], fe.get(k, 0))


def test_lod_ends_mirror_world_scene_builder():
    # WorldSceneBuilder: H(switch + 0.7 chunk) with tan 30; High lodBias 1.5, camera fov 60 -> x 1.5
    ends = D.lod_ends([0, 120, 300, 700], 256, 1.5, 60.0)
    assert ends == pytest.approx([448.8, 718.8, 1318.8])
    # a narrower camera keeps LODs longer (same screen height)
    assert D.lod_ends([0, 120, 300, 700], 256, 1.5, 40.0)[0] > ends[0]
    assert len(D.HIGH_LODS) == 4 and "buildings" in D.HIGH_LODS[0] and "buildings_lod1" in D.HIGH_LODS[3]


def test_frustum_test():
    cam = {"pos": [0.0, 0.0, 100.0], "look_at": [100.0, 0.0, 100.0], "fov_deg": 60.0}
    hf = D.hfov_deg(60.0, D.QA_ASPECT)
    assert 100 < hf < 106                                                   # 2340 x 1080 runner
    b = lambda e0, n0: {"e_min": e0, "e_max": e0 + 256, "n_min": n0, "n_max": n0 + 256}  # noqa: E731
    assert D.chunk_in_frustum(b(-128, -128), cam, hf, 2500)               # camera inside
    assert D.chunk_in_frustum(b(300, -128), cam, hf, 2500)                # ahead
    assert not D.chunk_in_frustum(b(-600, -128), cam, hf, 2500)           # behind
    assert not D.chunk_in_frustum(b(3000, -128), cam, hf, 2500)           # beyond the far clip
    assert D.chunk_in_frustum(b(1000, 1000), cam, hf, 2500)               # 45 deg left, inside the 51 deg half-fov


def test_base_merged_table_is_the_unity_high_table():
    ends = D.lod_ends([0, 120, 300, 700], 256, 1.5, 60.0)
    table = D.merged_lod_table(ends, D.BASE)
    assert [round(e, 1) for e, _ in table[:-1]] == [round(e, 1) for e in ends] and table[-1][0] == D.INF
    for (_, layers), unity in zip(table, D.HIGH_LODS):
        assert set(layers) == set(unity)


def test_merged_table_selects_the_per_layer_rules():
    ends = D.lod_ends([0, 120, 300, 700], 256, 1.5, 60.0)
    prop = D.combined(*D.by_name(D.ALL_CHUNK))
    spans = D.layer_ends(ends, prop)
    table = D.merged_lod_table(ends, prop)
    assert len(table) > len(D.HIGH_LODS)                                  # extra levels for the per-layer distances
    for d in range(0, 2600, 7):
        layers = next(ls for e, ls in table if d < e)
        want = {n for n, (a, b) in spans.items() if a <= d < b}
        assert set(layers) == want, d
    # buildings: LOD0 -> LOD0b -> LOD1 -> HLOD in that order, no gap
    b = sorted((spans[n], n) for n in ("buildings", "buildings_lod0b", "buildings_lod1", "buildings_hlod"))
    assert [n for _, n in b] == ["buildings", "buildings_lod0b", "buildings_lod1", "buildings_hlod"]
    assert all(b[i][0][1] == b[i + 1][0][0] for i in range(3))


def test_proposals_never_add_triangles(reg):
    means = D.tree_means()
    allp = D.combined(*D.by_name(D.ALL_CHUNK))
    cells = D.combined(*D.by_name(D.ALL_CELLS))
    for cam in reg["cameras"]:
        base = D.camera_estimate(reg, cam, D.BASE, means=means)
        for p in (*D.PROPOSALS[1:], allp, cells):
            e = D.camera_estimate(reg, cam, p, means=means)
            for m in ("legacy", "runtime"):
                assert e[m]["total"] <= base[m]["total"], (reg["id"], cam["id"], p.name, m)


def test_runtime_trees_follow_the_tier_policy():
    means = {"tris_lod0": 2000.0, "tris_lod1": 500.0, "tris_lod2": 2.0}
    cam = {"fov_deg": 60.0}
    # 100 LOD0 trees within 35 m in the legacy disc -> runtime: LOD0 only within 10 m, frustum share ~0.29
    got = D.runtime_instances({"trees_lod0": 100 * 2000}, cam, D.Runtime(), D.BASE, means)
    f = D.hfov_deg(60.0, D.QA_ASPECT) / 360
    rho = 100 / (math.pi * 35 ** 2)
    assert got["trees"] == pytest.approx(f * rho * math.pi * (10 ** 2 * 2000 + (30 ** 2 - 10 ** 2) * 500))
    assert got["trees"] < 0.25 * 100 * 2000


def test_near_distance_rules_never_reach_closer_geometry():
    # a rule at near x applies only when the reference point is >= x + 0.7 cell away, i.e. no geometry nearer than x
    t = {"buildings": 1000, "buildings_lod1": 100}
    p = D.Proposal("t", bld_lod0_m=200)
    assert D._buildings(t, 200 + D.MARGIN - 1, 449, p) == 1000
    assert D._buildings(t, 200 + D.MARGIN, 449, p) == 100
    # building cells of 64 m: the cell under the camera stays LOD0 while the far cells of the same chunk drop
    b = {"e_min": 0, "e_max": 256, "n_min": 0, "n_max": 256}
    cells = D.Proposal("c", bld_cell_m=64, bld_lod0_m=60)
    n = D._buildings_chunk(t, b, (8, 8, None), 120, 449, cells)
    assert 100 < n < 1000 and n >= 1000 / 16


def test_block_hlod_rule_merges_equal_heights_only():
    a, b = box(0, 0, 10, 10), box(10, 0, 20, 10)                       # touching
    one = D.block_hlod_tris([(a, 12.0), (b, 12.5)])                    # same 3 m bin -> one prism
    assert one == 2 * 4 + 2                                            # 4 walls x 2 + roof 2
    two = D.block_hlod_tris([(a, 12.0), (b, 21.0)])                    # skyline step kept
    assert two == 2 * (2 * 4 + 2)
    assert D.block_hlod_tris([(box(0, 0, 0.5, 0.5), 6.0)]) == 0         # < 1 m2 dropped


def test_parse_stats_reads_mesh_and_instanced_lines():
    txt = ("tier=High lighting=clear msaa=2 renderScale=1\n"
           "route-s0159: objects=182 drawsEst=990 shadowDrawsEst=171 trisK=1036 trisExact=1036897 (estimate, before SRP batching)\n"
           "  route-s0159 instanced (props+trees): draws 77, instances 900, triangles 64k, cells 200, forest HLOD cells 12, trianglesExact 64674\n")
    st = D.parse_stats(txt)
    assert st["route-s0159"] == {"draws": 990, "mesh": 1036897, "inst": 64674, "inst_draws": 77}


@pytest.mark.parametrize("region", sorted(D.STATS))
def test_scene_stats_in_git_stay_below_both_estimates(region):
    path, aspect = D.STATS[region]
    if not (REPO / path).exists():
        pytest.skip(f"{path} not in this checkout")
    rows = D.calibration(region, path, aspect)
    assert len(rows) >= 3
    for r in rows:                         # SceneStats (Unity LOD + frustum) < runtime model < ~legacy (upper bounds)
        assert r["unity"] < r["runtime"] and r["unity"] < r["legacy"], r


def test_building_probe_on_a_slice_of_c():
    pr = D.building_probe("bialystok-industrial-c", limit=40)
    assert pr["errors"] == 0 and pr["lod0"] > pr["lod1"] > 0
    assert 0 < pr["lod0b_ratio"] <= pr["lod0b_ratio_min"] < 1
    assert 0 < pr["hlod_ratio"] < 1
