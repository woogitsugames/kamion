"""ADR 0237: sidewalk surface types, kerb drops at pedestrian crossings, red block / slab materials (research R6).

Synthetic cases + the git data of bialystok-industrial-c and bialystok-dojlidy (no Data/raw needed)."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml
from shapely.geometry import LineString, Polygon

from roads import meshing as M
from roads import network as NW
from roads import standards as S
from streetscape import cycleways as CY
from streetscape import materials as MT
from streetscape import paved as PV
from streetscape import pavements as PVM
from streetscape import plots as PL

REPO = Path(__file__).resolve().parents[2]
REGIONS = ("bialystok-industrial-c", "bialystok-dojlidy")
RULES = [{"id": "r", "kind": "pavement_rules", "sidewalk_bdot": True, "crossing_kerb_drops": True}]


def _region(rid):
    d = REPO / "Data" / "Regions" / rid
    reg = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
    ov = yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    return d, (reg["origin"]["x"], reg["origin"]["y"]), ov


def _json(p):
    return json.loads(p.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------ rule
def test_rule_priority_override_osm_bdot_typology_default():
    c = PVM.classify
    assert c() == ("paving_grey", "default")
    assert c(bdot_material="masa bitumiczna") == ("asphalt", "bdot10k_SKRP")
    assert c(bdot_material="płyty betonowe") == ("slabs", "bdot10k_SKRP")
    assert c(bdot_material="kostka prefabrykowana") == ("paving_grey", "bdot10k_SKRP")
    assert c(bdot_material="grunt naturalny") == ("paving_grey", "default")            # not a paved footway
    assert c(bdot_material="masa bitumiczna", use_bdot=False) == ("paving_grey", "default")
    assert c(osm_surface="concrete:plates", bdot_material="masa bitumiczna") == ("slabs", "osm_surface")
    assert c(override="paving_red", osm_surface="asphalt", bdot_material="płyty betonowe")[0] == "paving_red"
    # street class + building typology: only on local streets beside blocks, only when the region asks for it
    assert c(highway="residential", near_blocks=True, estate_slabs=True) == ("slabs", "typology(WORKING_VALUE)")
    assert c(highway="residential", near_blocks=True, estate_slabs=False)[0] == "paving_grey"
    assert c(highway="trunk", near_blocks=True, estate_slabs=True)[0] == "paving_grey"
    assert c(highway="residential", near_blocks=False, estate_slabs=True)[0] == "paving_grey"
    assert c(highway="residential", near_blocks=True, estate_slabs=True, bdot_material="kostka prefabrykowana")[0] == "paving_grey"


def test_surface_types_have_materials_with_existing_texture_sets():
    spec = _json(REPO / "art-source" / "world" / "materials" / "materials_spec.json")["sets"]
    for surface, mat in PVM.MATERIAL.items():
        assert PVM.material_of(surface) == mat and PVM.material_of(mat) == mat
        assert mat in MT.M, mat
        assert MT.M[mat]["texture_set"] in spec, (mat, MT.M[mat]["texture_set"])
    with pytest.raises(ValueError):
        PVM.material_of("marble")
    # red blocks: a modulation set of the grey block scan, sampled in plan metres; the old `paving_red` never existed
    assert "paving_red" not in spec
    for mat in ("sidewalk_paving_red", "cycle_red"):
        d = MT.M[mat]
        assert d["texture_set"] == "paving_20x10_tint" and d["uv"] == "planar"
        r, g, b = d["color"]
        assert r > 1.5 * g and abs(g - b) < 0.03                    # red-brown, not pink (r / g of the old flat red: 3.3)
        assert 0.10 < 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.26   # darker than the grey blocks beside it
    tint, grey = spec["paving_20x10_tint"], spec["paving_20x10_grey"]
    assert tint["kind"] == "modulation_set" and tint["tile_m"] == grey["tile_m"]
    assert tint["source"]["elements_per_tile"] == grey["source"]["elements_per_tile"]
    assert tint["albedo"]["mean_rgb_linear"] == pytest.approx([0.5, 0.5, 0.5], abs=0.02)
    assert spec["sidewalk_slab_35"]["slots"] == ["sidewalk_slabs"]
    # footways keep the wear of the grey blocks
    for mat in ("sidewalk_slabs", "sidewalk_paving_red"):
        assert MT.M[mat]["ground_grime"] == MT.M["sidewalk_paving"]["ground_grime"]
        assert mat in PV.EDGED


def test_town_fallback_is_stable_by_way_and_yields_to_sourced_surfaces():
    points = np.array([[10.0, 10.0], [100.0, 100.0]])
    highways = {way: "residential" for way in range(1, 101)}
    highways[101] = "secondary"
    rules = {"mixed_sidewalks": True, "older_sidewalks": True}
    zones = PVM.Zones(rules, way_highway=highways)
    seen = set()
    for way in highways:
        surfaces, _, _ = PVM.surface_types(points, way, zones)
        assert surfaces[0] == surfaces[1]
        assert np.array_equal(surfaces, PVM.surface_types(points[::-1], way, zones)[0])
        seen.update(surfaces)
    assert seen == set(PVM.MIXED_SURFACES)
    assert PVM.surface_types(points, 101, zones)[0].tolist() == ["paving_grey"] * 2
    zones.rules = {"mixed_sidewalks": True}
    assert all(PVM.surface_types(points, way, zones)[0][0].startswith("paving_") for way in highways)
    zones.osm = [(LineString([(9, 10), (11, 10)]), "asphalt")]
    assert PVM.surface_types(points, 1, zones)[0][0] == "asphalt"
    zones.ways[1] = ("owner", "paving_red")
    assert PVM.surface_types(points, 1, zones)[0].tolist() == ["paving_red"] * 2


def test_town_surface_boundaries_survive_welding_as_one_primitive():
    from roads import build_world

    vertices = np.array([[0., 0., 0.], [1., 0., 0.], [1., 1., 0.], [0., 1., 0.]])
    faces = np.array([[0, 1, 2], [0, 2, 3]])
    parts = [M.Part("road", "sidewalk_paving", vertices, vertices[:, :2], faces, True, "w17")]
    zones = PVM.Zones({"mixed_sidewalks": True}, polys=[
        ("slabs", Polygon([(0.55, 0.), (1., 0.), (1., 1.), (0.55, 1.)]), "slabs")
    ])
    report = PVM.retype_sidewalks(parts, zones)
    primitive, = next(iter(build_world.assemble(parts, {"road"}, 128, mixed_sidewalks=True).values()))["road"]
    assert primitive["mat"] == "sidewalk_paving"
    assert report["tris_in"] == report["tris_out"] == len(primitive["T"]) == 2
    assert len(primitive["V"]) == 6
    assert {tuple(color) for color in primitive["COL"]} == {(0., 0., 0., 1.), (2 / 3, 0., 0., 1.)}
    assert all(np.ptp(primitive["COL"][face, 0]) == 0 for face in primitive["T"])


def test_behaton_scaled_to_the_polish_double_t_block():
    """R6-023: double-T block 198 x 163 mm. The scan's block pitch is 275 x 160 mm (measured), so the 1.92 m tile
    laid blocks 37 % too long; the review's x 1.16 assumed 140 mm rows in the scan (ADR 0063 text), not a measurement."""
    b = _json(REPO / "art-source" / "world" / "materials" / "materials_spec.json")["sets"]["behaton_i_grey"]
    along, two_rows = b["source"]["measured_period_m"]
    assert along == pytest.approx(0.2747, abs=0.003) and two_rows == pytest.approx(0.3197, abs=0.003)
    sx, sy = b["source"]["scale_to_standard_xy"]
    assert along * sx == pytest.approx(0.201, abs=0.001)             # 198 mm block + 3 mm joint
    assert two_rows * sy == pytest.approx(0.289, abs=0.001)          # 163 + waist 120 + 2 joints
    assert b["tile_m"] == pytest.approx([1.92 * sx, 1.92 * sy], abs=0.002)
    assert sx < 1.0 and sy < 1.0                                     # blocks get smaller, not x 1.16 larger


