"""ADR 0105: structural dressing must preserve deck ownership and clearance."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from roads import meshing as M
from streetscape import hero_bridge as H

ROOT = Path(__file__).resolve().parents[2]


def fixture():
    cfg = json.loads((ROOT / "Data/Regions/bialystok-industrial-c/viaduct_underdeck.json").read_text(encoding="utf-8"))
    prm = {**H.DEFAULTS, **cfg["set"]}
    sts = []
    for s in (0., 8., 16.):
        sts.append(dict(s=s, t=[1., 0.], l=[s, 5.65, 10.], r=[s, -5.65, 10.],
                        lg=[s, 4., 9.77], rg=[s, -4., 9.77], c=[s, 0., 9.77],
                        open=True, zc=3., zl=3., zr=3.))
    spec = dict(params=prm, stairs=[[[0., 6.3, 3., 3.1]], [[16., 6.3, 3., 3.1]]],
                decks=[dict(stations=sts, s_open=[0., 16.], piers=[dict(s=8., top=8.8,
                cols=[[8., -2., 3.], [8., 2., 3.]])])])
    buf = M.MeshBuf()
    for src, mat in (("road", "road_asphalt"), ("screen", "noise_glass"),
                     ("parapet", "barrier_steel"), ("fascia", "bridge_fascia_green"), ("soffit", "bridge_soffit")):
        M.box(buf, "bridge", mat, [8, 0], [1, 0], 8, 5, 8.8, 10., "c:test:" + src)
    w = SimpleNamespace(buf=buf, stats={"hero_bridges": {"applied": [], "stale": []}})
    return w, dict(spec=spec, chains=[SimpleNamespace(id="c:test")], override=cfg)


def test_preserves_deck_barriers_and_screens_byte_for_byte():
    w, hero = fixture()
    for p in w.buf.parts:
        p.UV1 = np.arange(len(p.V) * 2).reshape(-1, 2) / 17
        p.COL = np.arange(len(p.V) * 4).reshape(-1, 4) / 37
    old = [(p, p.V.copy(), p.T.copy(), p.UV.copy(), p.UV1.copy(), p.COL.copy())
           for p in w.buf.parts if not p.src.endswith(":soffit")]
    H._apply_underdeck(w, hero)
    for p, v, t, uv, uv1, col in old:
        assert any(part is p for part in w.buf.parts)
        np.testing.assert_array_equal(p.V, v)
        np.testing.assert_array_equal(p.T, t)
        np.testing.assert_array_equal(p.UV, uv)
        np.testing.assert_array_equal(p.UV1, uv1)
        np.testing.assert_array_equal(p.COL, col)
    assert not any(p.src == "c:test:soffit" for p in w.buf.parts)


def test_underdeck_envelope_lod_batching_and_ground_contact():
    w, hero = fixture()
    H._apply_underdeck(w, hero)
    parts = [p for p in w.buf.parts if ":underdeck0105" in p.src]
    assert {p.mat for p in parts} <= {"bridge_concrete", "bridge_soffit", "pier_yellow", "collision_building"}
    for p in parts:
        assert np.isfinite(p.V).all() and np.isfinite(p.UV).all()
        assert p.T.min() >= 0 and p.T.max() < len(p.V)
        area = np.linalg.norm(np.cross(p.V[p.T[:, 1]] - p.V[p.T[:, 0]], p.V[p.T[:, 2]] - p.V[p.T[:, 0]]), axis=1)
        assert (area > 1e-6).all()
        if p.src.endswith((":girder", ":drip", ":collector")):
            assert p.V[:, 2].min() >= 8.8 - 1e-6, "must not reduce the old road clearance"
        if p.src.endswith(":column"):
            assert p.V[:, 2].min() == 2.5, "column embedded 0.5 m in surveyed ground"
        if p.src.endswith(":stairs"):
            assert p.V[:, 2].min() < 3 < p.V[:, 2].max()
    assert any(p.src.endswith(":bearing") for p in parts)
    assert any(p.src.endswith(":downpipe") for p in parts)
    assert any(p.src.endswith(":joint_runoff") for p in parts)
    assert w.stats["hero_bridges"]["applied"] == []  # existing ADR 0067 report contract


def test_all_underside_faces_point_out_of_the_box():
    w, hero = fixture()
    H._apply_underdeck(w, hero)
    for p in w.buf.parts:
        if not p.src.endswith((":girder", ":drip")):
            continue
        normals = np.cross(p.V[p.T[:, 1]] - p.V[p.T[:, 0]], p.V[p.T[:, 2]] - p.V[p.T[:, 0]])
        assert (normals[:, 2] <= 1e-8).all()


def test_chamfered_column_faces_point_outwards():
    buf = M.MeshBuf()
    H._prism(buf, [0, 0], [1, 0], .5, .6, .25, 0., 4., "bridge_concrete", "test")
    p = buf.parts[0]
    normals = np.cross(p.V[p.T[:, 1]] - p.V[p.T[:, 0]], p.V[p.T[:, 2]] - p.V[p.T[:, 0]])
    centres = p.V[p.T].mean(axis=1)
    assert ((normals[:, :2] * centres[:, :2]).sum(axis=1) >= 0).all()


def test_bare_chamfers_partition_existing_faces_without_changing_collision():
    old, new = M.MeshBuf(), M.MeshBuf()
    args = ([0, 0], [1, 0], .5, .6, .25, 0., 4., "pier_yellow", "column")
    H._prism(old, *args, collision=True)
    H._prism(new, *args, collision=True, bevel_mat="bridge_concrete")
    visual = [p for p in new.parts if p.layer == "bridge"]
    assert {p.mat for p in visual} == {"pier_yellow", "bridge_concrete"}
    assert sum(len(p.T) for p in visual) == len(old.parts[0].T)
    bare = next(p for p in visual if p.mat == "bridge_concrete")
    assert len(bare.T) == 8
    np.testing.assert_array_equal(bare.T, old.parts[0].T[[2, 3, 6, 7, 10, 11, 14, 15]])
    assert len([p for p in new.parts if p.layer == "collision"]) == 1
    for attr in ("V", "T", "UV"):
        np.testing.assert_array_equal(getattr(old.parts[-1], attr), getattr(new.parts[-1], attr))


@pytest.mark.parametrize("config_enabled,spec_enabled", [(False, True), (True, False), (False, False)])
def test_stale_stair_spec_cannot_override_disabled_current_config(config_enabled, spec_enabled):
    w, hero = fixture()
    hero["override"]["set"]["stairs_enabled"] = config_enabled
    hero["spec"]["params"]["stairs_enabled"] = spec_enabled
    assert any(hero["spec"]["stairs"]), "fixture must contain a stale stair flight"
    H._apply_underdeck(w, hero)
    assert not any(p.src.endswith(":stairs") for p in w.buf.parts)


def test_confirmed_stairs_require_both_flags():
    w, hero = fixture()
    hero["override"]["set"]["stairs_enabled"] = True
    hero["spec"]["params"]["stairs_enabled"] = True
    H._apply_underdeck(w, hero)
    assert any(p.src.endswith(":stairs") for p in w.buf.parts)


def test_pier_weather_coordinates_follow_ground_and_head_without_changing_collision():
    old, new = M.MeshBuf(), M.MeshBuf()
    args = ([8, -2], [1, 0], .5, .6, .25, 2.5, 8.8, "pier_yellow", "column")
    H._prism(old, *args, collision=True)
    H._prism(new, *args, collision=True, bevel_mat="bridge_concrete",
             paint_weather={"ground_z": 3., "runoff_scale": .35})
    painted = next(p for p in new.parts if p.mat == "pier_yellow")
    np.testing.assert_allclose(painted.UV[:, 1], painted.V[:, 2] - 3.)
    np.testing.assert_allclose(painted.UV1[:, 1], 1 + (8.8 - painted.V[:, 2]) / .35)
    assert painted.UV1[:, 1].max() < 48, "ordinary runoff must not enter reserved sill encodings"
    assert next(p for p in new.parts if p.mat == "bridge_concrete").UV1 is None
    for attr in ("V", "T", "UV"):
        np.testing.assert_array_equal(getattr(old.parts[-1], attr), getattr(new.parts[-1], attr))


def test_weather_flag_replaces_geometric_column_streaks_only():
    w, hero = fixture()
    H._apply_underdeck(w, hero)
    assert not any(p.src.endswith(":runoff") for p in w.buf.parts)
    assert any(p.src.endswith(":joint_runoff") for p in w.buf.parts)
    assert any(p.UV1 is not None for p in w.buf.parts if p.mat == "pier_yellow")
    w, hero = fixture()
    hero["override"]["set"]["paint_weathering"] = False
    H._apply_underdeck(w, hero)
    assert any(p.src.endswith(":runoff") for p in w.buf.parts)


def test_vegetation_uses_only_an_existing_megascans_prototype():
    w, hero = fixture()
    hero["override"]["add_grass"] = True
    hero["spec"]["self_seeded_grass"] = [[0., 7., 3.]]
    instances = []
    H._apply_underdeck(w, hero, instances)
    assert instances == [], "no procedural substitute when the Fab prototype is unavailable"
    w, hero = fixture()
    hero["override"]["add_grass"] = True
    hero["spec"]["self_seeded_grass"] = [[0., 7., 3.]]
    instances = [dict(p="fab_grass_clumps")]
    H._apply_underdeck(w, hero, instances)
    assert len(instances) == 2
    assert instances[1]["p"] == "fab_grass_clumps" and instances[1]["z"] == 3.


def test_low_draw_budget_disables_additional_grass():
    w, hero = fixture()
    assert hero['override']['add_grass'] is False
    hero['spec']['self_seeded_grass'] = [[0., 7., 3.]]
    instances = [dict(p='fab_grass_clumps')]
    H._apply_underdeck(w, hero, instances)
    assert len(instances) == 1


def test_generated_specs_have_grounded_stair_flights_and_unchanged_decks():
    gen = ROOT / 'Data/Regions/bialystok-industrial-c/generated'
    specs = json.loads((gen / 'landmarks/viaduct_putry_underdeck.spec.json').read_text(encoding='utf-8'))
    qa = json.loads((gen / 'streetscape_qa.json').read_text(encoding='utf-8'))
    assert len(specs) == 2
    cfg = json.loads((ROOT / 'Data/Regions/bialystok-industrial-c/viaduct_underdeck.json').read_text(encoding='utf-8'))
    enabled = cfg['set']['stairs_enabled']
    flights = 0
    for spec in specs:
        assert spec['params']['stairs_enabled'] is enabled
        if not enabled:
            assert spec['stairs'] == [[], []]
        for steps in spec['stairs']:
            if not steps:  # a blocked landing must not create an unsupported flight
                continue
            flights += 1
            assert all(len(step) == 4 and step[3] > step[2] for step in steps)
            assert .079 <= steps[-1][3] - steps[-1][2] <= .301
            for a, b in zip(steps[:-1], steps[1:]):
                assert abs(a[3] - b[3] - spec['params']['stairs_rise_m']) < .002
    assert flights > 0 if enabled else flights == 0
    for report in qa['hero_bridges']['underdeck']:
        assert report['deck_before_sha256'] == report['deck_after_sha256']
        assert report['new_materials'] == []
