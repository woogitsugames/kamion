"""ADR 0190 (review REVIEW-2026-11-13-s19-0180-r2 P2-3 / P2-4 / P2-5): the tower by the Kwadrat lane - light band
windows under a dark lintel line on the white SE wall, white-framed clear-glass windows in the gable column, authored
roof masts (override `roof_masts`); both LODs draw the same windows, lintels and masts; no new material."""
import numpy as np
import pytest
import shapely

from test_buildings_0167 import TOWER, _build, _loaded
from test_buildings_0180 import SE, SW, _on_wall, _rule


def _normal(b, bearing):
    """Exact outward normal of the longest footprint edge looking to the bearing (rad) and its plane offset."""
    n0 = np.array([np.sin(bearing), np.cos(bearing)])
    c = np.asarray(b["poly"].exterior.coords)
    cen = np.asarray(b["poly"].centroid.coords[0])
    best = None
    for p, q in zip(c[:-1], c[1:]):
        d = q - p
        L = float(np.hypot(*d))
        for n in (np.array([d[1], -d[0]]) / L, np.array([-d[1], d[0]]) / L):
            if n @ n0 > 0.97 and p @ n > cen @ n and (best is None or L > best[0]):
                best = (L, n, float(p @ n))
    return best[1], best[2]


def _fr():
    from streetscape import frontage as FR
    return FR


def test_band_lights_are_hashed_white_joinery_windows():
    from streetscape import facade_atlas as FA
    FR = _fr()
    assert sum(s for s, _, _ in FR.BAND_LIGHTS) == 100
    li = FR.band_lights("k", 400)
    assert li == FR.band_lights("k", 400) and li != FR.band_lights("k2", 400)            # deterministic, keyed
    var = [FA.FAR_ROWS["office"][r][b][1] for r, b, _ in li]
    assert set(var) == {2, 4}                                                            # white frames only: no
    assert all(c in (0.0, 0.36) for _, _, c in li)                                       # beige blind (variant 0)
    assert all(c == 0.0 for (_, _, c), v in zip(li, var) if v == 2)
    light = sum(1 for (_, _, c), v in zip(li, var) if v == 4 and c > 0) / len(li)
    assert 0.5 < light < 0.75 and 0.03 < var.count(2) / len(li) < 0.2, (light, var.count(2))


def test_far_uv_crop_cuts_the_bottom_of_the_window():
    from streetscape import facade_atlas as FA
    FR = _fr()
    v = FA.far_row_v("office", 1)
    full, crop = FR.far_uv((0, 1.5, 0, 1.3, "office", 1, 2)), FR.far_uv((0, 1.5, 0, 1.3, "office", 1, 2, None), 0.36)
    assert full[0][1] == pytest.approx(v + 0.9) and full[2][1] == pytest.approx(v + 2.5)
    assert crop[0][1] == pytest.approx(v + 0.9 + 0.36 * 1.6) and crop[2][1] == full[2][1]
    assert [q[0] for q in crop] == [q[0] for q in full]


def test_rule_fields_are_validated():
    r = _rule(windows="ribbon", glazing="light", lintel_m=0.15, reveal_m=0.06)
    assert r["lintel_m"] == 0.15 and r["reveal_m"] == 0.06 and _rule(windows="ribbon")["lintel_m"] == 0.0
    for bad in ({"lintel_m": 0.8}, {"reveal_m": 0.0}, {"lintel_m": -0.1}):
        with pytest.raises(ValueError):
            _rule(windows="ribbon", **bad)
    FR = _fr()
    wins = FR.facade_windows(r, 10.0, 0.0, 0.45, 3.5, 8.5, 2, "k")
    lin = FR.facade_lintels(r, wins)
    assert len(lin) == len(wins) == 2 and all(l[2] == w[3] and l[3] == pytest.approx(w[3] + 0.15) and l[0] < w[0]
                                              and l[1] > w[1] for l, w in zip(lin, wins))
    assert all(len(w) == 8 and len(w[7]) == FR.ribbon_lights(w[1] - w[0]) for w in wins)
    assert FR.facade_lintels(_rule(windows="ribbon"), wins) == []


