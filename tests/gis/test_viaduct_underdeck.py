"""ADR 0105: structural dressing must preserve deck ownership and clearance."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

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
    spec = dict(params=prm, stairs=[[[0., 6.3, 3.]], [[16., 6.3, 3.]]],
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
    old = [(p, p.V.copy(), p.T.copy(), p.UV.copy()) for p in w.buf.parts if not p.src.endswith(":soffit")]
    H._apply_underdeck(w, hero)
    for p, v, t, uv in old:
        assert any(part is p for part in w.buf.parts)
        np.testing.assert_array_equal(p.V, v)
        np.testing.assert_array_equal(p.T, t)
        np.testing.assert_array_equal(p.UV, uv)
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