def test_gully_grate_is_the_620_x_420_frame():
    from roads import decals as DC
    from streetscape import life as LF
    assert DC.GULLY_SIZE == LF.GULLY_SIZE == (0.42, 0.62)            # (across, along): long side along the kerb


# ------------------------------------------------------------------------------------------------ kerb drops
def _chain(cid="c1", n=121, hw=3.5, t_a=6.0, t_b=6.0, h=S.KERB_HEIGHT, mat=1, kind=NW.URBAN, bridge=None):
    s = np.arange(n) * 0.5
    p = np.column_stack([s, np.zeros(n)])

    def project(q):
        return float(np.clip(q[0], 0, s[-1])), float(q[1])
    side = {"kind": np.full(n, kind), "h": np.full(n, h), "mat": np.full(n, mat)}
    return SimpleNamespace(id=cid, meta={}, line=SimpleNamespace(s=s, p=p, project=project), hw_at=lambda _s: hw,
                           t_a=t_a, t_b=t_b, length=float(s[-1]), bridge=bridge,
                           idx=lambda x: int(np.clip(round(x / 0.5), 0, n - 1)),
                           side={"L": side, "R": {k: v.copy() for k, v in side.items()}})


def _pt(e, n, **kw):
    return dict({"kind": "highway=crossing", "osm_node": 1, "e": e, "n": n}, **kw)