def test_tower_se_wall_has_a_dark_lintel_over_every_band_on_both_lods():
    FR = _fr()
    b = _loaded({TOWER})[TOWER]
    buf = _build(b)
    n, wall = _normal(b, SE)
    for layer, proud, quads in (("buildings", FR.LINTEL_PROUD_M[0], 1), ("buildings_low", FR.LINTEL_PROUD_M[1], 1)):
        tri = _on_wall(buf, layer, FR.LINTEL_MAT, SE, -1e9)
        tri = tri[(np.abs(np.ptp(tri[:, :, 2], axis=1) - 0.15) < 1e-6)                   # the 0.15 m front faces,
                  & (np.abs(tri[:, :, :2] @ n - (wall + proud)).max(1) < 5e-3)]          # proud of the wall: no z-fight
        assert len(tri) == 22 * 2 * quads, (layer, len(tri))                             # 11 storeys x 2 runs
    # the lintel sits right on the band head, on both LODs at the same height
    zs = []
    for layer, proud in (("buildings", FR.LINTEL_PROUD_M[0]), ("buildings_low", FR.LINTEL_PROUD_M[1])):
        zs.append(sorted({round(float(t[:, 2].min()), 3) for t in _on_wall(buf, layer, FR.LINTEL_MAT, SE, -1e9)
                          if abs(np.ptp(t[:, 2]) - 0.15) < 1e-6 and np.abs(t[:, :2] @ n - (wall + proud)).max() < 5e-3}))
    assert zs[0] == zs[1] and len(zs[0]) == 11


def test_tower_se_band_cells_are_the_light_variants_on_both_lods():
    from streetscape import facade_atlas as FA
    buf = _build(_loaded({TOWER})[TOWER])
    cells = {v: FA.cell("off", v) for v in range(5)}
    seen = set()
    for p in buf.parts:
        if p.layer != "buildings" or p.mat != "facade_atlas":
            continue
        tri, uv = p.V[p.T], p.UV[p.T]
        nn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        nn /= np.maximum(np.linalg.norm(nn, axis=1, keepdims=True), 1e-12)
        sel = (nn[:, :2] @ np.array([np.sin(SE), np.cos(SE)]) > 0.97) & (np.abs(np.ptp(tri[:, :, 2], axis=1) - 1.3) < 1e-6)
        for t in uv[sel]:
            c = t.mean(0)
            seen |= {v for v, (u0, v0, w, h) in cells.items() if u0 <= c[0] <= u0 + w and v0 <= c[1] <= v0 + h}
    assert seen == {2, 4}, seen                                    # no beige blinds, no anthracite frames
    # LOD1: the same windows = office rows; cropped lights start above the dark glass of the cell
    v0 = FA.far_row_v("office", 0)
    crops = set()
    for p in buf.parts:
        if p.layer == "buildings_low" and p.mat == "plaster_white__far_ribbon":
            for q in p.UV[p.T]:
                if q[:, 1].min() >= v0:
                    crops.add(round(float((q[:, 1].min() - v0) % FA.FAR_ROW_H - 0.9), 3))
    assert crops == {0.0, round(0.36 * 1.6, 3)}, crops


def test_tower_gable_windows_are_white_framed_clear_glass_with_a_shallow_reveal():
    from streetscape import facade_atlas as FA
    b = _loaded({TOWER})[TOWER]
    assert b["ovr"]["facades"][0]["variants"] == [2] and b["ovr"]["facades"][0]["reveal_m"] == 0.06
    buf = _build(b)
    n, wall = _normal(b, SW)
    tri = _on_wall(buf, "buildings", "facade_atlas", SW, 238.0)
    panes = tri[np.abs(np.ptp(tri[:, :, 2], axis=1) - 1.6) < 1e-6]
    assert len(panes) == 20 and np.allclose(panes[:, :, :2] @ n, wall - 0.06, atol=5e-3)
    u0, v0, w, h = FA.cell("off", 2)
    for p in buf.parts:
        if p.layer == "buildings" and p.mat == "facade_atlas":
            t, uv = p.V[p.T], p.UV[p.T]
            sel = (np.abs(np.ptp(t[:, :, 2], axis=1) - 1.6) < 1e-6) & (np.abs((t[:, :, :2] @ n).mean(1) - (wall - 0.06)) < 5e-3)
            c = uv[sel].mean(1)
            assert ((c[:, 0] > u0) & (c[:, 0] < u0 + w) & (c[:, 1] > v0) & (c[:, 1] < v0 + h)).all()


def test_roof_mast_specs_are_validated():
    FR = _fr()
    assert FR.roof_mast_specs(None) is None and FR.roof_mast_specs([]) is None
    s = FR.roof_mast_specs([{"kind": "lattice", "facing": "SW", "height_m": 9.5, "sectors": 3}])[0]
    assert s["side_m"] == 0.5 and s["material"] == FR.ROOF_MAST_MAT and s["panel_material"] == FR.ROOF_PANEL_MAT
    for bad in ({"kind": "tower", "facing": "SW"}, {"kind": "pole", "facing": "up"}, {"kind": "pole", "facing": "S", "height_m": 40},
                {"kind": "pole", "facing": "S", "u": 1.5}, {"kind": "pole", "facing": "S", "sectors": 9},
                {"kind": "pole", "facing": "S", "material": "no_such_material"}):
        with pytest.raises(ValueError):
            FR.roof_mast_specs([bad])


