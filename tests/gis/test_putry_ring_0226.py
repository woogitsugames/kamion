"""ADR 0226: centre island of Rondo Putry corrected to the GUGiK orthophoto (owner decision 2026-11-15).

Generator mechanisms: `truck_apron: {width_m}` on ring edges (distance carriageway edge -> island kerb; the ONE
island-strip mechanism shared with ADR 0218 / PR #97, here without material = width only) and the node override
`island_curb_radius` (kerb return between two ring carriageways). No Data/raw, no Unity: the unit tests are instant,
the `world` tests share the flat-ground road stage of tests/gis/conftest.py `piers_check` (about 100 s per session).
"""
import numpy as np
import pytest

from roads import network as Nw
from roads import standards as S

PUTRY_RING = {"180144451", "257367424", "257367425", "257367428"}
# Kerb of the centre island (asphalt side of the light kerb band), local E, N. Read by eye on a 1 m grid drawn over
# the GUGiK orthophoto WMS HighResolution, 0.05 m/px window E -640..-480 N -80..+80 fetched 2026-11-15 (reference
# only, not stored in the repo). WORKING_VALUE, +-0.3 m; the two points between the decks +-0.5 m. The parts under
# the two decks of estakada A cannot be seen and are not listed.
KERB = {
    "W": [(-572.6, 23.5), (-572.9, 38), (-572.9, 42), (-572.85, 45), (-572.3, 46.4), (-571.8, 47.5), (-571.2, 48.7),
          (-570.3, 49.8), (-569.3, 50.75), (-568.3, 51.4)],
    "N": [(-566.5, 52.6), (-564.75, 53.4), (-562.5, 53.8), (-560, 53.75), (-557.5, 53.25), (-555, 52.4),
          (-552.5, 51.4), (-550, 50.25), (-548, 49), (-546.5, 47.75), (-545.25, 46.25)],
    "E": [(-544.1, 45), (-543.4, 40), (-542.4, 35), (-541.6, 30), (-540.75, 25), (-539.0, 3)],
    "S": [(-569.0, 6.2), (-567.0, 3.4), (-565.0, 1.0), (-563.0, -0.6), (-560.0, -2.8), (-557.0, -5.0), (-555, -6.0),
          (-553, -6.7), (-551, -7.1), (-549, -7.25), (-547.8, -7.1)],
}


def _net(set_, junction="roundabout"):
    attrs = {k: {"v": v, "src": "osm", "conf": "high"} for k, v in
             dict(highway="trunk", oneway="yes", lanes=2, width=7.0, junction=junction).items() if v is not None}
    e = {"id": "w1:1-2", "attrs": attrs, "osm_way": 1}
    net = Nw.Network(nodes={}, sections={"w1:1-2": Nw.edge_section(e)}, sec_list=[], chains=[], origin=(0, 0))
    Nw.apply_edge_overrides(net, {"w1:1-2": (e, None, "1", "2")},
                            [{"id": "ov", "target": {"osm_way": 1}, "set": set_}])
    return net, net.sections["w1:1-2"]


@pytest.mark.unit
def _apron_w(sec):
    return None if sec.truck_apron is None else sec.truck_apron["width_m"]


@pytest.mark.unit
def test_apron_width_is_read_on_ring_edges_only():
    net, sec = _net({"apron": "asphalt", "truck_apron": {"width_m": 0.4}})
    assert sec.roundabout and sec.apron == "asphalt"
    assert sec.truck_apron == {"width_m": 0.4, "height_m": None, "material": None, "code": None}, "width only"
    assert not net.overrides_stale and sec.provenance["truck_apron"] == "authored_override:ov"
    net, sec = _net({"truck_apron": {"width_m": 0.4}}, junction=None)   # not a ring: nothing to move
    assert sec.truck_apron is None and net.overrides_stale == ["ov"]