def test_kerb_sources_are_cited_and_the_drop_is_two_centimetres():
    assert PVM.CROSSING_KERB_M == 0.02 and "§ 127 ust. 10" in PVM.KERB_SOURCES["crossing_m"]["src"]
    lo, hi = PVM.KERB_SOURCES["reveal_exception_m"]["value"]
    assert lo <= S.KERB_HEIGHT <= hi                                 # 0.13 m: inside 6-16 cm (R6-002/003) ...
    assert S.KERB_HEIGHT > PVM.KERB_SOURCES["reveal_default_m"]["value"][1]      # ... 1 cm above the OST default
    assert PVM.KERB_SOURCES["act_2022_number"]["value"] is None      # Dz.U. 2022 poz. 1518 names no number (R6-005)
    for k, v in PVM.KERB_SOURCES.items():
        assert v["status"].split()[0] in ("SOURCED", "WORKING_VALUE") and v["row"].startswith("R6-"), k
    assert PL.DROP_H_M == PVM.KERB_SOURCES["driveway_m"]["value"]
    assert PL.DROP_RAMP_M == PVM.CROSSING_RAMP_M == PVM.KERB_SOURCES["ramp_m"]["value"]


def test_crossing_lowers_both_kerbs_over_the_zebra_with_ramps():
    c = _chain()
    net = SimpleNamespace(chains=[c])
    st = {}
    drops = PVM.crossing_drops(net, [_pt(30.0, 0.4, crossing="uncontrolled")], RULES, st)
    assert [d["side"] for d in drops] == ["L", "R"] and st["dropped"] == 1 and st["shortened"] == 0
    assert all(d["kerb_only"] and d["h"] == 0.02 and d["half"] == S.P10_WIDTH / 2 for d in drops)
    n_before = {k: len(c.side[k]["h"]) for k in "LR"}
    assert PL.apply_drops(net, drops) == 2
    s = c.line.s
    for k in "LR":
        h = c.side[k]["h"]
        assert len(h) == n_before[k]                                              # no station added
        assert np.all(h[np.abs(s - 30.0) <= 2.0] == pytest.approx(0.02))         # flat over the 4 m crossing
        assert np.all(h[np.abs(s - 30.0) >= 2.0 + PVM.CROSSING_RAMP_M] == pytest.approx(S.KERB_HEIGHT))
        ramp = h[(np.abs(s - 30.0) > 2.0) & (np.abs(s - 30.0) < 3.0)]
        assert len(ramp) and np.all((ramp > 0.02) & (ramp < S.KERB_HEIGHT))
        assert np.all(np.diff(h[s <= 30.0]) <= 1e-12) and np.all(np.diff(h[s >= 30.0]) >= -1e-12)   # monotonic ramps


def test_crossing_drop_needs_rules_a_marked_crossing_and_room_on_the_chain():
    net = SimpleNamespace(chains=[_chain()])
    pts = [_pt(30.0, 0.0)]
    assert PVM.crossing_drops(net, pts, []) == []                                 # region without pavement_rules
    assert PVM.crossing_drops(net, pts, [{"kind": "pavement_rules", "crossing_kerb_drops": False}]) == []
    for skip in PVM.SKIP_CROSSING:
        assert PVM.crossing_drops(net, [_pt(30.0, 0.0, crossing=skip)], RULES) == []
    assert PVM.crossing_drops(net, [dict(_pt(30.0, 0.0), kind="highway=bus_stop")], RULES) == []
    st = {}
    assert PVM.crossing_drops(net, [_pt(30.0, 9.0)], RULES, st) == [] and st["skipped_off_chain"] == 1
    # inside the junction trim / closer to it than one ramp + 0.5 m: the corner strips own that kerb
    assert PVM.crossing_drops(net, [_pt(6.8, 0.0)], RULES, st) == [] and st["skipped_near_junction"] == 1
    # near the trim: a shorter flat part that still ends one ramp before the trim
    d = PVM.crossing_drops(net, [_pt(8.5, 0.0)], RULES, st)
    assert st["shortened"] == 1 and d[0]["half"] == pytest.approx(1.5)
    assert d[0]["s"] - d[0]["half"] - d[0]["ramp"] >= 6.0 - 1e-9
    # on a deck: no drop
    br = np.zeros(121, bool)
    br[50:70] = True
    assert PVM.crossing_drops(SimpleNamespace(chains=[_chain(bridge=br)]), [_pt(30.0, 0.0)], RULES, st) == []
    assert st["skipped_bridge"] == 1


