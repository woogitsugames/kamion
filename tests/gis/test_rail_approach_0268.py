"""ADR 0268 (owner D71 p. 3): signs / markings of the approach to a level crossing - Dz.U. 2025 poz. 1105 § 79
(A-9 / A-10, G-1a-f, board "Sygnalizacja automatyczna", U-1a, P-4, P-14) with the distances of Dz.U. 2019 poz. 2310
§ 3 ust. 2 and § 78 ust. 2-3; G-2 as a sign plate (§ 81 ust. 1), kerb cut over the crossing panels, crossing devices
after REVIEW s22 0217 visual. No Data/raw needed; the checks of built tiles skip until the tile is regenerated."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import shapely
from shapely.geometry import LineString, Point

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
REGIONS_DIR = REPO / "Data" / "Regions"
RAIL_ON = ("dk65-01", "dk65-02", "dk65-03", "dk65-04", "dw671-tykocin-01")


def _syn(barrier=None, light=None, electrified=None, overrides=(), tile=None, skew=0.0, road_w=7.0):
    """One east-west track and one road through (500, 500); skew = road direction offset from north (deg)."""
    from streetscape import rail as RL
    tags = {"railway": "rail", **({"electrified": electrified} if electrified else {})}
    ntags = {"railway": "level_crossing", **({"crossing:barrier": barrier} if barrier else {}),
             **({"crossing:light": light} if light else {})}
    src = {"osm": {"ways": [{"osm_way": 10, "part": 0, "tags": tags, "coords": [[0.0, 500.0], [1000.0, 500.0]]}],
                   "nodes": [{"osm_node": 1, "tags": ntags, "xy": [500.0, 500.0]}]}}
    dx = 500.0 * math.tan(math.radians(skew))
    road = LineString([(500.0 - dx, 0.0), (500.0 + dx, 1000.0)])
    return RL.Plan(src, (0.0, 0.0), tile, road.buffer(road_w / 2, cap_style=2), [road], overrides=overrides)


def _flat(z=100.0):
    return lambda e, n: np.full(np.shape(e), z) + 0.0 * np.asarray(n)


# ------------------------------------------------------------------------------------------------ the rule
def test_rule_fast_road_with_barriers_category_b():
    from streetscape import rail_approach as RA
    c = _syn(barrier="half", light="yes").crossings[0]
    assert c["category"] == "B"
    r = RA.rule(c, 90.0, 500.0)
    # § 79 pkt 1 lit. a + pkt 6; Dz.U. 2019 poz. 2310 § 3 ust. 2 (150-300 m above 60 km/h) and § 78 ust. 2
    assert r["sign"] == "A-9" and r["board"] and r["case"] == "§ 78 ust. 2" and r["dist_m"] == 150.0
    assert [(round(d, 1), p) for d, p in r["posts"]] == [(150.0, ["A-9", "T-SA", "G-1a"]), (100.0, ["G-1b"]),
                                                         (50.0, ["G-1c"])]
    assert 150.0 <= r["dist_m"] <= 300.0 and not r["t7_required"]
    # § 79 pkt 5 lit. b: guide posts outside the barriers (no post between the barrier and the rails)
    barrier_d = c["half_track"] / c["sin"] + 2.0 - RA.outer_rail_m(c)
    assert r["guide_m"] and min(r["guide_m"]) > barrier_d and len(r["guide_m"]) == 6
    assert np.allclose(np.diff(r["guide_m"]), 3.0)


def test_rule_slow_road_without_barriers_category_d():
    from streetscape import rail_approach as RA
    c = _syn(light="no").crossings[0]
    assert c["category"] == "D"
    r = RA.rule(c, None, 500.0)
    assert r["speed_src"] == "default" and r["sign"] == "A-10" and not r["board"]
    assert r["dist_m"] == 100.0                                   # § 3 ust. 2: up to 100 m
    assert [p for _, p in r["posts"]] == [["A-10", "G-1a"], ["G-1b"], ["G-1c"]]
    assert np.allclose([d for d, _ in r["posts"]], [100.0, 200.0 / 3, 100.0 / 3])
    # § 79 pkt 5 lit. a: 4 m from the outer rail, every 3 m, over 15-20 m of road
    assert r["guide_m"] == [4.0, 7.0, 10.0, 13.0, 16.0, 19.0]
    assert 15.0 <= r["guide_m"][-1] - r["guide_m"][0] <= 20.0 and r["guide_m"][-1] <= 20.0


def test_rule_board_only_for_exact_category_b_or_c():
    from streetscape import rail_approach as RA
    for barrier, light, cat, board in (("half", "yes", "B", True), ("no", "yes", "C", True), ("full", "yes", "A", False),
                                       ("no", "no", "D", False), (None, None, None, False), ("yes", None, "A|B", False),
                                       (None, "yes", "A|B|C", False)):
        c = _syn(barrier=barrier, light=light).crossings[0]
        assert c["category"] == cat
        r = RA.rule(c, 50.0, 500.0)
        assert r["board"] is board, (barrier, light)
        assert r["sign"] == ("A-9" if barrier in ("half", "full", "yes") else "A-10")


def test_rule_short_approaches_follow_par_78_ust_3():
    from streetscape import rail_approach as RA
    c = _syn(light="no").crossings[0]
    r = RA.rule(c, 90.0, 120.0)             # fast road, sign closer than 150 m: two-bar post under it, one-bar at 1/2
    assert r["case"] == "§ 78 ust. 3 zd. 1" and r["dist_m"] == 118.0
    assert [p for _, p in r["posts"]] == [["A-10", "G-1b"], ["G-1c"]]
    assert math.isclose(r["posts"][1][0], r["posts"][0][0] / 2)
    r = RA.rule(c, 50.0, 80.0)              # slow road: any distance up to 100 m is regular
    assert r["case"] == "§ 78 ust. 2" and r["dist_m"] == 78.0 and len(r["posts"]) == 3
    r = RA.rule(c, 50.0, 22.0)              # right at the crossing: one-bar post only
    assert r["case"] == "§ 78 ust. 3 zd. 2" and [p for _, p in r["posts"]] == [["A-10", "G-1c"]]
    r = RA.rule(c, 50.0, 6.0)
    assert r["case"] == "no room" and not r["posts"] and r["dropped"]
    assert RA.rule(c, 50.0, 6.0)["guide_m"] == [4.0]            # guide posts only on the road that exists


def test_rule_t7_flag_on_sharp_angle():
    from streetscape import rail_approach as RA
    c = _syn(light="no", skew=40.0).crossings[0]                  # road 40 deg off the normal: crossing angle 50 deg
    assert c["sin"] < math.sin(math.radians(60.0))
    assert RA.rule(c, 50.0, 500.0)["t7_required"]
    assert not RA.rule(_syn(light="no").crossings[0], 50.0, 500.0)["t7_required"]
    assert not RA.rule(_syn(barrier="half", light="yes", skew=40.0).crossings[0], 50.0, 500.0)["t7_required"]


# ------------------------------------------------------------------------------------------------ markers
def test_plan_positions_sides_and_headings():
    from streetscape import rail as RL
    from streetscape import rail_approach as RA
    p = _syn(barrier="half", light="yes")
    c = p.crossings[0]
    ap = RA.plan(p, speed_kmh=90.0, devices=[m for m in p.markers(0, c, _flat())])
    signs = [m for m in ap["markers"] if m["kind"] == "approach"]
    assert len(signs) == 6 and {m["approach"] for m in signs} == {1, -1}
    rail_d = RA.outer_rail_m(c)
    assert math.isclose(rail_d, RL.GAUGE_DEFAULT_MM / 2000.0, abs_tol=1e-6)
    for m in signs:
        drive = m["approach"] * np.asarray(c["rdir"])
        right = np.array([drive[1], -drive[0]])
        v = np.array([m["e"], m["n"]]) - np.asarray(c["p"])
        assert math.isclose(-float(v @ drive), rail_d + m["dist_m"], abs_tol=0.02)     # before the crossing
        assert float(v @ right) > c["road_w"] / 2                                       # right of the carriageway
        assert m["side"] == "right" and m["heading_deg"] == RL._heading(-drive)         # faces the driver
        assert m["plates"][-1].startswith("G-1") and m["bottom_z_m"] == RA.G1_BOTTOM_Z_M
    assert sorted(m["dist_m"] for m in signs if m["approach"] == 1) == [50.0, 100.0, 150.0]
    posts = [m for m in ap["markers"] if m["kind"] == "guide_post"]
    assert len(posts) == 24 and {m["side"] for m in posts} == {"left", "right"}
    devs = p.markers(0, c, _flat())
    for m in posts:
        assert abs(abs(m["e"] - 500.0) - (c["road_w"] / 2 + RA.U1_LATERAL_M)) < 0.02
        assert all(math.hypot(m["e"] - d["e"], m["n"] - d["n"]) >= 1.0 for d in devs)
    assert len(ap["rules"]) == 2 and all(r["basis"] and r["guide_basis"] for r in ap["rules"])


def test_plan_left_posts_only_on_one_way_and_tile_filter():
    from streetscape import rail_approach as RA
    p = _syn(light="no", tile=shapely.box(0.0, 440.0, 1000.0, 1000.0))    # the tile ends 60 m south of the track
    ap = RA.plan(p, speed_kmh=50.0)
    south = [r for r in ap["rules"] if r["approach"] == 1][0]              # approach 1 drives north (rdir = +N)
    north = [r for r in ap["rules"] if r["approach"] == -1][0]
    assert north["case"] == "§ 78 ust. 2" and north["dist_m"] == 100.0
    assert south["avail_m"] < 60.0 and south["case"] == "§ 78 ust. 3 zd. 1" and south["dist_m"] < 60.0
    tile = p.tile_local
    assert all(tile.contains(Point(m["e"], m["n"])) for m in ap["markers"])
    assert all(m["side"] == "right" for m in ap["markers"] if m["kind"] == "approach")
    assert all(not r["left_posts"] for r in ap["rules"])


# ------------------------------------------------------------------------------------------------ prototypes
def test_every_marker_has_a_prototype_or_plate():
    """REVIEW s21 #102 P0-2: a G-2 marker used to be built as a St Andrew's cross (KeyError 'arm_l_m')."""
    from streetscape import props as PP
    from streetscape import rail_approach as RA
    from streetscape import rail_props as RP
    from streetscape import signs as SG
    seen = set()
    for kw in ({"light": "no"}, {"barrier": "half", "light": "yes"}, {"barrier": "double_half", "light": "yes"},
               {"barrier": "full", "light": "yes"}, {"barrier": "no", "light": "yes"}, {}):
        p = _syn(electrified="contact_line", **kw)
        c = p.crossings[0]
        devs = p.markers(0, c, _flat())
        for m in devs + RA.plan(p, speed_kmh=90.0, devices=devs)["markers"]:
            seen.add((m["kind"], m.get("code")))
            if m["kind"] == "bell":
                continue                                           # rides the signal mast (signal_rail_lamps_bell)
            if m["kind"] == "approach" or (m["kind"] == "sign" and m["code"] == "G-2"):
                for code in m.get("plates", [m.get("code")]):
                    assert code in SG.FACES
                    lod0, lod1, _ = PP.plate(code)
                    assert f"sign_{code}" in lod0.prims and f"sign_{code}" in lod1.prims
                assert RP.proto_name(m) is None
                continue
            name = RP.proto_name(m)
            assert name and name.startswith("signal_rail_"), m      # LOD class of crossing devices (250 m cull)
            lod0, lod1, col = RP.build(name, m)
            assert lod0.prims and col is not None
    assert {("sign", "G-2"), ("sign", "G-3"), ("light", None), ("barrier", None), ("approach", None),
            ("guide_post", None)} <= seen


