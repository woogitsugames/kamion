"""ADR 0351 (CRITIC s24 wave 11 # 1): no lattice tower without conductors - in the tile and in the far-field ring.

No Unity, raw data or world build needed (synthetic lines + the committed streetscape sources of one tile)."""
import json
from itertools import permutations

import numpy as np
import pytest

from conftest import REPO
from streetscape import far_field as FF
from streetscape import furniture as FU


def _gis(lines, pylons):
    return {"power_lines": lines, "pylons": pylons}


def test_in_tile_mapped_tower_between_bdot_vertices_is_a_support():
    """A tower 150 m along a 600 m BDOT segment: the old equal subdivision put rule supports at 0 / 300 / 600 m
    and left the tower beside the conductor."""
    pl = FU.Placer(lambda e, n: np.zeros_like(np.asarray(e, float)))
    pl.add("pylon", np.array([150.0, 3.0]), 0.0, src="osm:node/1", group="pylon")
    rep = {}
    S = FU.power_supports(pl, np.array([[0.0, 0.0], [600.0, 0.0]]), True, "t", None, rep)
    assert any(np.hypot(*(s - [150.0, 3.0])) < 1e-6 for s in S)
    assert rep["mapped_supports"] == 1
    # no rule tower within one gap of the mapped one, every gap <= the span maximum
    gaps = np.hypot(*np.diff(S, axis=0).T)
    assert gaps.max() <= FU.SPAN_MAX_M["pylon"] + 1e-6 and gaps.min() > 100.0
    assert np.all(np.diff(S[:, 0]) > 0)   # ordered along the line


def test_far_field_towers_only_on_hv_lines_and_all_wired():
    half = 1024.0
    hv = {"pts": [[half, 200.0], [half + 900.0, 260.0], [half + 1600.0, 900.0]], "hv": True, "src": "bdot10k", "id": "h"}
    mv = {"pts": [[-half - 50.0, 0.0], [-half - 900.0, 40.0]], "hv": False, "src": "bdot10k", "id": "m"}
    osm_dup = {"pts": [[half + 5.0, 210.0], [half + 905.0, 270.0]], "hv": True, "src": "osm", "id": "osm_w1"}
    untagged = {"pts": [[0.0, -half - 200.0], [400.0, -half - 900.0]], "hv": None, "src": "osm", "id": "osm_w2"}
    pylons = [{"id": "t1", "e": half + 400.0, "n": 228.0, "kind": "słup energetyczny"},     # on the HV line
              {"id": "p1", "e": -half - 400.0, "n": 21.0, "kind": "słup energetyczny"},     # MV pole: dropped
              {"id": "m1", "e": 0.0, "n": half + 900.0, "kind": "maszt lub wieża telekomunikacyjna"}]
    plan = FF.power_plan(_gis([hv, mv, osm_dup, untagged], pylons), half)
    st = plan["stats"]
    assert st["lines_hv_bdot"] == 1 and st["osm_hv_duplicates_of_bdot"] == 1 and st["osm_untagged_dropped"] == 1
    assert st["unwired_power_pylons"] == 0 and st["seam_supports"] == 1
    assert st["dropped_towers_off_hv_lines"] == {"słup energetyczny": 1}
    assert [m["id"] for m in plan["masts"]] == ["m1"]
    assert any(p["id"] == "t1" for p in plan["pylons"])
    # every drawn tower ends a span; spans <= span max; the seam support is not drawn (the tile owns it)
    ends = {id(x) for ab in plan["spans"] for x in ab}
    assert all(id(p) in ends for p in plan["pylons"])
    assert not any(p["seam"] for p in plan["pylons"])
    for a, b in plan["spans"]:
        assert 5.0 <= np.hypot(a["e"] - b["e"], a["n"] - b["n"]) <= FU.SPAN_MAX_M["pylon"] + 1e-6