def test_kerb_only_drop_leaves_ditches_flush_edges_and_deck_caps_alone():
    drop = [{"chain": "c1", "side": "L", "s": 30.0, "half": 2.0, "h": 0.02, "ramp": 1.0, "kerb_only": True}]
    for kw in ({"kind": NW.RURAL, "h": 0.4}, {"mat": NW.MAT_FLUSH_ROAD, "h": 0.0}, {"mat": 2, "h": S.BRIDGE_KERB_H}):
        c = _chain(**kw)
        before = c.side["L"]["h"].copy()
        PL.apply_drops(SimpleNamespace(chains=[c]), drop)
        assert np.array_equal(c.side["L"]["h"], before), kw
    assert NW.WALK_MATS[PL.KERB_ONLY_SKIP_MAT] == "bridge_concrete"
    # a driveway drop (ADR 0114) is unchanged: 3 cm, and it still fills a ditch
    c = _chain(kind=NW.RURAL, h=0.4)
    PL.apply_drops(SimpleNamespace(chains=[c]), [{"chain": "c1", "side": "L", "s": 30.0, "half": 2.0}])
    assert c.side["L"]["h"][60] == pytest.approx(PL.DITCH_FILL_M)


def test_lowered_kerb_adds_no_triangles():
    """Budget (ADR 0237): the strip of a side with a crossing drop has exactly as many triangles as without it."""
    n = 81
    G = np.column_stack([np.arange(n) * 0.5, np.zeros(n)])
    OUT = np.tile([0.0, -1.0], (n, 1))

    def tris(h):
        buf = M.MeshBuf()
        params = [(NW.URBAN, float(x), S.SIDEWALK_W, 0.3, 1) for x in h]
        M._emit_strip(buf, G, OUT, np.zeros(n), params, np.zeros(n), 3.5, False, None, False, "w1:a-b")
        return sum(len(p.T) for p in buf.parts), {p.mat for p in buf.parts}
    c = _chain(n=n, t_a=0.0, t_b=0.0)
    net = SimpleNamespace(chains=[c])
    full, mats = tris(c.side["L"]["h"])
    PL.apply_drops(net, PVM.crossing_drops(net, [_pt(20.0, 0.0)], RULES))
    assert c.side["L"]["h"].min() == pytest.approx(0.02)
    lowered, mats2 = tris(c.side["L"]["h"])
    assert lowered <= full and full > 0 and mats2 == mats
    assert "sidewalk_paving" in mats and "curb_concrete" in mats


# ------------------------------------------------------------------------------------------------ retype
def _strip(buf, src, x0, x1, y0, y1, layer="road", mat="sidewalk_paving", step=1.0):
    xs = np.arange(x0, x1 + 1e-9, step)
    V = np.array([[x, y, 0.0] for x in xs for y in (y0, y1)])
    T = []
    for i in range(len(xs) - 1):
        a = 2 * i
        T += [[a, a + 2, a + 3], [a, a + 3, a + 1]]
    buf.add(layer, mat, V, V[:, :2].copy(), T, src=src)


def _zones(**kw):
    return PVM.Zones({"sidewalk_bdot": True, **kw.pop("rules", {})}, **kw)