def test_g2_never_builds_a_cross_and_category_b_has_no_cross():
    """§ 80 ust. 1: G-3 / G-4 only at category A without barriers, C and D; § 81 ust. 1: G-2 on the signal mast
    (A-C) or under the cross (D)."""
    from streetscape import rail_props as RP
    p = _syn(barrier="double_half", light="yes", electrified="contact_line")
    mk = p.markers(0, p.crossings[0], _flat())
    assert not [m for m in mk if m["kind"] == "sign" and m["code"] in ("G-3", "G-4")]
    g2 = [m for m in mk if m.get("code") == "G-2"]
    assert len(g2) == 2 and all(m["mount"] == "signal_mast" and RP.proto_name(m) is None for m in g2)
    d = _syn(light="no", electrified="contact_line")
    mk = d.markers(0, d.crossings[0], _flat())
    assert [m["mount"] for m in mk if m.get("code") == "G-2"] == ["below_cross"] * 2
    assert len([m for m in mk if m.get("code") == "G-3"]) == 2


class _Placer:
    def __init__(self):
        self.items, self.pts = [], {}

    def add(self, proto, p, yaw, z=None, sz=1.0, src="", group=None):
        z = 100.0 if z is None else z
        self.items.append({"p": proto, "e": p[0], "n": p[1], "z": z, "yaw": yaw, "src": src, "sz": sz})
        return z


