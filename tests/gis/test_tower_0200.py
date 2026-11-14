"""ADR 0200 (reviews REVIEW-2026-11-14-s20-mistral-m57 par. 6, REVIEW-2026-11-14-s20-0190 P2-A / P2-B / P2-G): the
tower at Andersa 38 - NW wall with 6 groups of about 5 white-framed sashes per storey (not a grid of punched windows),
the middle lattice mast and the masts of the N / E corners, grey drums below the pole tops, the ground-floor annex on
the SE wall; both LODs draw the same windows and masts; no new material."""
import json

import numpy as np
import pytest
import shapely

from test_buildings_0167 import ORIGIN, REGION_DIR, TOWER, _build, _loaded
from test_buildings_0180 import SE, _on_wall, _rule
from test_tower_0190 import _normal

NW = np.radians(298.2)
ANNEX = "override:g3a-office-tower-se-annex"
SPANS = [[0.01, 0.14], [0.17, 0.30], [0.33, 0.47], [0.51, 0.64], [0.67, 0.81], [0.84, 0.99]]


def _fr():
    from streetscape import frontage as FR
    return FR


def _nw_rule(b):
    FR = _fr()
    rules = FR.facade_rules(b["ovr"]["facades"], b["ovr"]["wall_material"])
    c = np.asarray(b["poly"].exterior.coords)
    hits = []
    for p, q in zip(c[:-1], c[1:]):
        L = float(np.hypot(*(q - p)))
        d = (q - p) / L
        nout = np.array([d[1], -d[0]])
        r = FR.facade_rule(rules, nout, L)
        if r is not None and FR.faces(nout, "NW"):
            hits.append((r, p, d, L))
    return hits


def test_new_rule_fields_are_validated_and_default_to_the_old_behaviour():
    FR = _fr()
    r = _rule(windows="ribbon", glazing="light")
    assert r["light_m"] == FR.RIBBON_LIGHT_M and r["sashes"] == 2 and r["mix"] is None
    assert r["far"] == "plaster_white__far_ribbon"
    assert FR.band_lights("k", 40) == FR.band_lights("k", 40, None, 2)
    r = _rule(windows="ribbon", glazing="light", light_m=0.96, light_sashes=1, light_mix=[10, 20, 70], far_kind="office")
    assert r["far"] == "plaster_white__far_office" and r["sashes"] == 1 and r["mix"] == (10, 20, 70)
    for bad in (dict(windows="ribbon", light_m=0.96),                              # dark ribbon rows: mullions at 1.5 m
                dict(windows="column", light_sashes=1),
                dict(windows="ribbon", glazing="light", light_m=0.3),
                dict(windows="ribbon", glazing="light", light_sashes=3),
                dict(windows="ribbon", glazing="light", light_mix=[50, 20, 20]),
                dict(windows="ribbon", glazing="light", light_mix=[50, 50]),
                dict(windows="ribbon", glazing="light", far_kind="nope"),
                dict(windows="ribbon", far_kind="office")):
        with pytest.raises(ValueError):
            _rule(**bad)


def test_single_sash_lights_come_in_pairs_of_one_window():
    FR = _fr()
    li = FR.band_lights("k", 9, (10, 20, 70), 1)
    assert len(li) == 9 and all(li[i] == li[i + 1] for i in range(0, 8, 2))        # two sashes of one hashed window
    assert [FR.sash_half(i, 1) for i in range(4)] == [0, 1, 0, 1] and FR.sash_half(3, 2) is None
    many = FR.band_lights("k", 2000, (10, 20, 70), 1)[::2]
    blind = sum(r == FR.BLIND_ROW for r, _, _ in many) / len(many)
    assert 0.05 < blind < 0.16, blind                                             # the authored share, not BAND_LIGHTS
    full, left, right = (FR.far_uv((0, 1, 0, 1.3, "office", 0, 1), 0.0, h) for h in (None, 0, 1))
    assert left[0][0] == full[0][0] and right[1][0] == full[1][0] and left[1][0] == pytest.approx(right[0][0])
    assert left[1][0] - left[0][0] == pytest.approx((full[1][0] - full[0][0]) / 2)


def test_tower_nw_wall_is_one_edge_with_the_band_rule():
    b = _loaded({TOWER})[TOWER]
    assert b["ovr"]["footprint_simplify_m"] == 0.3
    hits = _nw_rule(b)
    assert len(hits) == 1                                                  # BDOT10k: two edges 1.5 deg apart
    r, _, _, L = hits[0]
    assert L == pytest.approx(37.09, abs=0.1) and len(np.asarray(b["poly"].exterior.coords)) - 1 == 4
    assert r["windows"] == "ribbon" and r["group"] == "office" and r["wall"] == "plaster_beige"
    assert r["far"] == "plaster_beige__far_office" and r["lintel_m"] == 0.0
    assert [list(x) for x in r["spans"]] == SPANS                          # review M57: fractions from the NE end
    fc = json.loads((REGION_DIR / "buildings.geojson").read_text(encoding="utf-8"))
    from streetscape import buildings_mesh as BM
    raw = BM.load({"features": [f for f in fc["features"] if f["id"] == TOWER]}, ORIGIN, [])[0]
    assert b["poly"].symmetric_difference(raw["poly"].buffer(-3.3, join_style=2).buffer(3.3, join_style=2)).area < 6.0