def test_far_span_conductors_hang_from_arm_tips_with_sag():
    half = 1024.0
    elev = FF.BorderElevation(half, [100.0] * 2, [100.0] * 2, [100.0] * 2, [100.0] * 2)
    a = {"e": half, "n": 0.0, "h": 32.0, "seam": True}
    b = {"e": half + 120.0, "n": 0.0, "h": 32.0, "seam": False}     # inside the unforeshortened band
    for tier, n_cond in (("High", 7), ("Low", 2)):
        sectors = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
        FF._add_span(sectors, a, b, elev, half, tier)
        p = sectors["far_east"].primitives()[0]
        assert p["mat"] == "far_field_buildings" and set(p["COL"][:, 3]) == {0.0}
        V = p["V"]
        # the seam end sits on the tile tower's arm tips: lateral 4.3 m, heights 20/24/28 - 1.3 m (+ earth 32 m)
        seam = V[np.isclose(V[:, 0], half)]
        lat = np.unique(np.round(np.abs(seam[:, 1]), 2))
        assert set(lat) <= {0.0, 4.3}
        zc = np.unique(np.round((seam[:, 2].reshape(-1, 2).mean(1) if len(seam) % 2 == 0 else seam[:, 2]) - 100.0, 1))
        assert zc.min() >= 18.6 and zc.max() <= 32.1
        # mid-span lower than the ends (sag), conductors count
        mid = V[(V[:, 0] > half + 20.0) & (V[:, 0] < half + 100.0)]
        assert mid[:, 2].min() < seam[:, 2].min()
        assert len(np.unique(np.round(np.abs(seam[:, 1]) + seam[:, 2], 1))) >= n_cond // 2


def test_galvanised_colour_is_grey_and_varies():
    cols = np.array([FF.galv_colour(f"t{i}") for i in range(200)])
    assert cols.max() < 0.2 and cols.min() > 0.12            # mid grey, not the old 0.27-0.30 (white in sun)
    assert np.ptp(cols[:, 1]) > 0.02                          # per-tower variation
    assert np.all(np.abs(cols[:, 0] - cols[:, 2]) < 0.025)    # no saturated tint


@pytest.mark.parametrize("region", ["bialystok-kleeberga", "dk65-monki-05"])
def test_committed_tiles_have_no_unwired_mapped_pylon(region):
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
    import hv_wires_audit as A
    t = A.in_tile(region)
    assert t["pylon"]["mapped"] > 0 and t["pylon"]["unwired"] == 0, t["pylon"]["unwired_at"]


def test_far_field_mv_line_near_the_tile_gets_poles_and_three_conductors():
    half = 1024.0
    mv = {"pts": [[500.0, half], [520.0, half + 900.0]], "hv": False, "mv": True, "src": "bdot10k", "id": "m"}
    lv = {"pts": [[-500.0, half], [-520.0, half + 900.0]], "hv": False, "mv": False, "src": "osm", "id": "osm_w9"}
    plan = FF.power_plan(_gis([mv, lv], []), half)
    st = plan["stats"]
    assert st["mv_lines_near"] == 1 and st["mv_seam_supports"] == 1 and st["pylons"] == 0
    # clipped at MV_FAR_MAX_M; spans <= the MV span maximum; every pole wired
    assert max(p["n"] for p in plan["mv_poles"]) <= half + FF.MV_FAR_MAX_M + 1e-6
    for a, b in plan["mv_spans"]:
        assert np.hypot(a["e"] - b["e"], a["n"] - b["n"]) <= FU.SPAN_MAX_M["power_pole"] + 1e-6
    ends = {id(x) for ab in plan["mv_spans"] for x in ab}
    assert all(id(p) in ends for p in plan["mv_poles"])
    elev = FF.BorderElevation(half, [100.0] * 2, [100.0] * 2, [100.0] * 2, [100.0] * 2)
    sectors = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    a, b = plan["mv_spans"][0]
    assert a["seam"]
    FF._add_span(sectors, a, b, elev, half, "High", mv=True)
    V = sectors["far_north"].primitives()[0]["V"]
    seam = V[np.isclose(V[:, 1], half, atol=1e-6)]
    assert len(seam) and np.allclose(seam[:, 2], 111.7, atol=0.1)   # 100 + 12 - 0.3 m: the tile pole's insulators
    FF._add_pole(sectors, b, elev, half)
    lows = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    FF._add_span(lows, a, b, elev, half, "Low", mv=True)
    assert not any(x.primitives() for x in lows.values())     # MV: High only