def test_retype_follows_bdot_and_overrides_and_conserves_triangles():
    buf = M.MeshBuf()
    _strip(buf, "w100:a-b", 0, 100, 4.0, 6.0)                       # footway of way 100, y 4..6
    _strip(buf, "w200:c-d", 0, 100, 40.0, 42.0)                     # footway of way 200 (authored: slabs)
    _strip(buf, "w100:a-b", 0, 100, 3.85, 4.0, mat="curb_concrete")  # kerb: never touched
    _strip(buf, "j:n1", 0, 100, 80.0, 82.0)                         # junction / island fill
    tris0 = sum(len(p.T) for p in buf.parts)
    z = _zones(bdot=[(LineString([(0, 5.5), (40, 5.5)]), "masa bitumiczna"),
                     (LineString([(40, 5.5), (70, 5.5)]), "kostka prefabrykowana"),
                     (LineString([(70, 5.5), (100, 5.5)]), "płyty betonowe"),
                     (LineString([(0, 30.0), (100, 30.0)]), "masa bitumiczna")],     # 9 m away: nobody's footway
               ways={200: ("slab-street", "slabs")},
               polys=[("red-island", Polygon([(20, 79), (30, 79), (30, 83), (20, 83)]), "paving_red"),
                      ("nothing-here", Polygon([(0, 200), (1, 200), (1, 201)]), "slabs")])
    rep = PVM.retype_sidewalks(buf.parts, z)
    assert rep["tris_in"] == rep["tris_out"] and sum(len(p.T) for p in buf.parts) == tris0
    assert {p.mat for p in buf.parts} == {"sidewalk_paving", "curb_concrete"}       # QA still sees the footway
    out = {}
    for p in buf.parts:
        if p.mat == "sidewalk_paving":
            for t in p.V[p.T].mean(axis=1):
                out.setdefault(getattr(p, "export_mat", None) or p.mat, []).append((round(t[0], 2), round(t[1], 2)))
    xs = lambda mat, y0, y1: sorted(x for x, y in out[mat] if y0 < y < y1)          # noqa: E731
    assert xs("path_asphalt", 4, 6)[0] < 1 and xs("path_asphalt", 4, 6)[-1] < 40.5
    assert 69.5 < xs("sidewalk_slabs", 4, 6)[0] and xs("sidewalk_slabs", 4, 6)[-1] > 99
    assert 39.5 < xs("sidewalk_paving", 4, 6)[0] and xs("sidewalk_paving", 4, 6)[-1] < 70.5
    assert len(xs("sidewalk_slabs", 40, 42)) == 200 and not xs("sidewalk_paving", 40, 42)
    red = xs("sidewalk_paving_red", 80, 82)
    assert len(red) == 20 and 20 < red[0] and red[-1] < 30
    assert rep["overrides_applied"] == ["red-island", "slab-street"] and rep["overrides_stale"] == ["nothing-here"]
    assert rep["tris_by_material"] == {"path_asphalt": 80, "sidewalk_paving": 60 + 180, "sidewalk_paving_red": 20,
                                       "sidewalk_slabs": 60 + 200}
    assert rep["m2_by_material"]["sidewalk_paving_red"] == pytest.approx(20.0)
    assert rep["tris_by_provenance"]["authored_override"] == 220 and rep["tris_by_provenance"]["bdot10k_SKRP"] == 200
    # a second run changes nothing (retyped parts are left alone)
    rep2 = PVM.retype_sidewalks(buf.parts, z)
    assert rep2["tris_by_material"].get("path_asphalt") is None and sum(len(p.T) for p in buf.parts) == tris0


def test_retype_is_off_without_rules_and_data_rules_stay_on_the_road_layer():
    buf = M.MeshBuf()
    _strip(buf, "w100:a-b", 0, 10, 4.0, 6.0)
    _strip(buf, "bdot:x", 0, 10, 4.0, 6.0, layer="paved")            # a set-back path: BDOT already chose its material
    n = len(buf.parts)
    assert PVM.retype_sidewalks(buf.parts, None)["enabled"] is False and len(buf.parts) == n
    assert PVM.plan([{"id": "x", "kind": "sidewalk_surface", "surface": "slabs", "polygon_en": [[0, 0], [1, 0], [1, 1]]}]) is None
    z = _zones(bdot=[(LineString([(0, 5), (10, 5)]), "masa bitumiczna")])
    PVM.retype_sidewalks(buf.parts, z)
    by_layer = {p.layer: getattr(p, "export_mat", None) for p in buf.parts}
    assert by_layer == {"road": "path_asphalt", "paved": None}
    with pytest.raises(ValueError):
        PVM.plan(RULES + [{"id": "x", "kind": "sidewalk_surface", "surface": "granite", "polygon_en": [[0, 0], [1, 0], [1, 1]]}])