@pytest.mark.unit
@pytest.mark.parametrize("bad", [0.0, 0.1, -1.0, 6.5, "wide", None])
def test_apron_width_outside_the_range_is_refused(bad):
    net, sec = _net({"truck_apron": {"width_m": bad}})
    assert sec.truck_apron is None and net.overrides_stale == ["ov"], "a zero-width strip would mesh as degenerate triangles"
    net, sec = _net({"truck_apron": bad})                             # the bare number is not the key's form
    assert sec.truck_apron is None and net.overrides_stale == ["ov"]


@pytest.mark.unit
def test_default_apron_is_unchanged():
    _, sec = _net({"apron": "asphalt"})                               # ADR 0123 form, Rondo Biezenstwa
    assert sec.truck_apron is None
    assert S.ROUNDABOUT_APRON_W == 2.0 and Nw.TRUCK_APRON_W == (0.2, 6.0)


@pytest.mark.unit
def test_one_mechanism_for_the_island_strip():
    """REVIEW s21 #93 FIX 2: `apron_width` (first version of ADR 0226) and `truck_apron` (ADR 0218, PR #97) wrote the
    same ISLAND side width. One key, one field, one validator: `truck_apron`."""
    assert "apron_w" not in Nw.EdgeSection.__dataclass_fields__ and not hasattr(Nw, "APRON_W_MIN")
    net, sec = _net({"apron_width": 0.4})
    assert sec.truck_apron is None, "`apron_width` is not a key any more"
    net, sec = _net({"truck_apron": {"width_m": 3.2, "height_m": 0.04, "material": "kostka_jasna"}})   # #97 form
    # code 8 = apron_paving_light (owner D75, ADR 0218 5b; main's material, not the PR's first `sidewalk_paving`)
    assert sec.truck_apron["material"] == Nw.APRON_LIGHT == "apron_paving_light" and sec.truck_apron["code"] == 8
    assert not net.overrides_stale
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    hits = [str(p.relative_to(root)) for p in sorted((root / "Data/Regions").glob("*/overrides.yaml"))
            if "apron_width" in p.read_text(encoding="utf-8")]
    assert not hits, hits


@pytest.mark.unit
def test_island_profile_puts_the_kerb_at_the_apron_width():
    for w in (2.0, 0.4):
        prof = Nw.side_profile(Nw.ISLAND, S.KERB_HEIGHT, w, 0.5, Nw.MAT_FLUSH_ROAD)
        assert len(prof) == 5, "one topology for every island station"
        assert prof[1][:3:2] == (0.0, w) and prof[1][4] == "road_asphalt"          # flush strip 0 .. w
        assert prof[2][0] == prof[2][2] == w and prof[2][4] == "curb_concrete"     # kerb face at w
        assert prof[2][3] - prof[2][1] == pytest.approx(S.KERB_HEIGHT)
        assert all(abs(a[2] - a[0]) > 1e-6 or abs(a[3] - a[1]) > 1e-6 for a in prof[1:]), "no degenerate strip"