def test_far_hv_density_lod_prevents_foreshortened_overlap():
    """ADR 0351 addendum: foreshortening crushes 2-4 km spans into 1.6-15 m gaps; _select_far_hv enforces minimum
    foreshortened spacing across receding and parallel lines so towers never merge into a grey band."""
    half = 1024.0
    # Two parallel receding HV lines (55 m apart) running 0..3800 m outside the north border
    pts1 = [[738.0, half + d] for d in range(0, 3801, 250)]
    pts2 = [[793.0, half + d] for d in range(0, 3801, 250)]
    lines = [{"pts": pts1, "hv": True, "src": "bdot10k", "id": "hv1"},
             {"pts": pts2, "hv": True, "src": "bdot10k", "id": "hv2"}]
    plan = FF.power_plan(_gis(lines, []), half)
    assert len(plan["pylons"]) >= 24
    for tier in ("High", "Low"):
        rp, rs = FF._select_far_hv(plan, half, tier)
        assert len(rp) < len(plan["pylons"])
        assert len(rp) >= 4
        effs = [FF.foreshorten_point(p["e"], p["n"], half) for p in rp]
        max_d = FF.LOW_HV_MAX_D_M if tier == "Low" else FF.HIGH_HV_MAX_D_M
        assert all(dr <= max_d + 1e-6 for _, _, dr, _ in effs)
        for i in range(len(effs)):
            for j in range(i + 1, len(effs)):
                sep = float(np.hypot(effs[i][0] - effs[j][0], effs[i][1] - effs[j][1]))
                req = min(FF._hv_min_eff_sep(effs[i][2], tier), FF._hv_min_eff_sep(effs[j][2], tier))
                assert sep >= req - 1e-6, f"{tier}: towers too close in eff space ({sep:.1f} < {req:.1f})"
        # Near seam both parallel lines remain anchored to their seam supports
        seam_spans = [ab for ab in rs if ab[0].get("seam") or ab[1].get("seam")]
        assert len(seam_spans) == 2


@pytest.mark.parametrize("tier", ["Low", "High"])
def test_far_hv_lod_discards_a_tower_when_its_only_neighbour_is_out_of_range(tier):
    half = 1024.0
    near = {"id": "near", "e": half + 100, "n": 0}
    far = {"id": "far", "e": half + FF.HIGH_HV_MAX_D_M + 1, "n": 0}
    mast = {"id": "mast", "e": half + 100, "n": 100}
    plan = {"pylons": [near, far], "spans": [(near, far)], "masts": [mast]}
    selected = FF._select_far_hv(plan, half, tier)
    assert selected == ([], [])
    assert FF.far_hv_lod_stats(*selected) == {"pylons": 0, "spans": 0, "unwired_power_pylons": 0}
    assert plan["masts"] == [mast]


@pytest.mark.parametrize("tier", ["Low", "High"])
def test_far_hv_lod_resolves_competing_branches_independently_of_input_order(tier):
    seam = {"id": "seam", "e": 1100, "n": 0, "seam": True}
    south = {"id": "south", "e": 1200, "n": -10}
    north = {"id": "north", "e": 1200, "n": 10}
    twin = {**south, "id": "south-twin"}
    pylons = [south, north, twin]
    for spans in permutations([(seam, p) for p in pylons]):
        for reverse in (False, True):
            oriented = [(b, a) if reverse else (a, b) for a, b in spans]
            plan = {"pylons": pylons, "spans": oriented}
            assert FF._select_far_hv(plan, 1024, tier) == ([south], [(seam, south)])