def test_tower_roof_carries_the_authored_masts_on_both_lods():
    FR = _fr()
    b = _loaded({TOWER})[TOWER]
    specs = b["ovr"]["roof_masts"]
    assert len(specs) == 8 and sum(s["kind"] == "lattice" for s in specs) == 2
    buf = _build(b)
    low_walls = [p for p in buf.parts if p.layer == "buildings_low" and "__far_" in p.mat]
    zwall = max(float(p.V[:, 2].max()) for p in low_walls)
    hull = b["poly"].buffer(0.9)
    tops = {}
    for layer in ("buildings", "buildings_low"):
        V = [p.V[p.T].reshape(-1, 3) for p in buf.parts if p.layer == layer and p.mat in (FR.ROOF_MAST_MAT, FR.ROOF_PANEL_MAT)]
        V = np.concatenate(V)
        V = V[V[:, 2] > zwall + 0.5]                             # above the attic: only masts reach there
        assert len(V) > 300, (layer, len(V))
        assert shapely.contains_xy(hull, V[:, 0], V[:, 1]).all()     # nothing hangs out over the street
        tops[layer] = float(V[:, 2].max())
        # the two lattice masts and the six poles: tops cluster at 8 distinct plan positions
        top_pts = {(round(float(x), 0), round(float(y), 0)) for x, y, z in V if z > zwall + 1.8}
        assert len(top_pts) >= 8, (layer, len(top_pts))
    assert tops["buildings"] == pytest.approx(tops["buildings_low"])                    # same silhouette height
    assert tops["buildings"] == pytest.approx(zwall - 0.3 + 9.5 + 1.2, abs=0.4)          # tall mast + spike
    # no material the tower did not draw before (galvanised steel + white render, both LODs)
    assert FR.ROOF_MAST_MAT in buf.mats("buildings") and FR.ROOF_MAST_MAT in buf.mats("buildings_low")
    assert not any(m.startswith("frontage_") or m == "window_frame" for m in buf.mats("buildings_low"))


def test_tower_has_no_external_downpipes():
    """ADR 0190: the pair of galvanised pipes 0.7 m apart in the NW wall and the pairs at the corners (ADR 0184 par. 4)
    are gone on both LODs - every `downpipe` triangle of the tower is a roof mast now."""
    FR = _fr()
    b = _loaded({TOWER})[TOWER]
    assert b["ovr"]["downpipes"] is False
    buf = _build(b)
    zwall = max(float(p.V[:, 2].max()) for p in buf.parts if p.layer == "buildings_low" and "__far_" in p.mat)
    for layer in ("buildings", "buildings_low"):
        for p in buf.parts:
            if p.layer == layer and p.mat == FR.ROOF_MAST_MAT:
                tri = p.V[p.T]
                below = tri[tri[:, :, 2].min(1) < zwall - 0.5]          # AC brackets, the entrance canopy: small
                assert len(below) == 0 or float(np.ptp(below[:, :, 2], axis=1).max()) < 3.0, layer   # no pipe run


def test_roof_mast_faces_look_outwards():
    FR = _fr()

    class Acc:
        def __init__(self):
            self.t = []

        def add(self, layer, mat, V, T, UV=None, UV1=None):
            V = np.asarray(V, float)
            self.t += [(layer, mat, V[list(t)]) for t in np.asarray(T).reshape(-1, 3)]

        def quad(self, layer, mat, a, b, c, d, uv=None, uv1=None):
            self.add(layer, mat, [a, b, c, d], [[0, 1, 2], [0, 2, 3]])

        def box(self, layer, mat, c, ax, ay, az, skip=()):
            from streetscape.buildings_mesh import Acc as A
            A.box(self, layer, mat, c, ax, ay, az, skip)
    acc = Acc()
    spec = FR.roof_mast_specs([{"kind": "pole", "facing": "S", "height_m": 3.0, "dishes": 1, "sectors": 1}])
    c = [np.array(q) for q in ((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0))]       # outward normal = right of travel
    edges = [(c[i], c[(i + 1) % 4]) for i in range(4)]
    out = FR.roof_masts(acc, spec, edges, 20.0)
    assert out[0]["placed"] and out[0]["n"] == pytest.approx(1.0) and out[0]["e"] == pytest.approx(5.0)
    for layer in ("buildings", "buildings_low"):
        tri = np.array([t for la, m, t in acc.t if la == layer and m == FR.ROOF_PANEL_MAT])
        assert len(tri) >= 12
        # drum and panel are convex solids away from the pole: every face normal points away from its solid's centre
        for grp in (tri[tri[:, :, 2].mean(1) > 20.8], tri[tri[:, :, 2].mean(1) <= 20.8]):       # panel / drum
            assert len(grp) >= 6
            cen = grp.reshape(-1, 3).mean(0)
            nn = np.cross(grp[:, 1] - grp[:, 0], grp[:, 2] - grp[:, 0])
            assert ((nn * (grp.mean(1) - cen)).sum(1) > -1e-9).all(), layer