def test_place_g2_heights_and_instances():
    from streetscape import rail_props as RP
    from streetscape import signs as SG
    h = SG.RECT["G-2"][1]
    # category D: under the cross, on its post
    p = _syn(light="no", electrified="contact_line")
    pl, rep, codes = _Placer(), {}, set()
    RP.place(pl, p, _flat(), rep, codes=codes)
    assert rep["rail_crossing_devices"] == {"plate_G-2": 2, "signal_rail_saltire_g3": 2} and codes == {"G-2"}
    cross = [m for m in p.markers(0, p.crossings[0], _flat()) if m.get("code") == "G-3"][0]
    lower, top = RP.saltire_top_bottom(cross)
    for it in pl.items:
        if it["p"] == "plate_G-2":
            assert it["z"] + h / 2 < 100.0 + lower and it["z"] - h / 2 > 100.0 + 0.5      # below the cross, off the ground
    # category B: on the signal mast under the lamp backboards
    p = _syn(barrier="half", light="yes", electrified="contact_line")
    pl, rep = _Placer(), {}
    RP.place(pl, p, _flat(), rep)
    assert rep["rail_crossing_devices"]["plate_G-2"] == 2 and "signal_rail_saltire_g3" not in rep["rail_crossing_devices"]
    lamps_low = 100.0 + RP.SIGNAL_LAMP_Z_M - RP.SIGNAL_DISC_D_M / 2
    masts = {(it["e"], it["n"]) for it in pl.items if it["p"].startswith("signal_rail_lamps")}
    for it in pl.items:
        if it["p"] == "plate_G-2":
            assert it["z"] + h / 2 <= lamps_low and (it["e"], it["n"]) in masts
    # not electrified: no G-2
    pl, rep = _Placer(), {}
    RP.place(pl, _syn(light="no"), _flat(), rep)
    assert "plate_G-2" not in rep["rail_crossing_devices"]


