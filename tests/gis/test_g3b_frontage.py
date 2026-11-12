"""ADR 0126: authored frontage of the trade pavilions along G3-B (streetscape.frontage, override key `frontage`)
and the block overrides (wall_material / balconies / bands). Unit tests on a synthetic pavilion + the region data."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml
from shapely.geometry import Point, box
from shapely.geometry.polygon import orient

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
REGION_DIR = REPO / "Data" / "Regions" / "bialystok-industrial-c"
ORIGIN = (777995.0, 596223.0)
IDS = {"furniture": "bdot:2BE4B431-C34A-1BF0-E053-CC2BA8C0D140", "cars": "bdot:2BE4B431-C785-1BF0-E053-CC2BA8C0D140",
       "glazed": "bdot:3c5cd1c0-9ee5-4321-916e-ba061fd4d013", "block": "bdot:d0f4dd2c-c040-439e-aece-8fe13f9d3046"}


class _Buf:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, **kw):
        self.parts.append(SimpleNamespace(layer=layer, mat=mat, V=np.asarray(V, float), T=np.asarray(T).reshape(-1, 3),
                                          src=kw.get("src")))

    def tris(self, layer=None, mat=None):
        return sum(len(p.T) for p in self.parts if (layer is None or p.layer == layer) and (mat is None or p.mat == mat))

    def mats(self, layer):
        return {p.mat for p in self.parts if p.layer == layer}


_HF = SimpleNamespace(sample=lambda x, y: np.full(np.shape(x), 100.0))


def _build(ovr, typ="office", poly=None, props=None):
    from streetscape import buildings_mesh as BM
    poly = poly or box(0, 0, 30, 20)                      # walls look S (30 m), E (20 m), N, W
    b = {"id": "t:1", "poly": orient(poly),
         "props": props or {"height_m": 6.0, "function": "obiekt handlowo-usługowy", "storeys": 1}, "ovr": ovr, "typ": typ}
    buf, rep, signs = _Buf(), {}, []
    BM.build(buf, [b], _HF, None, None, box(-50, -30, 80, -10), rep, sign_out=signs)
    return buf, rep, signs


SPEC = {"wall": "brick_red", "walls": {"N": "plaster_grey"},
        "fascia": {"material": "hall_flashing", "height_m": 1.0, "facings": ["S", "E"]},
        "glazing": [{"facing": "S", "span": [0.0, 1.0], "z": [0.3, 3.5], "pitch_m": 2.4, "transom_m": 2.4},
                    {"facing": "E", "span": [0.0, 0.5], "z": [0.3, 3.5], "pitch_m": 2.4}],
        "accents": [{"facing": "W", "span": [0.0, 0.5], "material": "plaster_accent_terracotta", "z": [3.6, 5.0]}],
        "sign": {"code": "serwis", "facing": "S", "u": 0.5, "z_m": 5.4},
        "props": [{"kind": "flag_row", "facing": "S", "u": 0.5, "out_m": 8.0, "count": 3, "material": "paint_yellow"},
                  {"kind": "totem", "facing": "S", "u": -0.2, "out_m": 6.0, "material": "plaster_accent_grey"},
                  {"kind": "sign_mast", "facing": "S", "u": 1.1, "out_m": 6.0, "material": "bin_plastic_blue"}]}


def test_facing_and_plan_validation():
    from streetscape import frontage as FR
    from streetscape import materials as MT
    assert FR.faces(np.array([0.0, 1.0]), "N") and FR.faces(np.array([0.7, 0.7]), "NE")
    assert FR.faces(np.array([0.669, 0.743]), ["NW", "NE"]) and not FR.faces(np.array([0.669, 0.743]), "NW")
    assert not FR.faces(np.array([1.0, 0.0]), "N") and FR.faces(np.array([1.0, 0.0]), "all")
    assert FR.plan(None) is None and FR.plan({}) is None
    s = FR.plan(SPEC, MT.M)
    assert s["wall"] == "brick_red" and s["fascia"]["height_m"] == 1.0 and len(s["glazing"]) == 2 and len(s["props"]) == 3
    with pytest.raises(ValueError):
        FR.plan({"wall": "no_such_material"}, MT.M)
    with pytest.raises(ValueError):                       # hall cladding needs wall-top UV1 on every triangle
        FR.plan({"wall": "hall_wall_grey"}, MT.M)
    with pytest.raises(ValueError):
        FR.plan({"glazing": [{"facing": "north"}]}, MT.M)
    with pytest.raises(ValueError):
        FR.plan({"props": [{"kind": "billboard", "facing": "N"}]}, MT.M)


def test_pavilion_walls_glazing_and_lods():
    """Wall colour per facing, fascia, glazed runs with mullions - the same on LOD0 and LOD1, and nothing of the
    generic office facade (atlas windows, far-facade window zone, hashed render colour)."""
    buf, rep, signs = _build({"frontage": SPEC})
    assert rep["frontages"] == 1 and rep["typologies"] == {"office": 1}
    for layer in ("buildings", "buildings_low"):
        m = buf.mats(layer)
        assert {"brick_red", "plaster_grey", "showroom_glass", "hall_flashing", "plinth_dark",
                "plaster_accent_terracotta"} <= m, m
        assert "glass" not in m
        assert not any("__far_" in x or x == "facade_atlas" or x.startswith("hall_wall") for x in m), m
        assert buf.tris(layer, "showroom_glass") == 4              # one pane per glazed run (S and E)
    assert not any(p.mat in ("plaster_light", "plaster_beige", "plaster_white") for p in buf.parts)
    # glass: S wall 0.6...29.4 m at y = 0.1 (recessed), z 100.3...103.5; E wall first half only
    g = np.concatenate([p.V for p in buf.parts if p.layer == "buildings" and p.mat == "showroom_glass"])
    s = g[np.abs(g[:, 1] - 0.10) < 1e-6]
    assert abs(s[:, 0].min() - 0.6) < 1e-6 and abs(s[:, 0].max() - 29.4) < 1e-6
    assert abs(s[:, 2].min() - 100.3) < 1e-6 and abs(s[:, 2].max() - 103.5) < 1e-6
    e = g[np.abs(g[:, 0] - 29.9) < 1e-6]
    assert abs(e[:, 1].min() - 0.6) < 1e-6 and abs(e[:, 1].max() - 10.0) < 1e-6
    # fascia band only on S / E; the N wall is the other colour up to the top
    n = np.concatenate([p.V for p in buf.parts if p.layer == "buildings" and p.mat == "plaster_grey"])
    assert np.allclose(n[:, 1], 20.0) and abs(n[:, 2].max() - 106.0) < 1e-6
    t = np.concatenate([p.V for p in buf.parts if p.layer == "buildings" and p.mat == "plaster_accent_terracotta"])
    assert np.allclose(t[:, 0], 0.0) and abs(t[:, 1].min() - 10.0) < 1e-6 and abs(t[:, 1].max() - 20.0) < 1e-6
    assert abs(t[:, 2].min() - 103.6) < 1e-6 and abs(t[:, 2].max() - 105.0) < 1e-6
    # LOD1 is cheaper than LOD0 but not a plain box
    assert 60 < buf.tris("buildings_low") < buf.tris("buildings") < 1500, (buf.tris("buildings_low"), buf.tris("buildings"))
    assert buf.tris("collision") >= 8
    assert [s_["p"] for s_ in signs] == ["facade_sign_serwis"] and abs(signs[0]["z"] - 105.4) < 1e-6


def test_roof_overhang_slab_reaches_past_the_wall():
    buf, _, _ = _build({"frontage": {"wall": "brick_red", "fascia": {"material": "hall_flashing", "height_m": 0.4,
                                                                    "overhang_m": 0.6}}})
    for layer in ("buildings", "buildings_low"):
        v = np.concatenate([p.V for p in buf.parts if p.layer == layer and p.mat == "hall_flashing"])
        assert abs(v[:, 1].min() + 0.6) < 1e-6 and abs(v[:, 0].max() - 30.6) < 1e-6      # 0.6 m out on every side
        assert v[:, 2].max() <= 106.06


def test_props_stand_where_authored():
    buf, rep, _ = _build({"frontage": SPEC})
    pr = {p["kind"]: p for p in rep["frontage_props"]}
    assert set(pr) == {"flag_row", "totem", "sign_mast"} and all(p["placed"] and p["building"] == "t:1" for p in pr.values())
    # S wall runs from (0, 0) to (30, 0) left to right seen from outside; out = -y
    assert (pr["flag_row"]["e"], pr["flag_row"]["n"]) == (15.0, -8.0)
    assert (pr["totem"]["e"], pr["totem"]["n"]) == (-6.0, -6.0)
    assert (pr["sign_mast"]["e"], pr["sign_mast"]["n"]) == (33.0, -6.0)
    for layer in ("buildings", "buildings_low"):
        y = np.concatenate([p.V for p in buf.parts if p.layer == layer and p.mat == "paint_yellow"])
        # 3 banners x 2 sides; ADR 0129: a bowed mesh (6 x 2 cells on LOD0, 3 x 1 on LOD1), not a rigid quad
        assert buf.tris(layer, "paint_yellow") == (3 * 2 * 2 * 3 if layer == "buildings_low" else 3 * 2 * 2 * 12)
        assert y[:, 2].max() < 108.0 and y[:, 2].min() > 103.0
        o = np.concatenate([p.V for p in buf.parts if p.layer == layer and p.mat == "window_frame"])
        assert abs(o[:, 2].max() - 109.0) < 1e-6 and o[:, 0].max() - o[:, 0].min() > 4.5      # oval board on top, 4.6 m wide
    # rotate_deg turns the row clockwise from the wall direction: 90 deg = masts in a line towards the wall
    b2, _, _ = _build({"frontage": dict(SPEC, props=[dict(SPEC["props"][0], rotate_deg=90, spacing_m=4.0)])})
    y = np.concatenate([p.V for p in b2.parts if p.layer == "buildings" and p.mat == "frontage_galv"])
    y = y[(np.abs(y[:, 0] - 15.0) < 0.1) & (y[:, 1] < -1.0) & (y[:, 2] < 107.0)]     # masts only (not the top arms)
    assert abs(y[:, 1].min() + 12.04) < 1e-6 and abs(y[:, 1].max() + 3.96) < 1e-6
    spec = dict(SPEC, props=[{"kind": "totem", "facing": "NE"}])
    _, rep, _ = _build({"frontage": spec})
    assert rep["frontage_props"] == [{"kind": "totem", "placed": False, "reason": "no wall faces NE", "building": "t:1"}]


class _Acc:
    """Triangle soup per (layer, material) of the frontage prop functions (same calls as buildings_mesh.Acc)."""

    def __init__(self):
        from streetscape import buildings_mesh as BM
        self.acc = BM.Acc()

    def tris(self, layer, mat):
        return [it[0][t] for it in self.acc.d.get((layer, mat), []) for t in it[1]]


def _area(tri):
    return 0.5 * float(np.linalg.norm(np.cross(tri[1] - tri[0], tri[2] - tri[0])))


def test_oval_board_is_two_tone_without_overlap():
    """ADR 0129 (review 0126 P1 "owal czytany jako dysk"): rim + blank light field + colour field, one coplanar
    tessellation per side whose areas add up to the ellipse exactly (no overlap = no z-fighting), a board edge on
    LOD0, no degenerate triangle. No lettering: the light material is two plain fields."""
    import math
    from streetscape import frontage as FR
    a = _Acc()
    q, d, nout = np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([0.0, -1.0])
    FR.sign_mast(a.acc, {"kind": "sign_mast", "height_m": 10.0, "board_w_m": 4.6, "board_h_m": 1.3,
                         "board_dir": "along", "material": "bin_plastic_blue"}, q, d, nout, 100.0)
    for layer, seg in (("buildings", 14), ("buildings_low", 8)):
        blue, light = a.tris(layer, "bin_plastic_blue"), a.tris(layer, "window_frame")
        mid = [t for t in a.tris(layer, "frontage_galv") if t[:, 2].min() > 108.9 and np.allclose(np.abs(t[:, 1]), 0.09)]      # the two blank blocks
        assert blue and light and mid
        blue = blue + mid
        ab, al = sum(_area(t) for t in blue), sum(_area(t) for t in light)
        assert min(_area(t) for t in blue + light) > 1e-5
        full = 2 * math.pi * 2.3 * 0.65                                    # both sides
        assert 0.93 * full < ab + al < full, (layer, ab + al, full)        # polygonal outline: a little under
        assert 0.10 < al / (ab + al) < 0.25, al / (ab + al)                # light rim, the field dominates
        # two sides, 0.18 m apart, every face in one of the two planes (y = +-0.09)
        ys = np.concatenate(blue + light)[:, 1]
        assert np.allclose(np.abs(ys), 0.09)
        z = np.concatenate(light)[:, 2]
        assert abs(z.max() - 110.0) < 1e-6 and abs(z.min() - 108.7) < 1e-6
        # two blank blocks (greeking of the two words), inside the colour field, a gap between them
        assert abs(sum(_area(t) for t in mid) - 2 * ((0.64 - 0.03) * 4.6) * (0.30 * 1.3)) < 1e-6
        mv = np.concatenate(mid)
        assert np.abs(mv[:, 0]).min() == pytest.approx(0.03 * 2.3) and np.abs(mv[:, 0]).max() == pytest.approx(0.64 * 2.3)
    assert a.tris("buildings", "hall_flashing") and not a.tris("buildings_low", "hall_flashing")    # board edge: LOD0
    assert not a.tris("buildings", "downpipe") and a.tris("buildings", "frontage_galv")
    n0, n1 = (len(a.tris(l_, "frontage_galv")) for l_ in ("buildings", "buildings_low"))
    assert n1 < n0 < 700, (n0, n1)
    for l_, cap in (("buildings", 900), ("buildings_low", 500)):                # whole mast + board
        assert sum(len(it[1]) for (l2, _), its in a.acc.d.items() if l2 == l_ for it in its) < cap


def test_banners_are_bowed_not_rigid():
    """ADR 0129 (review 0126 P2 "flagi: sztywne płyty"): the free edge leaves the banner plane towards the hem, each
    banner a little differently; a top arm holds the head."""
    from streetscape import frontage as FR
    a = _Acc()
    FR.flag_row(a.acc, {"kind": "flag_row", "count": 3, "spacing_m": 3.0, "height_m": 8.5, "banner_w_m": 0.8,
                        "banner_h_m": 4.0, "banner_dir": "out", "material": "paint_yellow"},
                np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([0.0, -1.0]), 100.0)
    for layer in ("buildings", "buildings_low"):
        V = np.concatenate(a.tris(layer, "paint_yellow"))
        bows = []
        for x0 in (-3.0, 0.0, 3.0):                                   # banner plane: x = mast, banner hangs towards -y
            v = V[np.abs(V[:, 0] - x0) < 0.6]
            off = np.abs(v[:, 0] - x0)
            assert off[v[:, 2] > 108.3].max() < 1e-6                  # head: on the arm
            assert 0.08 < off.max() < 0.40, off.max()                 # hem: bowed, but still a banner
            assert v[:, 1].min() > -0.95 and v[:, 1].max() < -0.05
            bows.append(round(float(off.max()), 3))
        assert len(set(bows)) == 3, bows


def test_car_row_and_placement():
    from streetscape import frontage as FR
    from streetscape import materials as MT
    spec = dict(SPEC, props=[{"kind": "car_row", "facing": "S", "u": 0.5, "out_m": 6.0, "count": 4, "spacing_m": 2.8,
                             "protos": ["van_white", "car_suv_silver"]}])
    assert FR.plan(spec, MT.M)
    for bad in ("truck_red", "car_suv_pink", "van_blue", "car_coupe_red"):
        with pytest.raises(ValueError):
            FR.plan(dict(SPEC, props=[{"kind": "car_row", "facing": "S", "protos": [bad]}]), MT.M)
    buf, rep, _ = _build({"frontage": spec})
    (pr,) = rep["frontage_props"]
    cars = pr["cars"]
    assert pr["placed"] and [c["p"] for c in cars] == ["van_white", "car_suv_silver"] * 2
    e, n = np.array([c["e"] for c in cars]), np.array([c["n"] for c in cars])
    assert np.allclose(np.diff(e), 2.8, atol=1e-3) and abs(e.mean() - 15.0) < 1e-3 and np.abs(n + 6.0).max() <= 0.121
    # nose out = away from the S wall = towards -y: life.yaw_of((0, -1)) = -pi
    assert all(abs(c["yaw"] + np.pi) < np.radians(1.3) for c in cars)

    class _Pl:
        def __init__(self):
            self.items = [{"p": "car_hatch_red", "e": float(e[0]) - 1.0, "n": -6.0}]

        def add(self, proto, p_, yaw, src=""):
            self.items.append({"p": proto, "e": float(p_[0]), "n": float(p_[1]), "yaw": yaw, "src": src})
    pl, frep = _Pl(), {}
    assert FR.place_cars(pl, rep["frontage_props"], frep) == 3 and frep["frontage_cars"] == {"placed": 3, "skipped": 1}
    assert all(it["src"] == "frontage:t:1:car_row" for it in pl.items[1:])


def test_fence_style_override_and_frontage_materials():
    from streetscape import furniture as FU
    from streetscape import materials as MT
    assert FU.fence_styles([{"kind": "fence_style", "osm_way": [5, 7], "colour": "anthracite"}, {"kind": "landmark"}]) == {
        5: "fence_anthracite", 7: "fence_anthracite"}
    with pytest.raises(ValueError):
        FU.fence_styles([{"id": "x", "kind": "fence_style", "osm_way": [5], "colour": "white"}])
    g, w = MT.M["showroom_glass"], MT.M["glass"]
    assert g["sky_occ"][0] == 0.0 and 0.3 <= g["sky_occ"][1] < w["sky_occ"][1]      # mirrors more sky than a window
    assert g["rough"] == w["rough"] and "texture" not in g and "texture_set" not in g
    # lighter than the fascia over it and the grey wall beside it (review 0126: "czarne pudło")
    assert g["color"][1] > MT.M["plaster_accent_grey"]["color"][1] > MT.M["hall_flashing"]["color"][1]
    m = MT.M["frontage_galv"]
    assert not m.get("metal") and 0.2 < m["color"][1] < 0.35                        # matt: no white clip at overcast


def test_block_overrides_wall_balconies_bands():
    poly = box(0, 0, 60, 12)
    props = {"height_m": 14.35, "function": "budynek wielorodzinny", "storeys": 4}
    base, rep0, _ = _build({}, typ="block", poly=poly, props=props)
    buf, rep, _ = _build({"wall_material": "plaster_light", "balconies": False, "bands": False}, typ="block", poly=poly,
                         props=props)
    assert rep0["balconies"] > 0 and rep["balconies"] == 0
    assert "plaster_light" in buf.mats("buildings") and "panel_concrete" not in buf.mats("buildings")
    assert any(m.startswith("plaster_light__far_") for m in buf.mats("buildings_low"))
    assert not any(m.startswith("plaster_accent") for m in buf.mats("buildings"))


# ------------------------------------------------------------------------------------------ region data
@pytest.fixture(scope="module")
def region_blds():
    from streetscape import buildings_mesh as BM
    fc = json.loads((REGION_DIR / "buildings.geojson").read_text(encoding="utf-8"))
    ov = yaml.safe_load((REGION_DIR / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    return {b["id"]: b for b in BM.load(fc, ORIGIN, ov)}, ov


def test_overrides_target_real_buildings_and_valid_specs(region_blds):
    from streetscape import buildings_mesh as BM
    from streetscape import frontage as FR
    from streetscape import materials as MT
    blds, ov = region_blds
    mine = [o for o in ov if str(o.get("id", "")).startswith("g3b-frontage-")]
    style = [o for o in mine if o.get("kind") == "fence_style"]
    mine = [o for o in mine if "target" in o]
    assert len(style) == 1 and style[0]["colour"] == "anthracite" and 344253283 in style[0]["osm_way"]
    assert len(mine) == 4 and {o["target"]["building"] for o in mine} == set(IDS.values())
    for o in mine:
        assert o.get("reason") and o.get("confidence") in ("low", "medium", "high")
    for k in ("furniture", "cars", "glazed"):
        b = blds[IDS[k]]
        assert b["typ"] == "office", (k, b["typ"])               # not a hall: no docks, no truck zone round a showroom
        spec = FR.plan(b["ovr"]["frontage"], MT.M)
        edges = BM.ring_edges(b["poly"].exterior)
        h = b["props"]["height_m"]
        n_glass = 0
        for a, c_ in edges:
            L = float(np.linalg.norm(c_ - a))
            if L < 0.05:
                continue
            d = (c_ - a) / L
            ops = FR.openings(spec, np.array([d[1], -d[0]]), L, 0.0, h)
            n_glass += len(ops)
            for o_ in ops:
                assert 0.0 < o_[0] < o_[1] < L and 0.0 < o_[2] < o_[3] < h - 0.2
        assert n_glass >= 2, (k, n_glass)                         # glazed runs on the road end and one side
        for g in spec["glazing"]:
            assert g["z"][1] <= h, (k, g)
    assert blds[IDS["block"]]["typ"] == "block"
    assert blds[IDS["block"]]["ovr"] == {"wall_material": "plaster_light", "balconies": False, "bands": False}


def test_heights_and_storeys_come_from_gugik(region_blds):
    """Volumes stay data-driven: BDOT10k footprint, LoD1 2024 height; the overrides change no height."""
    blds, _ = region_blds
    want = {"furniture": 6.55, "cars": 6.11, "glazed": 7.02, "block": 14.35}
    for k, h in want.items():
        p = blds[IDS[k]]["props"]
        assert p["height_source"] == "gugik_lod1_2024" and p["footprint_source"] == "bdot10k" and p["height_m"] == h
        assert "height_m" not in blds[IDS[k]]["ovr"]
    assert blds[IDS["block"]]["props"]["storeys"] == 4


def test_props_clear_of_buildings_and_at_the_orthophoto_spots(region_blds):
    """Mast / flags / totem stand where their shadows start on the orthophoto 2024-05-27 (+-2 m) and in no building."""
    from streetscape import buildings_mesh as BM
    from streetscape import frontage as FR
    from streetscape import materials as MT
    blds, _ = region_blds
    b = blds[IDS["cars"]]
    spec = FR.plan(b["ovr"]["frontage"], MT.M)
    edges = BM.ring_edges(b["poly"].exterior)
    want = {"sign_mast": (-204.5, -300.0), "flag_row": (-168.2, -332.8), "totem": (-162.0, -338.8)}
    rows = [(-170.0, -337.5), (-175.3, -340.8)]                   # ADR 0129: van / car rows on the orthophoto
    seen, cars = set(), []
    for p in spec["props"]:
        q, d, nout = FR._anchor(p, edges)
        if p["kind"] == "car_row":
            assert np.hypot(*(q - np.array(rows[len(cars) // 4]))) < 2.0, (p["kind"], q)
            row = FR.car_row(p, q, d, nout)
            assert len(row) == 4 and all(FR.bearing(nout) == pytest.approx(42.0, abs=1.0) for _ in row)
            for c in row:                                         # noses to the road (NE), clear of every building
                assert abs((np.degrees(c["yaw"]) + 90.0 - 48.0 + 180.0) % 360.0 - 180.0) < 3.0, c
                assert all(x["poly"].distance(Point(c["e"], c["n"])) > 3.0 for x in blds.values()), c
            cars += row
            continue
        assert np.hypot(*(q - np.array(want[p["kind"]]))) < 2.0, (p["kind"], q)
        assert all(x["poly"].distance(Point(*q)) > 1.5 for x in blds.values()), p["kind"]
        assert not p.get("text") and not p.get("label")           # no lettering on advertising structures
        seen.add(p["kind"])
    assert seen == set(want) and len(cars) == 8
    P = np.array([[c["e"], c["n"]] for c in cars])                # no two display vehicles overlap
    dd = np.hypot(*(P[:, None, :] - P[None, :, :]).transpose(2, 0, 1)) + np.eye(len(P)) * 99
    assert dd.min() > 2.5, dd.min()


# ------------------------------------------------------------------------------------------ generated world
@pytest.fixture(scope="module")
def qa():
    p = REGION_DIR / "generated" / "streetscape_qa.json"
    if not p.exists():
        pytest.skip("streetscape_qa.json not generated")
    q = json.loads(p.read_text(encoding="utf-8"))
    if "frontages" not in q.get("buildings", {}):
        pytest.skip("world built before ADR 0126: rerun roads/build_world.py")
    return q


def test_world_has_the_frontage(qa):
    b = qa["buildings"]
    assert b["frontages"] == 3
    pr = b["frontage_props"]
    assert sorted(p["kind"] for p in pr) == ["car_row", "car_row", "flag_row", "sign_mast", "totem"] and all(p["placed"] for p in pr)
    assert all(p["building"] == IDS["cars"] for p in pr)
    assert not any(IDS["furniture"][5:13] in f and "C34A" in f for f in b["dock_facades"])     # showroom: no docks
    assert b["hall_wall_runoff_tris"]["without_uv1"] == 0