def test_estate_rule_only_beside_blocks_on_local_streets():
    buf = M.MeshBuf()
    _strip(buf, "w1:a-b", 0, 100, 4.0, 6.0)        # residential
    _strip(buf, "w2:a-b", 0, 100, 14.0, 16.0)      # trunk, as close to the block
    block = Polygon([(40, 8), (60, 8), (60, 12), (40, 12)])
    z = _zones(rules={"estate_slabs": True}, blocks=[block], way_highway={1: "residential", 2: "trunk"})
    rep = PVM.retype_sidewalks(buf.parts, z)
    slabs = [p for p in buf.parts if getattr(p, "export_mat", None) == "sidewalk_slabs"]
    assert len(slabs) == 1 and slabs[0].src == "w1:a-b"
    x = slabs[0].V[slabs[0].T].mean(axis=1)[:, 0]
    assert 40 - PVM.ESTATE_M - 1 < x.min() < 40 - PVM.ESTATE_M + 3 and x.max() < 60 + PVM.ESTATE_M + 1
    assert rep["tris_by_provenance"]["typology(WORKING_VALUE)"] == len(slabs[0].T)


# ------------------------------------------------------------------------------------------------ cycle paths
def test_bdot_cycle_path_material_follows_the_region_rules():
    assert PVM.bdot_cycle_material([], "kostka prefabrykowana") == "cycle_red"          # regions without rules: as before
    assert PVM.bdot_cycle_material([], "masa bitumiczna") == "cycle_red"
    assert PVM.bdot_cycle_material([], "grunt naturalny") is None
    assert PVM.bdot_cycle_material(RULES, "kostka prefabrykowana") == "cycle_red"
    assert PVM.bdot_cycle_material(RULES, "masa bitumiczna") == "cycle_asphalt"         # grey DDR asphalt (ADR 0188)
    grey = [dict(RULES[0], cycle_paver_material="sidewalk_paving")]
    assert PVM.bdot_cycle_material(grey, "kostka prefabrykowana") == "sidewalk_paving"
    assert PV.PATH_SURFACE["płyty betonowe"] == "sidewalk_slabs"


def test_cycleway_override_sets_the_footway_surface():
    way = {"osm_way": 7, "part": 0, "geometry": [[0.0, 0.0], [80.0, 0.0]],
           "tags": {"highway": "path", "bicycle": "designated", "foot": "designated", "segregated": "yes",
                    "surface": "paved"}}
    data = {"ways": [way]}
    base = CY.plan(data, (0.0, 0.0), [], None, None)
    assert base and base[0]["mat_foot"] == "sidewalk_paving"
    ov = [{"id": "o", "kind": "cycleway", "target": {"osm_way": [7]}, "foot_surface": "slabs"}]
    it = CY.plan(data, (0.0, 0.0), ov, None, None)
    assert it[0]["mat_foot"] == "sidewalk_slabs" and it[0]["mat_cycle"] == base[0]["mat_cycle"]


# ------------------------------------------------------------------------------------------------ regions (git data)
@pytest.mark.parametrize("rid", REGIONS)
def test_region_rules_and_zones_from_git_data(rid):
    d, origin, ov = _region(rid)
    rules = PVM.rules_of(ov)
    assert rules and rules["id"] == "pavements-0237" and rules["crossing_kerb_drops"] and rules["sidewalk_bdot"]
    assert rules["estate_slabs"] is False                           # WORKING_VALUE rule: off until a frame shows it
    z = PVM.plan(ov, origin, _json(d / "generated" / "streetscape_sources.json"),
                 _json(d / "generated" / "osm_context.json"), _json(d / "buildings.geojson"), _json(d / "roads.graph.json"))
    mats = {m for _, m in z.bdot}
    assert {"kostka prefabrykowana", "masa bitumiczna"} <= mats <= set(PVM.BDOT_SIDEWALK)
    half = _json(d / "roads.graph.json")["bbox"]
    for ln, _ in z.bdot:                                            # local metres: inside the 2 km tile (+ clip slack)
        assert max(abs(v) for v in ln.bounds) < 1100, (half, ln.bounds)
    assert z.way_highway and not z.blocks
    for oid, poly, surf in z.polys:
        assert poly.is_valid and 20 < poly.area < 2000 and surf in PVM.MATERIAL, oid