def test_plate_stack_and_new_plate_shapes():
    from roads import standards as S
    from streetscape import props as PP
    from streetscape import rail_props as RP
    from streetscape import signs as SG
    stack, top = RP.plate_stack(["A-9", "T-SA", "G-1a"], 1.0)
    z = dict(stack)
    tri_h = S.SIGN_SIZE["triangle"] * math.sqrt(3) / 2
    assert math.isclose(z["G-1a"], 1.0 + 0.5) and math.isclose(z["T-SA"], 2.05 + SG.RECT["T-SA"][1] / 2)
    tri_low = 2.05 + SG.RECT["T-SA"][1] + 0.05
    assert tri_low >= S.SIGN_H_MIN                                   # the warning sign keeps the 2.0 m of Table 1.11
    assert math.isclose(z["A-9"], tri_low + tri_h / 3) and math.isclose(top, tri_low + tri_h + 0.05)
    for code, (w, h) in SG.RECT.items():
        m, _, _ = PP.plate(code)
        V = np.vstack(m.prims[f"sign_{code}"][0])
        assert math.isclose(np.ptp(V[:, 0]), w, abs_tol=1e-6) and math.isclose(np.ptp(V[:, 2]), h, abs_tol=1e-6)
    m, _, _ = PP.plate("A-10")                                         # upright: apex above the centroid
    V = np.vstack(m.prims["sign_A-10"][0])
    assert math.isclose(V[:, 2].max(), 2 * tri_h / 3, abs_tol=1e-6) and math.isclose(V[:, 2].min(), -tri_h / 3, abs_tol=1e-6)
    m, _, _ = PP.plate("A-7")                                          # the inverted A-7 is untouched
    V = np.vstack(m.prims["sign_A-7"][0])
    assert math.isclose(V[:, 2].min(), -2 * tri_h / 3, abs_tol=1e-6)
    for k, n in zip("abcdef", (3, 2, 1, 3, 2, 1)):                     # 3 / 2 / 1 bars; a-c and d-f are mirror images
        im = np.asarray(SG.face(f"G-1{k}")[1].convert("RGB")).astype(int)
        red = (im[:, im.shape[1] // 2, 0] > 150) & (im[:, im.shape[1] // 2, 1] < 90)
        runs = int(np.sum(np.diff(red[12:-12].astype(int)) == 1))
        assert runs == n, (k, runs)
    a, d = (np.asarray(SG.face(f"G-1{k}")[1]) for k in "ad")
    assert np.array_equal(a, d[:, ::-1])


def test_signal_mast_banded_and_saltire_bands():
    from streetscape import rail_props as RP
    m, l1, _ = RP.signal()
    for mesh in (m, l1):
        assert {"paint_ral3020", "paint_white_reflective"} <= set(mesh.prims) and "steel_galv" not in mesh.prims
    m, _, _ = RP.saltire("G-3")
    assert {"paint_ral3020", "paint_white_reflective", "steel_galv"} <= set(m.prims)
    red = np.vstack(m.prims["paint_ral3020"][0])
    r = np.hypot(red[:, 0], red[:, 2] - red[:, 2].mean())
    assert r.min() > 0.1                                               # the centre of the cross is white
    b, _, _ = RP.barrier(4.0)
    assert "drive_cabinet_faded" in b.prims and "cone_orange" not in b.prims
    from streetscape import materials as MT
    assert "drive_cabinet_faded" in MT.M


# ------------------------------------------------------------------------------------------------ kerb cut
class _Line:
    def __init__(self, pts):
        from roads.geom import Polyline
        self._pl = Polyline(np.asarray(pts, float))
        self.p, self.s = self._pl.p, self._pl.s

    def __getattr__(self, k):
        return getattr(self._pl, k)


class _Chain:
    def __init__(self, pts, kind, h=0.12, hw=3.5):
        from roads import network as NW
        from roads.geom import Polyline
        self.id = "c1"
        self.line = Polyline(np.asarray(pts, float))
        n = len(self.line.s)
        self.side = {s: {"kind": np.full(n, kind), "h": np.full(n, h), "mat": np.zeros(n, int)} for s in "LR"}
        self.meta, self._hw = {}, hw
        self.NW = NW

    def hw_at(self, s):
        return np.full(np.shape(s), self._hw) if np.ndim(s) else self._hw


class _Net:
    def __init__(self, chains):
        self.chains = chains


def test_attach_cuts_kerbs_over_the_panels_only():
    from roads import network as NW
    from streetscape import rail as RL
    from streetscape import rail_approach as RA
    p = _syn(barrier="double_half", light="yes",
             overrides=[{"id": "o", "kind": "rail_crossing", "target": {"osm_node": 1}, "set": {"panel_margin_m": 1.5}}])
    c = p.crossings[0]
    ch = _Chain([(500.0, y) for y in np.arange(400.0, 600.01, 0.5)], NW.URBAN)
    rep = RA.attach(_Net([ch]), p)
    assert rep["crossings"] == 1 and not rep["missed"] and rep["kerb_cut_m"] > 0
    s = np.asarray(ch.line.s)
    d = np.abs(s - 100.0)
    panel_half = c["half_track"] / c["sin"]
    for side in "LR":
        h = ch.side[side]["h"]
        assert np.all(h[d <= panel_half + RA.KERB_CUT_MARGIN_M] == 0.0)        # flush under the panels + margin
        assert np.all(h[d >= panel_half + RA.KERB_CUT_MARGIN_M + RA.KERB_RAMP_M + 0.5] == 0.12)   # untouched outside
        assert np.all(np.diff(h[s <= 100.0]) <= 1e-9) and np.all(np.diff(h[s >= 100.0]) >= -1e-9)
    assert RL.PANEL_LIFT > 0.0                                                   # panels above the flush kerb
    x = ch.meta["rail_xings"][0]
    assert math.isclose(x["s"], 100.0, abs_tol=0.01) and x["category"] == "B"
    assert math.isclose(x["device_d"], panel_half + RL.SIGN_SETBACK)
    # a rural profile keeps (fills) its ditch like a driveway, a skewed crossing cuts a longer kerb
    rur = _Chain([(500.0, y) for y in np.arange(400.0, 600.01, 0.5)], NW.RURAL, h=0.6)
    RA.attach(_Net([rur]), p)
    assert rur.side["L"]["h"].min() < 0.1 and rur.side["L"]["h"].max() == 0.6
    ps = _syn(light="no", skew=30.0)
    L = ps.road_lines[0]
    sk = _Chain([L.interpolate(d).coords[0] for d in np.arange(0.0, L.length, 0.5)], NW.URBAN)
    RA.attach(_Net([sk]), ps)
    cut = lambda chn: float(np.sum(chn.side["L"]["h"] == 0.0)) * 0.5
    st = _Chain([(500.0, y) for y in np.arange(400.0, 600.01, 0.5)], NW.URBAN)
    RA.attach(_Net([st]), _syn(light="no"))
    assert cut(sk) > cut(st) > 0


def test_override_guide_post_key_and_unknown_key():
    from streetscape import rail as RL
    from streetscape import rail_approach as RA
    ov = [{"id": "o", "kind": "rail_crossing", "target": {"osm_node": 1},
           "set": {"barrier": "double_half", "light": True, "light_left": True, "panel_margin_m": 1.5,
                   "guide_post": "red_white"}}]
    p = _syn(overrides=ov)
    assert p.crossings[0]["category"] == "B" and p.crossings[0]["equipment_src"] == "authored_override"
    assert p.report["overrides_applied"] == [{"id": "o", "target": "osm:node/1"}]
    posts = [m for m in RA.plan(p, speed_kmh=90.0)["markers"] if m["kind"] == "guide_post"]
    assert posts and all(m["style"] == "red_white" for m in posts)
    with pytest.raises(ValueError):
        _syn(overrides=[{"id": "bad", "kind": "rail_crossing", "target": {"osm_node": 1}, "set": {"colour": 1}}])
    assert set(RL.OVERRIDE_KEYS) == {"barrier", "light", "light_left", "bell", "saltire", "panel_margin_m", "guide_post",
                                     "approach_speed_kmh"}


def test_approach_post_never_stands_on_a_side_road():
    """A G-1 post whose nominal station falls in the mouth of a side road slides along the road (shifted_m)."""
    from shapely.geometry import box
    from streetscape import rail_approach as RA
    p = _syn(barrier="half", light="yes")
    base = [m for m in RA.plan(p, speed_kmh=90.0)["markers"] if m["kind"] == "approach" and m["plates"] == ["G-1c"]]
    g = [m for m in base if m["approach"] == 1][0]
    assert "shifted_m" not in g
    p.road_poly = p.road_poly.union(box(g["e"] - 2.0, g["n"] - 2.5, g["e"] + 30.0, g["n"] + 2.5))   # side road, 5 m
    out = RA.plan(p, speed_kmh=90.0)
    h = [m for m in out["markers"] if m["kind"] == "approach" and m["plates"] == ["G-1c"] and m["approach"] == 1][0]
    assert h["shifted_m"] and 2.0 <= abs(h["shifted_m"]) <= 4.0
    assert not p.road_poly.buffer(-0.05).contains(Point(h["e"], h["n"]))
    assert abs(h["dist_m"] - (g["dist_m"] + h["shifted_m"])) < 0.11


def test_speed_source_is_reported_and_override_wins():
    """A graph default (attrs.maxspeed.src == 'default') is never reported as a known limit; the authored
    approach_speed_kmh of the crossing decides the § 3 ust. 2 bracket (150-300 m above 60 km/h)."""
    from roads import network as NW
    from streetscape import rail_approach as RA
    e = {"id": "e", "attrs": {"highway": {"v": "secondary", "src": "osm"}, "maxspeed": {"v": 50, "src": "default"}}}
    assert NW.edge_section(e).maxspeed_src == "default"
    c = _syn(barrier="half", light="yes").crossings[0]
    assert RA.rule(c, 50.0, 500.0, speed_src="default")["speed_src"] == "default"
    assert RA.rule(c, 50.0, 500.0, speed_src="osm")["speed_src"] == "osm"
    assert RA.rule(c, None, 500.0, speed_src="osm")["speed_src"] == "default"
    ov = [{"id": "o", "kind": "rail_crossing", "target": {"osm_node": 1},
           "set": {"barrier": "double_half", "light": True, "approach_speed_kmh": 90}}]
    r = [x for x in RA.plan(_syn(overrides=ov), speed_kmh=50.0)["rules"] if "sign" in x]
    assert r and all(x["speed_src"] == "authored_override" and x["speed_kmh"] == 90.0 and x["dist_m"] == 150.0
                     for x in r)
    assert all([round(p["dist_m"], 1) for p in x["posts"]] == [150.0, 100.0, 50.0] for x in r)


def test_dw671_override_builds_in_the_real_tile():
    """REVIEW s21 #102 P0-1: the authored override of DW671 (light_left, panel_margin_m) must pass the one mechanism."""
    import yaml
    from streetscape import rail as RL
    rid = "dw671-tykocin-01"
    ry = yaml.safe_load((REGIONS_DIR / rid / "region.yaml").read_text(encoding="utf-8"))
    ov = yaml.safe_load((REGIONS_DIR / rid / "overrides.yaml").read_text(encoding="utf-8"))
    ov = ov.get("overrides", ov) if isinstance(ov, dict) else ov
    src = json.loads((REGIONS_DIR / rid / "generated" / "rail_sources.json").read_text(encoding="utf-8"))
    o = (ry["origin"]["x"], ry["origin"]["y"])
    g = json.loads((REGIONS_DIR / rid / "roads.graph.json").read_text(encoding="utf-8"))
    lines = [shapely.affinity.translate(LineString(e["geometry"]), -o[0], -o[1]) for e in g["edges"]
             if len(e["geometry"]) >= 2]
    p = RL.Plan(src, o, None, shapely.union_all([L.buffer(3.5, cap_style=2) for L in lines]), lines, overrides=ov)
    c = [c for c in p.crossings if c["src"] == "osm:node/1778182481"][0]
    assert c["barrier"] == "double_half" and c["light"] and c["light_left"] and c["category"] == "B"
    assert c["equipment_src"] == "authored_override" and not p.report.get("overrides_stale")
    assert p.sign_code(c) is None                                  # § 80 ust. 1: no G-3 at category B


# ------------------------------------------------------------------------------------------------ built tiles
@pytest.mark.parametrize("rid", RAIL_ON)
def test_built_tile_carries_the_approach(rid):
    p = REGIONS_DIR / rid / "generated" / "rail.json"
    if not p.exists():
        pytest.skip("tile not built with the rail stage yet")
    d = json.loads(p.read_text(encoding="utf-8"))
    if "approach_rules" not in d:
        pytest.skip("tile built before ADR 0268 - regenerate (build_world)")
    assert len(d["crossings"]) == d["approach_attach"]["crossings"] and not d["approach_attach"]["missed"]
    tile = None
    for r in d["approach_rules"]:
        if "sign" not in r:
            continue
        c = d["crossings"][r["crossing"]]
        with_barriers = c["barrier"] in ("half", "double_half", "full", "gate", "yes", "chain")
        assert r["sign"] == ("A-9" if with_barriers else "A-10")
        assert r["board"] == (c["category"] in ("B", "C"))
        if r["case"] == "§ 78 ust. 2":
            assert (150.0 <= r["dist_m"] <= 300.0) if r["speed_kmh"] > 60 else (r["dist_m"] <= 100.0)
    for m in d["approach"]:
        assert m["kind"] in ("approach", "guide_post")
    if d["crossings"]:
        assert any(m["kind"] == "approach" for m in d["approach"]) or all(
            r.get("case") in ("no room", "no approach (one-way against, or no chain)") or r.get("dropped")
            for r in d["approach_rules"])
    if rid == "dw671-tykocin-01":
        r = [x for x in d["approach_rules"] if "sign" in x]
        assert r and all(x["sign"] == "A-9" and x["board"] for x in r)
        man = json.loads((REGIONS_DIR / rid / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
        assert man is not None
