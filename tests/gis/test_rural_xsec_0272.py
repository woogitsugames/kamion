"""ADR 0272: shoulder of kerbless carriageway edges as data (roads/xsec_rules.yaml) - class rule, OSM shoulder tags,
authored override; no kerb / gully / manhole beside a ground shoulder; Ełcka asphalt 6.5-7.1 m; DW671 at the level
crossing; cities (C, Dojlidy) unchanged. Runs on the graphs and overrides in git, no Data/raw."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

from roads import network as Nw  # noqa: E402
from roads import pipeline  # noqa: E402
from roads import standards as S  # noqa: E402
from roads import xsec as X  # noqa: E402

ELCKA_ASPHALT_M = (6.5, 7.1)        # orthophoto 0.1 m: VERIFY-2026-11-15-pr80-pr82 (asphalt 6.5-7.1 m), ADR 0272
ELCKA_WAYS = {716806121, 1024956365, 41533343, 1243220441, 1024956364, 1399803717, 1560819273}
DW671_WAYS = {145989268, 286989055}
DW671_XING_EDGE = "w286989055:1845461231-839431484"
DW671_XING_EN = (758830.85 - 759563.0, 610025.61 - 610559.0)     # OSM node 1778182481, region-local


def _sec(cls, oneway=False, maxspeed=90.0, highway="secondary", ref=None, shoulder=None, osm=None):
    return SimpleNamespace(cls=cls, oneway=oneway, maxspeed=maxspeed, highway=highway, ref=ref, shoulder=shoulder,
                           osm_shoulder=osm)


# ------------------------------------------------------------------------------------------------ rule data
def test_legacy_profile_is_the_pre_0272_constant():
    assert X.LEGACY == (S.PAVED_SHOULDER, S.SHOULDER_W["GP"]) == (1.00, 0.75)
    assert X.decode(0) == X.LEGACY and X.decode(Nw.MAT_FLUSH_ROAD) == X.LEGACY


@pytest.mark.parametrize("cls,oneway,kind,paved,ground,rule", [
    ("G", False, "ground", 0.08, 1.00, "g-single-ground"),
    ("Z", False, "ground", 0.05, 1.00, "z-single-ground"),
    ("L", False, "ground", 0.05, 0.75, "l-d-ground"),
    ("D", True, "ground", 0.05, 0.75, "l-d-ground"),
    ("G", True, "paved", 1.00, 0.75, "legacy-paved"),       # dual carriageway: unchanged (no measurement)
    ("GP", False, "paved", 1.00, 0.75, "legacy-paved"),
    ("GP", True, "paved", 1.00, 0.75, "legacy-paved"),
    ("A", True, "paved", 1.00, 0.75, "legacy-paved"),
    ("S", True, "paved", 1.00, 0.75, "legacy-paved"),
])
def test_road_class_to_shoulder(cls, oneway, kind, paved, ground, rule):
    sh = X.resolve(_sec(cls, oneway), "left")
    assert (sh.kind, sh.paved_m, sh.ground_m, sh.src, sh.force) == (kind, paved, ground, rule, None)
    assert (sh.code == 0) == (rule == "legacy-paved")
    assert X.decode(sh.code) == (paved, ground)


def test_ground_widths_are_inside_ptb2022_par_23_ust_10():
    """Dz.U. 2022 poz. 1518 § 23 ust. 10 pkt 3-5: ground shoulder G 1.25 (>= 0.50), Z 1.00 (>= 0.50), L/D 0.75 (>= 0.50)."""
    for cls, std in (("G", 1.25), ("Z", 1.00), ("L", 0.75), ("D", 0.75)):
        assert 0.50 <= X.resolve(_sec(cls), "left").ground_m <= std


def test_open_road_rule_is_the_old_class_and_speed_rule():
    assert X.rules()["open_road"] == {"classes": ["A", "S", "GP", "G"], "min_speed_kmh": 70}
    assert S.RURAL_MIN_SPEED == 70.0
    assert X.open_road(_sec("G", maxspeed=70.0)) and not X.open_road(_sec("G", maxspeed=50.0))
    assert not X.open_road(_sec("Z", maxspeed=90.0)) and not X.open_road(_sec("G", maxspeed=None))


def test_osm_shoulder_tags():
    paved = X.resolve(_sec("Z", maxspeed=50.0, osm={"shoulder": "both", "shoulder:width": "1.5"}), "right")
    assert (paved.kind, paved.paved_m, paved.force, paved.src) == ("paved", 1.5, "open", "osm:shoulder")
    ground = X.resolve(_sec("Z", osm={"shoulder": "right", "shoulder:width": "0,8 m", "shoulder:surface": "gravel"}), "right")
    assert (ground.kind, ground.paved_m, ground.ground_m, ground.force) == ("ground", 0.05, 0.8, "open")
    other_side = X.resolve(_sec("Z", osm={"shoulder": "right"}), "left")
    assert other_side.force is None and other_side.src == "z-single-ground"
    assert X.resolve(_sec("Z", osm={"shoulder": "no"}), "left").force is None
    assert X.resolve(_sec("Z", osm={"shoulder": "yes"}), "left").paved_m == 1.00         # default_width_m


def test_authored_override_wins_over_osm_and_rule():
    sec = _sec("G", maxspeed=50.0, osm={"shoulder": "both", "shoulder:width": "2"},
               shoulder={"both": {"kind": "ground", "ditch_m": 0.0, "id": "ov"}})
    sh = X.resolve(sec, "left")
    assert (sh.kind, sh.paved_m, sh.ground_m, sh.force, sh.src) == ("ground", 0.08, 1.00, "open", "authored_override:ov")
    assert sh.ditch_m == X.FLAT_DITCH_M
    kerb = X.resolve(_sec("G", shoulder={"left": {"kind": "kerb", "id": "k"}}), "left")
    assert kerb.force == "kerb"
    assert X.resolve(_sec("G", shoulder={"left": {"kind": "kerb", "id": "k"}}), "right").force is None
    wide = X.resolve(_sec("G", shoulder={"both": {"kind": "paved", "paved_m": 1.2, "ground_m": 0.6, "id": "p"}}), "right")
    assert (wide.kind, wide.paved_m, wide.ground_m) == ("paved", 1.2, 0.6)


def test_shoulder_tags_reach_the_graph():
    import osm_extract
    import roadgraph
    assert set(roadgraph.SHOULDER_TAGS) <= set(osm_extract.ROAD_TAGS) and set(roadgraph.SHOULDER_TAGS) <= set(roadgraph.RAW_TAGS)
    a = roadgraph.edge_attrs({"highway": "secondary", "shoulder": "both", "shoulder:width": "1.5"}, 100.0)
    assert a["shoulder"]["v"] == "both" and a["shoulder:width"]["v"] == "1.5"
    assert "shoulder" not in roadgraph.edge_attrs({"highway": "secondary"}, 100.0)


# ------------------------------------------------------------------------------------------------ side profile
def test_ground_shoulder_profile_has_no_kerb_and_keeps_the_topology():
    legacy = Nw.side_profile(Nw.RURAL, 0.6, 0.0, 0.5, 0)
    code = X.resolve(_sec("G"), "left").code
    ground = Nw.side_profile(Nw.RURAL, 0.6, 0.0, 0.5, code)
    assert len(ground) == len(legacy) == 6
    assert [seg[4] for seg in ground] == [seg[4] for seg in legacy]
    assert "curb_concrete" not in {seg[4] for seg in ground}
    assert legacy[0][2] == pytest.approx(1.00) and legacy[1][2] - legacy[1][0] == pytest.approx(0.75)
    assert ground[0][4] == "road_asphalt" and ground[0][2] == pytest.approx(0.08)
    assert ground[1][4] == "shoulder_gravel" and ground[1][2] - ground[1][0] == pytest.approx(1.00)
    assert Nw.side_extent(Nw.RURAL, 0.6, 0.0, 0.5, code) == pytest.approx(Nw.side_extent(Nw.RURAL, 0.6, 0.0, 0.5, 0) - 0.67, abs=0.02)
    flat = Nw.side_profile(Nw.RURAL, X.FLAT_DITCH_M, 0.0, 0.5, code)
    assert min(seg[3] for seg in flat[:5]) > -0.20            # `ditch_m: 0`: no trench beside the shoulder
    assert Nw.walk_mat(code) == "curb_concrete" and Nw.walk_mat(1) == "sidewalk_paving"


def test_manholes_only_beside_a_kerb_or_paved_shoulder():
    g = (0.08, 1.0)
    assert not X.manholes_allowed([g, g])
    assert X.manholes_allowed([None, g]) and X.manholes_allowed([None, None])       # None = kerbed edge
    assert X.manholes_allowed([X.LEGACY, X.LEGACY])                                 # paved shoulder (GP in the city)


# ------------------------------------------------------------------------------------------------ synthetic network
def _graph(highway, maxspeed, width=6.6, extra=None):
    attrs = {"highway": {"v": highway}, "oneway": {"v": "no"}, "lanes": {"v": 2}, "maxspeed": {"v": maxspeed},
             "surface": {"v": "asphalt"}, "width": {"v": width}, **(extra or {})}
    return {"nodes": [{"id": "a", "x": 0.0, "y": 0.0}, {"id": "b", "x": 0.0, "y": 400.0}],
            "edges": [{"id": "w1:a-b", "osm_way": 1, "from": "a", "to": "b", "attrs": attrs,
                       "geometry": [[0.0, 0.0], [0.0, 400.0]]}]}


def _net(graph, overrides=()):
    net = Nw.load(graph, (0.0, 0.0), list(overrides))
    Nw.assign_sides(net, [])
    return net


def _asphalt_width(net, c, s):
    sec = c.section(s, net.sec_list)
    sh = [Nw.side_shoulder(c, sd, s) for sd in ("L", "R")]
    return (None if None in sh else 2 * float(c.hw_at(s)) + sh[0][0] + sh[1][0]), sec


def test_synthetic_rural_g_road_asphalt_width_and_no_kerb():
    net = _net(_graph("secondary", 90))
    (c,) = net.chains
    w, _ = _asphalt_width(net, c, 200.0)
    assert ELCKA_ASPHALT_M[0] <= w <= ELCKA_ASPHALT_M[1] and w == pytest.approx(6.76)
    for side in "LR":
        assert (c.side[side]["kind"] == Nw.RURAL).all()
        mats = {seg[4] for seg in Nw.side_profile(*Nw.side_params(c, side, 200.0))}
        assert mats == {"road_asphalt", "shoulder_gravel", "verge_grass"}
    assert not X.manholes_allowed([Nw.side_shoulder(c, sd, 200.0) for sd in "LR"])


def test_synthetic_trunk_keeps_the_legacy_paved_shoulder():
    net = _net(_graph("trunk", 90, width=8.0))
    (c,) = net.chains
    assert all((c.side[sd]["kind"] == Nw.RURAL).all() and (c.side[sd]["mat"] == 0).all() for sd in "LR")
    assert Nw.side_shoulder(c, "L", 200.0) == (1.00, 0.75)


def test_synthetic_default_speed_road_is_kerbed_until_authored_or_tagged():
    kerbed = _net(_graph("secondary", 50, width=7.0)).chains[0]
    assert all((kerbed.side[sd]["kind"] == Nw.URBAN).all() for sd in "LR")
    assert Nw.side_shoulder(kerbed, "L", 200.0) is None
    ov = [{"id": "t", "target": {"osm_way": 1}, "set": {"shoulder": {"kind": "ground", "ditch_m": 0.0}}}]
    opened = _net(_graph("secondary", 50, width=7.0), ov).chains[0]
    for sd in "LR":
        assert (opened.side[sd]["kind"] == Nw.RURAL).all()
        assert opened.side[sd]["raw"]["h"].max() == pytest.approx(X.FLAT_DITCH_M)
        assert Nw.side_shoulder(opened, sd, 200.0) == (0.08, 1.00)
    one = _net(_graph("secondary", 50, width=7.0), [{"id": "t", "target": {"osm_way": 1}, "set": {"shoulder_left": "ground"}}]).chains[0]
    assert (one.side["L"]["kind"] == Nw.RURAL).all() and (one.side["R"]["kind"] == Nw.URBAN).all()
    tagged = _net(_graph("tertiary", 50, width=6.0, extra={"shoulder": {"v": "both"}, "shoulder:surface": {"v": "gravel"}})).chains[0]
    assert all((tagged.side[sd]["kind"] == Nw.RURAL).all() for sd in "LR")
    kept = _net(_graph("secondary", 90), [{"id": "k", "target": {"osm_way": 1}, "set": {"shoulder": "kerb"}}]).chains[0]
    assert all((kept.side[sd]["kind"] == Nw.URBAN).all() for sd in "LR")
    with pytest.raises(ValueError):
        _net(_graph("secondary", 50), [{"id": "bad", "target": {"osm_way": 1}, "set": {"shoulder": "grass"}}])


# ------------------------------------------------------------------------------------------------ graphs in git
def _region_sides(region_id):
    """The road network with side profiles, as roads.pipeline.build makes it before the heights (no heightfield)."""
    import shapely
    from shapely.geometry import LineString, Polygon
    from roads import junctions as J
    region = pipeline.load_region(region_id)
    origin = (region["origin"]["x"], region["origin"]["y"])
    rdir = pipeline.REGIONS / region_id
    ctx = json.loads((rdir / "generated" / "osm_context.json").read_text(encoding="utf-8"))
    net, _graph_, overrides, _ = pipeline.build_network(region_id)
    net.region_id = region_id
    pts, foot = pipeline.ctx_local(ctx, origin)
    walk = [LineString(np.array(f["geometry"]) - np.array(origin)) for f in ctx["footways"] if f["highway"] != "path"]
    yards = None
    ss = rdir / "generated" / "streetscape_sources.json"
    if ss.exists():
        src = json.loads(ss.read_text(encoding="utf-8"))
        walk += [LineString(np.array(f["geometry"]["coordinates"]) - np.array(origin)) for f in src["bdot10k"]["OT_SKRP_L"]
                 if f["props"].get("materialnawierzchni") not in (None, "grunt naturalny")]
        polys = [Polygon(np.array(f["geometry"]["coordinates"][0]) - np.array(origin)) for f in src["bdot10k"]["OT_PTPL_A"]
                 if f["props"].get("materialnawierzchni") != "grunt naturalny"]
        polys += [Polygon(np.array(a["geometry"]["coordinates"][0]) - np.array(origin)) for a in src["osm"]["areas"]
                  if a["tags"].get("amenity") == "parking"]
        polys += [Polygon(np.array(o["polygon_epsg2180"]) - np.array(origin)) for o in overrides if o.get("kind") == "paved_area"]
        if polys:
            yards = shapely.union_all([shapely.make_valid(p) for p in polys])
            shapely.prepare(yards)
    Nw.assign_sides(net, foot, walkways=walk, yards=yards)
    J.build_junctions(net, pts)
    Nw.assign_sides(net, foot, walkways=walk, yards=yards, trims=True)
    return net


def _way(sec):
    return int(sec.edge_id.split(":")[0].lstrip("w"))


def _stations(net, ways):
    """(chain, station index, section) of every dense station on the given OSM ways, off bridges and roundabouts."""
    for c in net.chains:
        if c.roundabout:
            continue
        for i in range(len(c.line.s)):
            sec = net.sec_list[int(c.sec_idx[i])]
            if _way(sec) in ways and not c.bridge[i]:
                yield c, i, sec


@pytest.mark.parametrize("region_id", ["dk65-02", "dk65-03", "dk65-04", "dk65-05"])
def test_elcka_asphalt_width_matches_the_orthophoto(region_id):
    net = _region_sides(region_id)
    widths, kerbed, n = [], 0, 0
    for c, i, sec in _stations(net, ELCKA_WAYS):
        n += 1
        kinds = [int(c.side[sd]["kind"][i]) for sd in "LR"]
        if kinds != [Nw.RURAL, Nw.RURAL]:
            kerbed += 1          # junction corners, a footway attached to the kerb (village of dk65-04)
            continue
        paved = [X.decode(int(c.side[sd]["mat"][i]))[0] for sd in "LR"]
        assert paved == [0.08, 0.08], (c.id, i)
        if sec.width_src.startswith("authored_override:dk65-elcka-xsec"):
            widths.append(2 * float(c.hw[i]) + sum(paved))
    assert n > 100 and len(widths) > 0.6 * n, (n, len(widths), kerbed)
    widths = np.array(widths)
    # tapers to the bridge (7.5 m) / to BDOT widths at the ends of the override are short: the median is the section
    assert ELCKA_ASPHALT_M[0] <= np.median(widths) <= ELCKA_ASPHALT_M[1]
    assert np.median(widths) == pytest.approx(6.76, abs=0.01)             # was 8.6 m (2 x 1.0 m paved shoulder)
    assert (widths <= ELCKA_ASPHALT_M[1] + 1e-6).mean() > 0.9


@pytest.fixture(scope="module")
def dw671():
    return _region_sides("dw671-tykocin-01")


def test_dw671_has_ground_shoulders_not_kerbs(dw671):
    n = rural = 0
    for c, i, sec in _stations(dw671, DW671_WAYS):
        assert sec.provenance.get("shoulder", "").startswith("authored_override:dw671-ground-shoulder")
        assert sec.edge_lines == "both"
        for sd in "LR":
            n += 1
            d = c.side[sd]
            if int(d["kind"][i]) == Nw.RURAL:
                rural += 1
                assert X.decode(int(d["mat"][i])) == (0.08, 1.00)
                assert "curb_concrete" not in {seg[4] for seg in Nw.side_profile(*Nw.side_params(c, sd, float(c.line.s[i])))}
    assert n > 1500 and rural / n > 0.93, (n, rural)     # the rest: junction corners beside kerbed village streets


def test_dw671_crossing_edge_is_flat_and_unkerbed(dw671):
    hit = 0
    for c in dw671.chains:
        for i in np.where([dw671.sec_list[int(k)].edge_id == DW671_XING_EDGE for k in c.sec_idx])[0]:
            s = float(c.line.s[i])
            if np.hypot(*(c.line.p[i] - np.array(DW671_XING_EN))) > 25.0:
                continue
            hit += 1
            for sd in "LR":
                kind, h, w, depth, mat = Nw.side_params(c, sd, s)
                assert kind == Nw.RURAL and h < 0.12           # no kerb; swale smoothed out to the flat verge
                prof = Nw.side_profile(kind, h, w, depth, mat)
                assert min(seg[3] for seg in prof[:5]) > -0.25  # nothing dug across the track bed
            assert not X.manholes_allowed([Nw.side_shoulder(c, sd, s) for sd in "LR"])
    assert hit >= 10


def test_dw671_no_gullies_and_rail_zone_on_the_paved_road(dw671):
    """Full road mesh on a flat heightfield: gullies only at kerbs; the footprint the rail stage reads at the level
    crossing is the paved road (carriageway + 2 x 0.08 m), not the ground shoulders."""
    from shapely.geometry import LineString
    from roads import build_world as BW
    from roads import decals as D
    from roads.profile import Heightfield
    from streetscape import paved as PV
    rid = "dw671-tykocin-01"
    region = pipeline.load_region(rid)
    origin = (region["origin"]["x"], region["origin"]["y"])
    tm = json.loads((pipeline.REGIONS / rid / "terrain.json").read_text(encoding="utf-8"))
    w_, h_ = tm["samples"]
    wd = pipeline.build(rid, hf=Heightfield(np.full((h_, w_), float(region["origin"]["z"])), tm["bbox"], origin))
    chains = {c.id: c for c in wd.net.chains}
    n0 = len(wd.buf.parts)
    rep = {}
    D.gullies(wd.buf, wd.net, rep)
    assert rep["gullies"] > 0                                   # the kerbed village streets keep theirs
    for p in wd.buf.parts[n0:]:
        cid, side, _k = p.src.split(":", 1)[1].rsplit(":", 2)          # "gully:<chain id>:<side>:<k>"
        c = chains[cid]
        s, _lat = c.line.project(p.V[:, :2].mean(0))
        assert int(Nw.side_params(c, side, float(s))[0]) in (Nw.URBAN, Nw.ISLAND), p.src
        assert _way(c.section(float(s), wd.net.sec_list)) not in DW671_WAYS or \
            Nw.side_shoulder(c, side, float(s)) is None, p.src
    # level crossing: width of the footprint handed to the rail stage, across the road at the crossing node
    c = min((c for c in wd.net.chains if any(wd.net.sec_list[int(k)].edge_id == DW671_XING_EDGE for k in c.sec_idx)),
            key=lambda c: abs(c.line.project(np.array(DW671_XING_EN))[1]))
    s, lat = c.line.project(np.array(DW671_XING_EN))
    assert abs(lat) < 1.0
    p0, nrm = c.line.point(float(s)), c.line.n[c.idx(float(s))]
    cut = LineString([p0 - nrm * 15.0, p0 + nrm * 15.0])
    road = [p for p in wd.buf.parts if p.layer == "road"]
    x0, y0, x1, y1 = cut.buffer(20.0).bounds
    full = PV.road_footprint_polygon(road, (x0, y0, x1, y1))
    zone = PV.road_footprint_polygon([p for p in road if p.mat not in BW.RAIL_ZONE_EXCLUDE_MATS], (x0, y0, x1, y1))
    hw = float(c.hw_at(float(s)))
    assert cut.intersection(zone).length == pytest.approx(2 * hw + 0.16, abs=0.1)
    assert cut.intersection(full).length > 2 * hw + 2.0          # shoulders + flat verge: not part of the crossing
    # REVIEW #138 P1-4: the filter lives inside build_world._rail_plan (both passes plan the same crossing): the
    # crossing spans the paved road only, and all 24 guide posts of the two approaches survive, behind the shoulder
    from streetscape import rail_approach as RA
    plan = BW._rail_plan(wd, rid)
    xc = [x for x in plan.crossings if x["src"] == "osm:node/1778182481"][0]
    assert xc["road_w"] * xc["sin"] == pytest.approx(2 * hw + 0.16, abs=0.15) or         xc["road_w"] == pytest.approx(2 * hw + 0.16, abs=0.15)
    posts = [m for m in RA.plan(plan, wd.net)["markers"] if m["kind"] == "guide_post"]
    assert len(posts) == 24
    for m in posts:
        s2, lat2 = c.line.project(np.array([m["e"], m["n"]]))
        sh = Nw.side_shoulder(c, "L" if lat2 > 0 else "R", float(s2))
        assert sh is not None and abs(lat2) >= float(c.hw_at(float(s2))) + sh[0] + sh[1] + 0.2


# ------------------------------------------------------------------------------------------------ cities unchanged
@pytest.mark.parametrize("region_id", ["bialystok-industrial-c", "bialystok-dojlidy"])
def test_city_regions_keep_their_side_profiles(region_id):
    """C and Dojlidy: no edge is authored / tagged with a shoulder, no single-carriageway class G open road exists, so
    every kerbless station keeps mat 0 = the legacy profile and the kerb decision is the old class / speed rule."""
    net = _region_sides(region_id)
    # the one authored exception (leader decision OD-005, s23): DK8 way 257367422 at the seam to bialystok-maczka keeps
    # a hard edge (kind: kerb) so both tiles share one cross-section family
    od005 = "dk8-seam-kerb-od005-c"

    def authored_ids(sec):
        return {v.get("id") for v in (sec.shoulder or {}).values() if isinstance(v, dict)}

    assert all(sec.osm_shoulder is None and authored_ids(sec) <= {od005} for sec in net.sec_list)
    assert all(v.get("kind") == "kerb" for sec in net.sec_list for v in (sec.shoulder or {}).values())
    if region_id != "bialystok-industrial-c":
        assert all(sec.shoulder is None for sec in net.sec_list)
    rural = 0
    for c in net.chains:
        assert not any(k.startswith(("authored_override", "osm:")) and od005 not in str(k) + str(v)
                       for k, v in c.meta.get("shoulder_src", {}).items())
        for sd in "LR":
            d = c.side[sd]
            m = d["kind"] == Nw.RURAL
            rural += int(m.sum())
            assert (d["mat"][m] == 0).all(), (c.id, sd)
            assert (d["mat"] < X.SHOULDER_CODE).all(), (c.id, sd)
            if m.any():
                sec = net.sec_list[int(c.sec_idx[len(c.sec_idx) // 2])]
                assert X.open_road(sec) and X.class_rule(sec).src == "legacy-paved", (c.id, sec.cls, sec.oneway)
    assert rural > 500      # the fast GP dual carriageways still have their paved shoulders


def test_szosa_elcka_in_bialystok_knyszynska_keeps_its_paved_shoulder():
    """City-edge tile: way 303739903 is class G, two-way, 90 km/h - the rule would give it a ground shoulder; the
    orthophoto shows ~9 m of asphalt, so an authored entry keeps the profile it had (mat 0 = legacy)."""
    net = _region_sides("bialystok-knyszynska")
    n = 0
    for c, i, sec in _stations(net, {303739903}):
        for sd in "LR":
            if int(c.side[sd]["kind"][i]) == Nw.RURAL:
                n += 1
                assert int(c.side[sd]["mat"][i]) == 0
    assert n > 300


# ------------------------------------------------------------------------------------------------ REVIEW #138 fixes
def test_guardrail_stands_on_the_shoulder_of_the_station():
    """P1-1: the W-beam of a kerbless edge used `PAVED_SHOULDER` (1.00 m): 1.60 m from the carriageway edge, base at
    the paved-edge height. With the ground shoulder (0.08 + 1.00 m) that is in the ditch slope, 0.3-0.4 m in the air."""
    from streetscape import furniture as FU
    code = X.resolve(_sec("G"), "left").code
    hw, zg = np.array([3.3, 3.3]), np.array([10.0, 10.0])
    off, zb = FU.rural_barrier_line(np.array([0, code]), hw, zg)
    # legacy station: exactly the pre-0272 line
    assert off[0] == pytest.approx(3.3 + S.PAVED_SHOULDER + S.GUARDRAIL_OFFSET)
    assert zb[0] == pytest.approx(10.0 - S.CROSSFALL * S.PAVED_SHOULDER)
    # ground shoulder: on the gravel, inside its outer edge, at the height of the profile surface there
    prof = Nw.side_profile(Nw.RURAL, S.DITCH_DEPTH, 0.0, 0.5, code)
    gravel = next(seg for seg in prof if seg[4] == "shoulder_gravel")
    u = off[1] - 3.3
    assert gravel[0] < u <= gravel[2] - FU.GUARDRAIL_GROUND_EDGE_M + 1e-9
    z_surface = gravel[1] + (gravel[3] - gravel[1]) * (u - gravel[0]) / (gravel[2] - gravel[0])
    assert zb[1] - 10.0 == pytest.approx(z_surface, abs=1e-6)
    # the old line on the new profile: past the shoulder, on the ditch slope well below the old base height
    u_old = S.PAVED_SHOULDER + S.GUARDRAIL_OFFSET
    assert u_old > gravel[2]
    slope = next(seg for seg in prof if seg[0] <= u_old <= seg[2] and seg[4] == "verge_grass")
    z_old_ground = slope[1] + (slope[3] - slope[1]) * (u_old - slope[0]) / (slope[2] - slope[0])
    assert (-S.CROSSFALL * S.PAVED_SHOULDER) - z_old_ground > 0.3
    # a narrow ground part: the post never leaves it
    narrow = X.Shoulder("ground", 0.05, 0.5, "t").code
    off_n, _ = FU.rural_barrier_line(np.array([narrow]), hw[:1], zg[:1])
    assert off_n[0] - 3.3 == pytest.approx(0.05 + 0.25)


def test_guardrail_rule_no_longer_reads_the_paved_shoulder_constant():
    src = (REPO / "tools/worldgen/streetscape/furniture.py").read_text(encoding="utf-8")
    body = src[src.index("def guardrails(lin, net, zground, report):"):]
    assert "S.PAVED_SHOULDER " not in body and "S.PAVED_SHOULDER\n" not in body and "S.PAVED_SHOULDER)" not in body
    assert body.count("r_off[") == 3 and body.count("r_zb[") == 3      # embankment, beside a structure, deck approach


@pytest.mark.parametrize("st", [{"kind": "ground", "ground_m": 12.0}, {"kind": "ground", "ground_m": -0.5},
                                {"kind": "paved", "paved_m": 4.0}, {"kind": "ground", "ditch_m": -1.0}])
def test_shoulder_override_widths_are_range_checked(st):
    """P2-6: >= 10 m would overflow the side code, a negative width inverts the profile."""
    with pytest.raises(ValueError):
        X.resolve(_sec("G", shoulder={"both": {**st, "id": "bad"}}), "left")


def test_osm_shoulder_width_is_clamped_and_codes_round_trip():
    sh = X.resolve(_sec("Z", osm={"shoulder": "both", "shoulder:width": "25"}), "left")
    assert sh.paved_m == X.MAX_SHOULDER_M and X.decode(sh.code) == (X.MAX_SHOULDER_M, sh.ground_m)
    assert X.decode(X.Shoulder("ground", 0.05, X.MAX_SHOULDER_M, "t").code) == (0.05, X.MAX_SHOULDER_M)


def test_rural_run_after_a_kerbed_run_starts_with_its_own_shoulder(monkeypatch):
    """P2-1: the station a run borrows from the previous profile family carried that family's `mat` (legacy 1.00 m of
    asphalt), a 0.92 m wedge over one station."""
    from roads import meshing as M
    net = _net(_graph("secondary", 90))
    (c,) = net.chains
    code = int(c.side["L"]["mat"][0])
    assert code >= X.SHOULDER_CODE
    n = len(c.line.s)
    half = n // 2
    d = c.side["L"]
    d["kind"][:half] = Nw.URBAN                     # first half kerbed (a village), second half open road
    d["mat"][:half] = 0
    d["raw"]["h"][:half] = S.KERB_HEIGHT
    for k in ("h", "w", "depth"):
        d.setdefault(k, d["raw"][k].copy())
    seen = []
    monkeypatch.setattr(M, "_emit_strip", lambda buf, G, OUT, zg, params, *a, **kw: seen.append(list(params)))
    monkeypatch.setattr(M, "_emit_verge", lambda *a, **kw: None)
    c.crossfall_z = lambda s, lat: np.zeros(len(np.atleast_1d(s)))
    st = c.line.s[::4]
    P = np.array([c.line.point(float(s)) for s in st])
    N = np.array([c.line.n[c.idx(float(s))] for s in st])
    M.build_side_strip(None, c, st, "L", 1.0, P, N, np.full(len(st), 3.3), None, True)
    rural = [run for run in seen if run[-1][0] == Nw.RURAL]
    assert len(seen) == 2 and len(rural) == 1
    assert {p[4] for p in rural[0]} == {code}        # the borrowed first station too


def test_ortho_measurements_in_git_give_the_numbers_of_the_adr():
    """P1-2: the rows behind 'Ełcka: asphalt median 6.75 m, lines 6.2 m' and 'DW671 6.85 m' are in the repository."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("ortho_xsec", REPO / "tools/worldgen/qa/ortho_xsec.py")
    ox = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ox)
    d = REPO / "docs/reports/ortho-xsec-0272"
    rows = lambda *names: [r for nm in names for r in json.loads((d / nm).read_text(encoding="utf-8"))]  # noqa: E731
    elcka = ox.summarise(rows("dk65-04_elcka.json", "dk65-05_elcka.json"))
    assert (elcka["stations"], elcka["clean"], elcka["edge_lines_both"]) == (21, 17, 10)
    assert elcka["asphalt_median_m"] == 6.75 and elcka["edge_line_spacing_median_m"] == 6.2
    assert ELCKA_ASPHALT_M[0] <= elcka["asphalt_median_m"] <= ELCKA_ASPHALT_M[1]
    assert (elcka["asphalt_median_m"] - 6.6) / 2 == pytest.approx(0.08, abs=0.006)        # paved_m of g-single-ground
    dw = ox.summarise(rows("dw671-tykocin-01_dw671.json"))
    assert (dw["clean"], dw["asphalt_median_m"]) == (11, 6.85)
    assert "mapy.geoportal.gov.pl" in ox.WMS_URL and "google" not in ox.WMS_URL.lower()