def test_far_pylon_silhouette_open_and_lightweight():
    """ADR 0351 addendum: far-field towers drop heavy horizontal ring bars, close to a tapered A-frame spire peak,
    and switch past FAR_HV_SILHOUETTE_D_M (and on Low) to a crisp open A/Y ribbon silhouette (<= 30 tris)."""
    half = 1024.0
    elev = FF.BorderElevation(half, [100.0] * 2, [100.0] * 2, [100.0] * 2, [100.0] * 2)
    # Near High (300 m out): open 3D A-frame without horizontal rings (< old 222 tris)
    sec_near = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    FF._add_pylon(sec_near, {"id": "p_near", "e": 0.0, "n": half + 300.0, "h": 32.0}, elev, half, "High", yaw=0.0)
    p_near = sec_near["far_north"].primitives()[0]
    assert len(p_near["T"]) <= 160
    assert p_near["mat"] == "far_field_buildings"
    assert set(p_near["COL"][:, 3]) == {0.0}
    assert p_near["UV1"][:, 0].min() >= 0.0
    # Far High (1800 m out) & Low: crisp A/Y ribbon silhouette (<= 30 tris)
    for tier, dist in (("High", 1100.0), ("High", 2200.0), ("Low", 400.0)):
        sec = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
        FF._add_pylon(sec, {"id": "p_far", "e": 0.0, "n": half + dist, "h": 32.0}, elev, half, tier, yaw=0.0)
        p = sec["far_north"].primitives()[0]
        assert 12 <= len(p["T"]) <= 30, f"{tier}@{dist}: unexpected tri count {len(p['T'])}"
        assert set(p["COL"][:, 3]) == {0.0}
        assert p["UV1"][:, 0].min() >= 0.0


def test_far_span_wire_lod_thinning_and_shader_fade_uv1():
    """ADR 0351 addendum: far conductors use thinner capped widths, drop from 7 -> 3 -> 0 with distance, and carry
    distance-fade metadata in TEXCOORD_1 (uv1.x >= 0, uv1.y <= -100, COLOR_0.a == 0) for WorldSurface.shader."""
    half = 1024.0
    elev = FF.BorderElevation(half, [100.0] * 2, [100.0] * 2, [100.0] * 2, [100.0] * 2)
    # Near seam: 7 conductors + wire fade UV1
    sec_near = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    FF._add_span(sec_near, {"e": half, "n": 0.0, "h": 32.0, "seam": True},
                 {"e": half + 200.0, "n": 0.0, "h": 32.0, "seam": False}, elev, half, "High")
    p_near = sec_near["far_east"].primitives()[0]
    assert set(p_near["COL"][:, 3]) == {0.0}
    assert p_near["UV1"][:, 0].min() >= 0.0
    assert p_near["UV1"][:, 1].max() <= -FF.FAR_WIRE_UV1_SENTINEL
    # Mid distance (650..900 m): reduced to 3 silhouette conductors (< half the tris of near seam)
    sec_mid = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    FF._add_span(sec_mid, {"e": half + 650.0, "n": 0.0, "h": 32.0, "seam": False},
                 {"e": half + 900.0, "n": 0.0, "h": 32.0, "seam": False}, elev, half, "High")
    p_mid = sec_mid["far_east"].primitives()[0]
    assert 0 < len(p_mid["T"]) < len(p_near["T"])
    assert p_mid["UV1"][:, 1].max() <= -FF.FAR_WIRE_UV1_SENTINEL
    # Far horizon (> 1400 m): 0 opaque wire ribbons
    sec_far = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    FF._add_span(sec_far, {"e": half + 1500.0, "n": 0.0, "h": 32.0, "seam": False},
                 {"e": half + 1800.0, "n": 0.0, "h": 32.0, "seam": False}, elev, half, "High")
    assert not sec_far["far_east"].primitives()


def _run_tile_wires(src):
    from roads.meshing import MeshBuf
    origin = np.zeros(2)
    zero = lambda e, n: np.zeros_like(np.asarray(e, float))
    pl = FU.Placer(zero)
    for nd in src.get("osm", {}).get("nodes", []):
        proto = {"tower": "pylon", "pole": "power_pole"}.get(nd["tags"].get("power"))
        if proto and not pl.near(proto, nd["geometry"]["coordinates"], 3.0):
            pl.add(proto, nd["geometry"]["coordinates"], 0.0, src=f"osm:node/{nd['osm_node']}", group=proto)
    lin = FU.Lin(MeshBuf(), zero)
    rep = {}
    FU.power_lines(lin, src, origin, rep, pl=pl)
    return pl, lin.buf, rep


