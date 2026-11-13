"""ADR 0180 (review REVIEW-2026-11-13-s17-0171 P1): authored office facades - building override `facades`
(frontage.facade_rules): the tower by the Kwadrat lane gets blank sand gables with one stair column of windows and
white long walls with one window band per storey; both LODs draw the same rectangles; no new material."""
import numpy as np
import pytest

from test_buildings_0167 import ORIGIN, REGION_DIR, TOWER, _build, _loaded

SW, SE = np.radians(208.3), np.radians(118.2)          # bearings of the tower's gable and long wall normals (BDOT10k)


def _tris(buf, layer, mat):
    return sum(len(p.T) for p in buf.parts if p.layer == layer and p.mat == mat)


def _on_wall(buf, layer, mat, bearing, depth_min):
    """Triangles (n, 3, 3) of a material lying on walls that look to the bearing, at least depth_min along it."""
    n = np.array([np.sin(bearing), np.cos(bearing)])
    out = []
    for p in buf.parts:
        if p.layer != layer or p.mat != mat:
            continue
        tri = p.V[p.T]
        nn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)
        out.append(tri[(nn[:, :2] @ n > 0.97) & ((tri[:, :, :2] @ n).min(1) > depth_min)])
    return np.concatenate(out) if out else np.zeros((0, 3, 3))


def _panes(tri, h):
    """Window panes among atlas triangles: those exactly h high (AC units, the door and sills use the atlas too)."""
    return tri[np.abs(np.ptp(tri[:, :, 2], axis=1) - h) < 1e-6]


def _rule(**kw):
    from streetscape import frontage as FR
    return FR.facade_rules([dict({"facing": "S"}, **kw)], "plaster_white")[0]


def test_rules_are_validated_and_optional():
    from streetscape import frontage as FR
    assert FR.facade_rules(None, "plaster_white") is None and FR.facade_rules([], "plaster_white") is None
    r = _rule(windows="ribbon")
    assert r["wall"] == "plaster_white" and r["far"] == "plaster_white__far_ribbon" and r["spans"] == [(0.0, 1.0)]
    assert _rule(windows="column", wall_material="plaster_beige")["far"] == "plaster_beige__far_office"
    assert _rule(windows="blank")["far"] is None
    for bad in ({"windows": "grid"}, {"facing": "up"}, {"windows": "ribbon", "wall_material": "plaster_slate_blue"},
                {"sill_m": 2.0, "head_m": 1.0}, {"u": 1.5}, {"spans": [[0.5, 0.2]]}, {"spans": [[0.0, 0.6], [0.5, 1.0]]},
                {"wall_material": "no_such_material"}):
        with pytest.raises(ValueError):
            FR.facade_rules([dict({"facing": "S", "windows": "ribbon"}, **bad)], "plaster_white")


def test_rule_selection_by_facing_and_length():
    from streetscape import frontage as FR
    rules = FR.facade_rules([{"facing": "S", "min_len_m": 18, "max_len_m": 19, "windows": "blank"},
                             {"facing": ["S", "N"], "min_len_m": 5, "windows": "ribbon"}], "plaster_white")
    south, east = np.array([0.0, -1.0]), np.array([1.0, 0.0])
    assert FR.facade_rule(rules, south, 18.4)["windows"] == "blank"            # the first matching rule wins
    assert FR.facade_rule(rules, south, 30.0)["windows"] == "ribbon"
    assert FR.facade_rule(rules, -south, 18.4)["windows"] == "ribbon"
    assert FR.facade_rule(rules, south, 1.8) is None and FR.facade_rule(rules, east, 30.0) is None
    assert FR.facade_rule(None, south, 30.0) is None