def test_tower_nw_wall_has_six_groups_of_about_five_sashes_per_storey_on_both_lods():
    FR = _fr()
    from streetscape import facade_atlas as FA
    b = _loaded({TOWER})[TOWER]
    r, a, d, L = _nw_rule(b)[0]
    runs = FR.facade_runs(r, L)
    assert len(runs) == 6
    for (u0, u1), (x0, x1) in zip(runs, SPANS):
        assert u0 == pytest.approx(max(L * x0, FR.RIBBON_END_M), abs=1e-6) and u1 <= L * x1 + 1e-6
    lights = [FR.ribbon_lights(u1 - u0, r["light_m"]) for u0, u1 in runs]
    assert lights == [5, 5, 5, 5, 5, 6]
    buf = _build(b)
    n, off = _normal(b, NW)
    # LOD0: glazing quads of the atlas inside the band of every storey lie in the 6 groups only
    tri = _on_wall(buf, "buildings", "facade_atlas", float(np.arctan2(n[0], n[1])), off - 0.4)
    u = (tri[:, :, :2] - a) @ d
    h = np.ptp(tri[:, :, 2], axis=1)
    panes = tri[np.abs(h - 1.3) < 1e-6]
    up = ((panes[:, :, :2] - a) @ d)
    assert len(panes) == 2 * 11 * sum(lights)
    inside = np.zeros(len(panes), bool)
    for u0, u1 in runs:
        inside |= (up.min(1) > u0 - 1e-6) & (up.max(1) < u1 + 1e-6)
    assert inside.all()
    assert float(np.median(np.ptp(up, axis=1))) == pytest.approx(0.96, abs=0.12)       # one sash per light
    zs0 = sorted({round(float(z), 2) for z in panes[:, :, 2].min(1)})
    assert len(zs0) == 11
    # LOD1: the same groups and storeys as window quads of the office rows in the gables' far material
    v0 = FA.far_row_v("office", 0)
    low = [p for p in buf.parts if p.layer == "buildings_low" and p.mat == "plaster_beige__far_office"]
    wins = []
    for p in low:
        t, uv = p.V[p.T], p.UV[p.T]
        nn = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        on = (nn[:, :2] @ n > 0) & (np.abs(t[:, :, :2] @ n - off).max(1) < 0.05) & (uv[:, :, 1].min(1) > 1.0)
        wins.append(t[on])
    wins = np.concatenate(wins)
    uw = (wins[:, :, :2] - a) @ d
    inside = np.zeros(len(wins), bool)
    for u0, u1 in runs:
        inside |= (uw.min(1) > u0 - 1e-6) & (uw.max(1) < u1 + 1e-6)
    assert inside.all() and len(wins) == 2 * 11 * sum((k + 1) // 2 for k in lights)       # a pair of sashes = one quad
    assert sorted({round(float(z), 2) for z in wins[:, :, 2].min(1)}) == zs0
    assert v0 > 1.0
    # no hashed punched grid is left on NW: nothing of the dark office rows, no window kit frames
    assert not any(p.mat.endswith("__far_office_d") for p in buf.parts)


def test_tower_far_materials_and_se_wall_are_unchanged():
    b = _loaded({TOWER})[TOWER]
    buf = _build(b)
    assert {m for m in buf.mats("buildings_low") if "__far_" in m} == {"plaster_beige__far_office",
                                                                        "plaster_white__far_ribbon"}
    se = next(r for r in b["ovr"]["facades"] if r["facing"] == "SE")
    assert se["wall_material"] == "plaster_white" and se["spans"] == [[0.03, 0.20], [0.30, 1.0]]     # colour: open
    assert "light_m" not in se and "light_mix" not in se
    n, off = _normal(b, SE)
    assert len(_on_wall(buf, "buildings", "plaster_white", float(np.arctan2(n[0], n[1])), off - 0.4)) > 100


def test_roof_masts_follow_the_orthophoto_base_frames():
    FR = _fr()
    b = _loaded({TOWER})[TOWER]
    assert b["ovr"]["machine_rooms"] is False
    specs = FR.roof_mast_specs(b["ovr"]["roof_masts"])
    lat = [s for s in specs if s["kind"] == "lattice"]
    assert sorted(s["height_m"] for s in lat) == [4.6, 5.0, 6.5, 9.5, 11.0]
    mid = next(s for s in lat if s["height_m"] == 11.0)
    assert mid["facing"] == "SE" and 0.45 <= mid["u"] <= 0.55                    # middle of the length (M57)
    west = next(s for s in lat if s["height_m"] == 9.5)
    assert west["facing"] == "SW" and west["u"] <= 0.22 and west["inset_m"] <= 3.0           # review 0190 P2-B
    assert sum(s["facing"] == "NE" for s in lat) == 2                            # N and E corners
    poles = [s for s in specs if s["kind"] == "pole"]
    assert len({s["height_m"] for s in poles}) >= 4                              # P2-A: no row of identical poles
    assert sum(s["sectors"] > 0 for s in poles) >= 3 and sum(s["dishes"] > 0 for s in poles) >= 2
    buf = _build(b)
    zwall = max(float(p.V[:, 2].max()) for p in buf.parts if p.layer == "buildings_low" and "__far_" in p.mat)
    hull = b["poly"].buffer(0.9)
    for layer in ("buildings", "buildings_low"):
        V = np.concatenate([p.V[p.T].reshape(-1, 3) for p in buf.parts
                            if p.layer == layer and p.mat in (FR.ROOF_MAST_MAT, FR.ROOF_PANEL_MAT)])
        V = V[V[:, 2] > zwall + 0.5]
        assert shapely.contains_xy(hull, V[:, 0], V[:, 1]).all()
        # no lift machine room box on the roof (hashed rule of tall offices)
        assert not any(p.layer == layer and p.mat == "balcony_slab" and float(p.V[:, 2].max()) > zwall
                       for p in buf.parts)
    for bad in ({"kind": "pole", "facing": "S", "panel_h_m": 3.0}, {"kind": "pole", "facing": "S", "dish_m": 2.0},
                {"kind": "pole", "facing": "S", "height_m": 1.2, "panel_h_m": 1.4}):
        with pytest.raises(ValueError):
            FR.roof_mast_specs([bad])


def test_drum_hangs_below_the_pole_top_in_galvanised_grey():
    FR = _fr()
    from streetscape.buildings_mesh import Acc
    acc = Acc()
    spec = FR.roof_mast_specs([{"kind": "pole", "facing": "S", "height_m": 3.0, "dishes": 1}])
    c = [np.array(q) for q in ((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0))]
    FR.roof_masts(acc, spec, [(c[i], c[(i + 1) % 4]) for i in range(4)], 20.0)
    assert {k[1] for k in acc.d} == {FR.ROOF_MAST_MAT}                           # no white globe on a stick
    for layer in ("buildings", "buildings_low"):
        V = np.concatenate([np.asarray(it[0], float).reshape(-1, 3) for it in acc.d[(layer, FR.ROOF_MAST_MAT)]])
        drum = V[np.abs(V[:, 1] - 1.0) > 0.12]
        assert float(V[:, 2].max()) == pytest.approx(23.0) and float(drum[:, 2].max()) < 23.0 - 0.8, layer


def test_se_annex_is_a_one_storey_part_at_the_bdot_protrusion():
    from streetscape import buildings_mesh as BM
    got = _loaded({TOWER})
    assert ANNEX in got and got[ANNEX]["typ"] == "office" and got[ANNEX]["props"]["height_m"] == 3.9
    an, tw = got[ANNEX]["poly"], got[TOWER]["poly"]
    fc = json.loads((REGION_DIR / "buildings.geojson").read_text(encoding="utf-8"))
    raw = BM.load({"features": [f for f in fc["features"] if f["id"] == TOWER]}, ORIGIN, [])[0]["poly"]
    step = raw.difference(tw.buffer(0.05)).buffer(-0.3).buffer(0.3)             # what the opening cut off (no slivers)
    assert step.area > 8.0 and an.intersection(step).area > 0.9 * step.area       # the BDOT10k protrusion
    assert an.difference(raw.buffer(0.05)).area < 0.1 and 0.3 < an.intersection(tw).area < 3.0      # no gap at the wall
    # the entrance: on the SE face of the annex, never on the SE wall of the tower (it sat half behind the annex)
    FR = _fr()
    ar = FR.facade_rules(got[ANNEX]["ovr"]["facades"], "plaster_beige")
    assert ar[0]["door"] is True and ar[0]["facing"] == "SE" and ar[1]["door"] is False
    tr = FR.facade_rules(got[TOWER]["ovr"]["facades"], "plaster_beige")
    assert [r["door"] for r in tr] == [None, False, None]
    assert _rule(windows="blank")["door"] is None
    buf = _build(got[ANNEX])
    n, off = _normal(got[ANNEX], SE)
    door = _on_wall(buf, "buildings", "facade_atlas", float(np.arctan2(n[0], n[1])), off - 0.4)
    assert len(door) >= 2 and float(np.ptp(door[:, :, 2])) > 2.0                  # the door leaf on the SE face
    zs = np.concatenate([p.V[:, 2] for p in buf.parts if p.layer == "buildings_low"])
    assert float(zs.max()) - 100.0 < 4.6                                          # one storey (ground at 100 in tests)
    for layer in ("buildings", "buildings_low"):
        assert buf.mats(layer) <= {"plaster_beige", "plaster_beige__far_office", "plinth_dark", "hall_flashing",
                                   "roof_membrane", "facade_atlas", "reveal_plaster", "canopy_steel", "window_sill",
                                   "balcony_slab", "downpipe"}, buf.mats(layer)
    assert sum(len(p.T) for p in buf.parts if p.layer == "buildings_low") < 60