def test_in_tile_osm_minor_line_crossing_tile_seam():
    """Synthetic tile: OSM power=minor_line clipped at east seam x=1024 gets a seam rule pole and full wire span."""
    src = {
        "schema": "truck-sim-pl/streetscape-sources/2",
        "osm": {
            "nodes": [{"osm_node": 1, "tags": {"power": "pole"}, "geometry": {"type": "Point", "coordinates": [950.0, 200.0]}}],
            "ways": [{"osm_way": 10, "part": 0, "tags": {"power": "minor_line", "cables": "3"},
                      "geometry": {"type": "LineString", "coordinates": [[950.0, 200.0], [1024.0, 200.0]]}}],
        },
        "bdot10k": {"OT_SULN_L": [], "OT_BUWT_P": []},
    }
    pl, buf, rep = _run_tile_wires(src)
    assert rep["power_lines"] == 1 and rep["power_supports_added"] == 1
    seam_poles = [it for it in pl.items if it["p"] == "power_pole" and abs(it["e"] - 1024.0) < 1e-3]
    assert len(seam_poles) == 1
    wire_parts = [p for p in buf.parts if p.layer == "wires"]
    assert len(wire_parts) == 3
    xs = np.concatenate([p.V[:, 0] for p in wire_parts])
    assert xs.min() == pytest.approx(950.0) and xs.max() == pytest.approx(1024.0)
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
    import hv_wires_audit as A
    res = A.in_tile(src=src, origin=[0.0, 0.0], use_pbf=False)
    assert res["power_pole"]["mapped"] == 1
    assert res["power_pole"]["unwired"] == 0 and res["power_pole"]["without_line"] == 0


def test_in_tile_osm_terminal_pole_and_bdot_continuation():
    """Terminal pole on an OSM minor_line extending past a BDOT segment is wired without duplicating the BDOT span."""
    src = {
        "schema": "truck-sim-pl/streetscape-sources/2",
        "osm": {
            "nodes": [
                {"osm_node": 1, "tags": {"power": "pole"}, "geometry": {"type": "Point", "coordinates": [70.0, 100.0]}},
                {"osm_node": 2, "tags": {"power": "pole"}, "geometry": {"type": "Point", "coordinates": [140.0, 100.0]}},
            ],
            "ways": [
                {"osm_way": 20, "part": 0, "tags": {"power": "minor_line", "voltage": "15000", "cables": "3"},
                 "geometry": {"type": "LineString", "coordinates": [[0.0, 100.0], [70.0, 100.0], [140.0, 100.0]]}},
            ],
        },
        "bdot10k": {
            "OT_SULN_L": [{"id": "b1", "props": {"rodzaj": "linia elektroenergetyczna średniego napięcia"},
                           "geometry": {"type": "LineString", "coordinates": [[0.0, 100.0], [70.0, 100.0]]}}],
            "OT_BUWT_P": [],
        },
    }
    pl, buf, rep = _run_tile_wires(src)
    assert rep["power_lines"] == 2
    wire_parts = [p for p in buf.parts if p.layer == "wires"]
    # 3 conductors for BDOT (0..70) + 3 conductors for OSM continuation (70..140), no duplicate on 0..70
    assert len(wire_parts) == 6
    assert sum(1 for it in pl.items if it["p"] == "power_pole") == 3
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
    import hv_wires_audit as A
    res = A.in_tile(src=src, origin=[0.0, 0.0], use_pbf=False)
    assert res["power_pole"]["mapped"] == 2 and res["power_pole"]["unwired"] == 0 and res["power_pole"]["without_line"] == 0