def test_runs_ribbon_spans_and_column():
    from streetscape import frontage as FR
    assert FR.facade_runs(_rule(windows="ribbon"), 10.0) == [(0.4, 9.6)]                    # pier to pier
    assert FR.facade_runs(_rule(windows="ribbon"), 3.0) == []                               # under two lights
    runs = FR.facade_runs(_rule(windows="ribbon", spans=[[0.06, 0.40], [0.60, 1.0]]), 18.42)
    assert [tuple(round(x, 2) for x in r) for r in runs] == [(1.11, 7.37), (11.05, 18.02)]
    assert FR.ribbon_lights(6.26) == 4 and FR.ribbon_lights(9.2) == 6
    (u0, u1), = FR.facade_runs(_rule(windows="column", u=0.52, window_w_m=1.8), 16.09)
    assert abs(0.5 * (u0 + u1) - 0.52 * 16.09) < 1e-9 and abs(u1 - u0 - 1.8) < 1e-9
    (u0, u1), = FR.facade_runs(_rule(windows="column", u=0.0), 10.0)                        # kept 0.6 m off the corner
    assert abs(u0 - 0.6) < 1e-9
    assert FR.facade_runs(_rule(windows="blank"), 10.0) == []


def test_windows_one_per_storey_below_the_attic_and_no_ground_floor_window_at_the_door():
    from streetscape import frontage as FR
    r = _rule(windows="column", sill_m=0.9, head_m=2.5)
    w = FR.facade_windows(r, 16.0, 100.0, 0.45, 3.5, 100.0 + 0.45 + 4 * 3.5 + 0.8, 4, "k")
    assert len(w) == 4 and [round(x[2] - 100.0, 2) for x in w] == [1.35, 4.85, 8.35, 11.85]
    assert all(x[4] == "office" and abs(x[3] - x[2] - 1.6) < 1e-9 for x in w)
    assert len(FR.facade_windows(r, 16.0, 100.0, 0.45, 3.5, 100.0 + 12.0, 4, "k")) == 3     # head under the attic
    assert len(FR.facade_windows(r, 16.0, 100.0, 0.45, 3.5, 115.25, 4, "k", door=True)) == 3
    assert FR.facade_windows(r, 16.0, 100.0, 0.45, 3.5, 115.25, 4, "k") == \
        FR.facade_windows(r, 16.0, 100.0, 0.45, 3.5, 115.25, 4, "k")                        # deterministic


def test_far_uv_reads_the_glazed_part_of_the_row():
    from streetscape import facade_atlas as FA
    from streetscape import frontage as FR
    uv = FR.far_uv((1.0, 7.2, 0.0, 1.3, "ribbon", 1, 3))                                   # 6.2 m = 4 lights
    v = FA.far_row_v("ribbon", 1)
    assert uv[0] == [9.0, v + 0.9] and uv[2] == [15.0, v + 2.5]
    uv = FR.far_uv((1.0, 2.8, 0.0, 1.6, "office", 0, 2))
    v = FA.far_row_v("office", 0)
    assert uv[0] == [6.75, v + 0.9] and uv[2] == [8.25, v + 2.5]                           # the 1.5 m window of bay 2
    assert all(0.0 <= p[0] <= 2 * FA.FAR_M[0] and 0.0 <= p[1] <= FA.FAR_M[1] for p in uv)


def test_lod1_facade_tiles_the_wall_without_overlap():
    from streetscape import frontage as FR

    class Acc:
        def __init__(self):
            self.q = []

        def quad(self, layer, mat, a, b, c, d, uv=None):
            self.q.append((layer, mat, np.array([a, b, c, d]), uv))
    r = _rule(windows="ribbon", spans=[[0.0, 0.4], [0.6, 1.0]])
    wins = FR.facade_windows(r, 20.0, 0.0, 0.45, 3.5, 12.0, 3, "k")
    acc = Acc()
    n = FR.lod1_facade(acc, r, wins, np.array([0.0, 0.0]), np.array([1.0, 0.0]), 20.0, 0.6, 12.0)
    assert n == len(acc.q) == 3 + 2 * (2 * 3 + 1) and {q[1] for q in acc.q} == {"plaster_white__far_ribbon"}
    area = sum(float(np.ptp(q[2][:, 0]) * np.ptp(q[2][:, 2])) for q in acc.q)
    assert abs(area - 20.0 * (12.0 - 0.6)) < 1e-6                                           # exact tiling: no overlap
    glazed = [q for q in acc.q if q[3][0][1] > 2.0]
    assert len(glazed) == len(wins) == 6
    acc = Acc()
    assert FR.lod1_facade(acc, r, [], np.array([0.0, 0.0]), np.array([1.0, 0.0]), 20.0, 0.6, 12.0) == 1