@pytest.mark.unit
def test_island_curb_radius_has_a_range():
    from roads import junctions as J
    assert J.ISLAND_CURB_R == (2.0, 30.0)
    import yaml
    from pathlib import Path
    ov = yaml.safe_load((Path(__file__).resolve().parents[2]
                         / "Data/Regions/bialystok-industrial-c/overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    vals = [o["set"]["island_curb_radius"] for o in ov if "island_curb_radius" in (o.get("set") or {})]
    assert vals == [10.0] and all(J.ISLAND_CURB_R[0] <= v <= J.ISLAND_CURB_R[1] for v in vals)


# ---------------------------------------------------------------- built road stage (flat ground model)
@pytest.fixture(scope="module")
def world(piers_check):
    return piers_check[1]


def _driven(world, mats=lambda m: m.startswith("road_") or m == "apron_sett"):
    import shapely
    from shapely.geometry import Polygon
    tris = []
    for p in world.buf.parts:
        if p.layer != "road" or not p.footprint or not len(p.T) or p.src.endswith(":vg") or not mats(p.mat):
            continue
        v = p.V[:, :2]
        if v[:, 0].max() < -620 or v[:, 0].min() > -500 or v[:, 1].max() < -60 or v[:, 1].min() > 100:
            continue
        for t in v[p.T]:
            a, b = t[1] - t[0], t[2] - t[0]
            if abs(a[0] * b[1] - a[1] * b[0]) > 1e-9:
                tris.append(Polygon(t))
    return shapely.union_all(tris) if tris else None


@pytest.fixture(scope="module")
def island(world):
    from shapely.geometry import Point, Polygon
    road = _driven(world)
    holes = [Polygon(h) for g in getattr(road, "geoms", [road]) for h in g.interiors]
    hit = [h for h in holes if h.contains(Point(-558.0, 25.0))]
    assert len(hit) == 1, "the centre island of Rondo Putry is one kerbed hole in the driven surface"
    return hit[0]


def test_only_the_putry_ring_has_an_authored_apron_width(world):
    secs = [s for s in world.net.sec_list if s.truck_apron is not None]
    assert {str(s.edge_id).split(":")[0].lstrip("w") for s in secs} == PUTRY_RING
    assert all(s.roundabout and s.apron == "asphalt" and _apron_w(s) == pytest.approx(0.4) for s in secs)
    assert all(s.truck_apron["code"] is None for s in secs), "width only: the strip stays the `apron: asphalt` carriageway"
    other = [s for s in world.net.sec_list if s.roundabout and s.truck_apron is None]
    assert other, "Rondo Biezenstwa keeps the rule's apron width"
    stale = set(world.net.overrides_stale)
    assert not stale & {"putry-ring-s-placement", "putry-ring-island-kerb", "putry-ring-island-nw-corner"}


def test_island_side_of_the_ring_chains_uses_the_authored_width(world):
    for c in world.net.chains:
        if not c.roundabout:
            continue
        ways = {str(e).split(":")[0].lstrip("w") for e, _ in c.edges}
        side = "L" if (c.dirn > 0).mean() >= 0.5 else "R"
        kind, _h, w, _d, _m = Nw.side_params(c, side, c.length / 2)
        assert kind == Nw.ISLAND
        assert w == pytest.approx(0.4 if ways <= PUTRY_RING else S.ROUNDABOUT_APRON_W), c.id


def test_no_sett_apron_is_left_on_the_putry_ring(world):
    assert _driven(world, lambda m: m == "apron_sett") is None


def test_generated_island_kerb_follows_the_orthophoto(island):
    from shapely.geometry import Point
    d = {k: np.array([island.exterior.distance(Point(q)) * (1.0 if island.contains(Point(q)) else -1.0) for q in v])
         for k, v in KERB.items()}                     # + = the generated island is larger than the real one there
    alld = np.abs(np.concatenate(list(d.values())))
    assert len(alld) == 38
    assert alld.mean() < 0.6, alld.mean()              # 0.46 m (ADR 0198 geometry: 2.02 m)
    assert alld.max() < 1.6, alld.max()                # 1.37 m at the north-west corner (ADR 0198 geometry: 4.93 m)
    assert np.abs(d["S"]).max() < 1.0, d["S"]          # the side under the SW deck: was 1.4 - 4.9 m inside
    assert abs(d["S"].mean()) < 0.4 and abs(d["E"].mean()) < 0.4
    assert 1600.0 < island.area < 1750.0               # 1679 m2 inside the kerb line (ADR 0198 geometry: 1388 m2)


def test_north_west_island_corner_has_the_authored_radius(world):
    j = next(j for j in world.junctions if "n3890183128" in j.nodes)
    ring = [c for c in j.corners if j.arms[c.k].is_ring() and j.arms[c.k1].is_ring()]
    assert len(ring) == 1 and ring[0].kind == "fillet" and ring[0].R == pytest.approx(10.0)
    assert all(c.R != pytest.approx(10.0) for c in j.corners if c is not ring[0]), "outer corners keep the class rule"
    for jj in world.junctions:                          # the other three island corners: the rule (12 m, x 0.7 retries)
        if jj is j:
            continue
        for c in jj.corners:
            if c.kind == "fillet" and jj.arms[c.k].is_ring() and jj.arms[c.k1].is_ring():
                assert c.R in (pytest.approx(12.0), pytest.approx(8.4), pytest.approx(5.88)), (jj.id, c.R)