def test_in_tile_pole_without_line_and_audit_distinction():
    """Audit distinguishes poles without any line in data (stork nest / standalone) from poles with an unwired line."""
    src = {
        "schema": "truck-sim-pl/streetscape-sources/2",
        "osm": {
            "nodes": [
                {"osm_node": 1, "tags": {"power": "pole", "natural": "birds_nest"},
                 "geometry": {"type": "Point", "coordinates": [100.0, 100.0]}},
                {"osm_node": 2, "tags": {"power": "pole"},
                 "geometry": {"type": "Point", "coordinates": [300.0, 100.0]}},
                {"osm_node": 3, "tags": {"power": "pole"},
                 "geometry": {"type": "Point", "coordinates": [500.0, 100.0]}},
            ],
            "ways": [
                {"osm_way": 30, "part": 0, "tags": {"power": "minor_line"},
                 "geometry": {"type": "LineString", "coordinates": [[450.0, 100.0], [500.0, 100.0]]}},
            ],
        },
        "bdot10k": {"OT_SULN_L": [], "OT_BUWT_P": []},
    }
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
    import hv_wires_audit as A
    before = A.in_tile(src=src, origin=[0.0, 0.0], use_pbf=False, osm_lines=False)
    assert before["power_pole"]["mapped"] == 3
    assert before["power_pole"]["unwired"] == 1
    assert before["power_pole"]["without_line"] == 2
    assert before["power_pole"]["unwired_at"] == [[500.0, 100.0, "osm:node/3"]]
    after = A.in_tile(src=src, origin=[0.0, 0.0], use_pbf=False, osm_lines=True)
    assert after["power_pole"]["mapped"] == 3
    assert after["power_pole"]["unwired"] == 0
    assert after["power_pole"]["without_line"] == 2


def test_in_tile_skips_substation_bay_busbar_and_unmapped_osm_line():
    """Substation busbar/bay ways and OSM lines without mapped poles never spawn phantom rule poles."""
    src = {
        "schema": "truck-sim-pl/streetscape-sources/2",
        "osm": {
            "nodes": [],
            "ways": [
                {"osm_way": 40, "part": 0, "tags": {"power": "line", "line": "busbar", "voltage": "110000"},
                 "geometry": {"type": "LineString", "coordinates": [[500.0, 500.0], [560.0, 500.0]]}},
                {"osm_way": 41, "part": 0, "tags": {"power": "line", "line": "bay", "voltage": "110000"},
                 "geometry": {"type": "LineString", "coordinates": [[520.0, 500.0], [520.0, 540.0]]}},
                {"osm_way": 42, "part": 0, "tags": {"power": "minor_line"},
                 "geometry": {"type": "LineString", "coordinates": [[0.0, 20.0], [200.0, 20.0]]}},
            ],
        },
        "bdot10k": {
            "OT_SULN_L": [{"id": "b1", "props": {"rodzaj": "linia elektroenergetyczna średniego napięcia"},
                           "geometry": {"type": "LineString", "coordinates": [[0.0, 0.0], [200.0, 0.0]]}}],
            "OT_BUWT_P": [],
        },
    }
    pl, _buf, rep = _run_tile_wires(src)
    assert rep["power_lines"] == 1
    assert all(it["p"] == "power_pole" and abs(it["n"]) < 1e-6 for it in pl.items)


def test_committed_mickiewicza_and_stork_tiles_audit():
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
    import hv_wires_audit as A
    m = A.in_tile("bialystok-mickiewicza")
    assert m["power_pole"]["mapped"] == 9 and m["power_pole"]["unwired"] == 0 and m["power_pole"]["without_line"] == 0
    assert m["pylon"]["unwired"] == 0
    d = A.in_tile("bialystok-dojlidy")
    assert d["power_pole"]["mapped"] == 1 and d["power_pole"]["unwired"] == 0 and d["power_pole"]["without_line"] == 1
    k3 = A.in_tile("dk65-03")
    assert k3["power_pole"]["mapped"] == 3 and k3["power_pole"]["unwired"] == 0 and k3["power_pole"]["without_line"] == 3