def test_tower_gable_is_blank_with_one_stair_column():
    b = _loaded({TOWER})[TOWER]
    assert len(b["ovr"]["facades"]) == 3 and b["ovr"]["wall_material"] == "plaster_white"
    buf = _build(b)
    # LOD0: the atlas panes on the SW gable (16.09 m) form ONE column, one window per storey (11)
    g = _panes(_on_wall(buf, "buildings", "facade_atlas", SW, 238.0), 1.6)
    d = np.array([-np.cos(SW), np.sin(SW)])                           # along the gable
    u = g[:, :, :2] @ d
    assert len(g) == 22 and np.ptp(u) < 1.8 + 1e-6, (len(g), float(np.ptp(u)))
    assert len({round(float(t[:, 2].min()), 2) for t in g}) == 11
    # LOD1: two plain side quads + 11 x (plain piece + window) + top piece = 25 quads in the far material
    assert _tris(buf, "buildings_low", "plaster_beige__far_office") == 2 * 25 * 2          # SW and NE gables
    assert len(_on_wall(buf, "buildings_low", "plaster_beige__far_office", SW, 238.0)) == 50
    assert len(_on_wall(buf, "buildings", "plaster_beige", SE, -1e9)) == 0                 # sand on the gables only


def test_tower_long_wall_has_one_band_per_storey_on_white():
    b = _loaded({TOWER})[TOWER]
    buf = _build(b)
    for layer, mat in (("buildings", "plaster_white"), ("buildings_low", "plaster_white__far_ribbon")):
        assert len(_on_wall(buf, layer, mat, SE, -1e9)) > 0, (layer, mat)
    g = _panes(_on_wall(buf, "buildings", "facade_atlas", SE, -1e9), 1.3)                  # bands 1.3 m high
    z = sorted({round(float(t[:, 2].min()), 2) for t in g})
    assert len(z) == 11 and all(abs((b_ - a_) - (z[1] - z[0])) < 0.02 for a_, b_ in zip(z, z[1:]))    # 11 storeys
    # LOD1 window quads carry far-row UVs of the ribbon rows; plain pieces stay in the plain strip (v < 1 m)
    from streetscape import facade_atlas as FA
    v0 = FA.far_row_v("ribbon", 0)
    rows = 0
    for p in buf.parts:
        if p.layer == "buildings_low" and p.mat == "plaster_white__far_ribbon":
            assert ((p.UV[:, 1] < 1.0) | (p.UV[:, 1] >= v0 + 0.9 - 1e-6)).all()
            rows += int((p.UV[:, 1] >= v0).sum())
    assert rows > 0
    m1, m0 = buf.mats("buildings_low"), buf.mats("buildings")
    assert not any(x.endswith("__far_office") and not x.startswith("plaster_beige") for x in m1)
    assert "plaster_band_grey" not in m0 and "window_frame" not in m1


def test_tower_uses_only_materials_the_generic_office_set_has():
    from streetscape import buildings_mesh as BM
    from streetscape import materials as MT
    buf = _build(_loaded({TOWER})[TOWER])
    for layer in ("buildings", "buildings_low"):
        assert buf.mats(layer) <= set(MT.M), buf.mats(layer) - set(MT.M)
    far = {m for m in buf.mats("buildings_low") if "__far_" in m}
    assert far == {"plaster_beige__far_office", "plaster_white__far_ribbon"}
    assert {"plaster_white", "plaster_beige"} <= set(BM.OFFICE_WALLS)
    # LOD1 stays cheap: under 700 triangles for the whole tower (300 with the hashed facade)
    assert sum(len(p.T) for p in buf.parts if p.layer == "buildings_low") < 700


def test_buildings_without_the_override_are_unchanged():
    import json
    from streetscape import buildings_mesh as BM
    fc = json.loads((REGION_DIR / "buildings.geojson").read_text(encoding="utf-8"))
    plain = BM.load({"features": [f for f in fc["features"] if f["id"] == TOWER]}, ORIGIN, [])[0]
    assert "facades" not in plain["ovr"]
    buf = _build(plain)
    far = {m for m in buf.mats("buildings_low") if "__far_" in m}
    assert len(far) == 1                                              # one hashed far material, as before ADR 0180