def test_dojlidy_cycle_tracks_stay_grey_and_the_red_strip_is_authored():
    """R6-110 / ADR 0188: no red cycle track in Dojlidy; red blocks only where photo P11-063 shows them."""
    d, origin, ov = _region("bialystok-dojlidy")
    assert PVM.bdot_cycle_material(ov, "kostka prefabrykowana") == "sidewalk_paving"
    assert not [o for o in ov if o.get("kind") == "cycleway" and o.get("colour") == "red"]
    items = CY.plan(_json(d / "generated" / "osm_cycleways.json"), origin, ov, None, None)
    assert items and {it["mat_cycle"] for it in items} <= {"cycle_asphalt", "path_asphalt"}
    red = [o for o in ov if o.get("kind") == "sidewalk_surface"]
    assert [o["id"] for o in red] == ["mickiewicza-kuronia-red-block-strip"] and red[0]["surface"] == "paving_red"
    strip = Polygon(red[0]["polygon_en"])
    cams = {c["id"]: c for c in _json(d / "control_cameras_photo.authored.json")["cameras"]}
    cam = np.array(cams["photo_P11-063"]["pos_en"])
    hd = np.radians(cams["photo_P11-063"]["heading_deg"])
    ahead = cam + 4.5 * np.array([np.sin(hd), np.cos(hd)])          # the strip lies 3-5.5 m in front of the camera
    from shapely.geometry import Point
    assert strip.contains(Point(*ahead)) and not strip.contains(Point(*cam))
    axis = [e for e in _json(d / "roads.graph.json")["edges"] if e["osm_way"] == 258564446]
    ln = LineString(np.asarray(axis[0]["geometry"]) - origin)
    dist = [ln.distance(Point(*p)) for p in red[0]["polygon_en"]]
    assert 4.0 < min(dist) and max(dist) < 9.0                      # a band beside the carriageway, not on it


def test_region_c_keeps_its_red_asphalt_tracks():
    d, origin, ov = _region("bialystok-industrial-c")
    red_ways = {w for o in ov if o.get("kind") == "cycleway" and o.get("colour") == "red" for w in o["target"]["osm_way"]}
    assert len(red_ways) == 11                                      # M65: Rondo Putry / Andersa
    items = CY.plan(_json(d / "generated" / "osm_cycleways.json"), origin, ov, None, None)
    red = {it["osm_way"] for it in items if it["mat_cycle"] == "cycle_asphalt_red"}
    assert red and red <= red_ways | set(CY.RED_ASPHALT_WAYS)
    assert PVM.bdot_cycle_material(ov, "kostka prefabrykowana") == "cycle_red"


@pytest.mark.parametrize("rid,lo", [("bialystok-industrial-c", 60), ("bialystok-dojlidy", 60)])
def test_marked_crossings_in_region_data(rid, lo):
    """The crossings the kerb drops come from: marked OSM crossing nodes on the built roads (snap by chain needs a
    build; here: nodes within 6 m of a graph edge)."""
    d, origin, _ = _region(rid)
    pts = [p for p in _json(d / "generated" / "osm_context.json")["points"]
           if p["kind"] == "highway=crossing" and p.get("crossing") not in PVM.SKIP_CROSSING]
    import shapely
    tree = shapely.STRtree([LineString(e["geometry"]) for e in _json(d / "roads.graph.json")["edges"]])
    near = tree.query_nearest(shapely.points([[p["x"], p["y"]] for p in pts]), max_distance=6.0, all_matches=False)[0]
    assert lo <= len(set(near.tolist())) <= len(pts)


# ------------------------------------------------------------------------------------------------ budget
def test_frame_budget_inputs_exist_and_the_change_is_triangle_neutral():
    """Region C sits at the 2 M triangle limit (streetscape_qa.json mesh_budget.frame_estimate). ADR 0237 adds no
    triangle by construction: kerb drops edit station heights (test_lowered_kerb_adds_no_triangles), the retype
    splits parts (tris_in == tris_out), the gully is one quad of another size. This test pins the inputs of that
    statement: the committed frame estimate and the generator constants that would change it."""
    qa = _json(REPO / "Data" / "Regions" / "bialystok-industrial-c" / "generated" / "streetscape_qa.json")
    fe = qa["mesh_budget"]["frame_estimate"]
    assert len(fe) >= 5 and all(c["tris_high"] > 0 and c["by_category_high"]["roads"] > 0 for c in fe)
    assert NW.DENSE == 0.5 and S.P10_WIDTH == 4.0                    # 8 stations flat + 2 per ramp on a 4 m crossing
