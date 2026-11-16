"""ADR 0274: Knyszyn roundabout - kerb-mode outline, DK65 carriageway split, island mesh, P-13 / P-10 at the ring,
and the fixes of code review s23 D18 (compact roundabout).

Synthetic 4-arm roundabout (the graph of test_compact_roundabout_0218, pure Python, no Data/raw) + the Knyszyn data
that are in git (roads.graph.json, overrides.yaml, generated/osm_context.json; heights flat - no Data/raw).
Run: uv run --project tools/worldgen python -m pytest tests/gis/test_roundabout_0274.py -q
"""
import copy
import inspect
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import shapely
import shapely.ops  # noqa: F401  (roads.gores uses shapely.ops)
from shapely.geometry import LineString, Point, Polygon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
sys.path.insert(0, str(ROOT / "tools" / "worldgen" / "qa"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_compact_roundabout_0218 as T18  # noqa: E402
from roads import carriageway_split as CS  # noqa: E402
from roads import compact_roundabout as CR  # noqa: E402
from roads import junctions as J  # noqa: E402
from roads import markings as MK  # noqa: E402
from roads import meshing as M  # noqa: E402
from roads import network as Nw  # noqa: E402
from roads import standards as S  # noqa: E402
import roundabout_ortho as RO  # noqa: E402
from terrain_mesh.gltf import smooth_normals  # noqa: E402

KERB = {"entry_r_m": 6.0, "exit_r_m": 8.0, "splitter_w_m": 2.4, "lane_w_m": 4.0, "crossing_offset_m": 5.0,
        "crossings": [T18.ARM_WAY, T18.ARM_WAY + 2]}
SPLIT = {"id": "split0", "kind": "carriageway_split", "node": "s0".lstrip("n"),
         "set": {"length_m": 25.0, "taper_m": 14.0, "lane_offset_m": 3.0}}


def _graph(split_ids=True):
    g = T18._graph()
    if split_ids:                         # carriageway_split addresses nodes as n<osm id>
        ren = {"s0": "ns0"}
        for n in g["nodes"]:
            n["id"] = ren.get(n["id"], n["id"])
        for e in g["edges"]:
            e["from"], e["to"] = ren.get(e["from"], e["from"]), ren.get(e["to"], e["to"])
    return g


def _world(opts=None, extra_ov=(), graph=None):
    ov = T18._ov(True, dict(KERB) if opts is None else opts) + list(extra_ov)
    net = Nw.load(graph or _graph(), (0.0, 0.0), ov)
    Nw.assign_sides(net, [], built_up=True, walkways=[], yards=None)
    juncs = J.build_junctions(net, [])
    T18._flat(net)
    return net, juncs


def _spec(juncs):
    return next(j for j in juncs if j.compact is not None)


def _between_arms(sp):
    """Asphalt of the outline that is neither the ring disc nor a mouth strip: the patches between the arms."""
    parts = [Point(*sp.center).buffer(sp.r_out, 96)]
    for m in sp.mouths.values():
        mid, off = m["mid"], m["half_w"]
        tg = np.gradient(mid, axis=0)
        tg /= np.hypot(*tg.T)[:, None]
        nl = np.column_stack([-tg[:, 1], tg[:, 0]])
        parts.append(Polygon(np.vstack([mid + nl * off[:, None], (mid - nl * off[:, None])[::-1]])).buffer(0))
    return sp.outline.difference(shapely.union_all(parts).buffer(0.05))


# ------------------------------------------------------------------------------------------- (a) kerb-mode outline
def test_kerb_mode_outline_is_one_simple_junction():
    net, juncs = _world()
    assert net.overrides_stale == []
    j = _spec(juncs)
    sp = j.compact
    assert CR.kerb_mode(sp.opts) and sp.notes == [] and len(j.arms) == 4
    poly = Polygon([p for p, _ in j.boundary])
    assert poly.is_valid and poly.is_simple and poly.exterior.is_ccw
    assert poly.exterior.distance(Point(*sp.center)) >= sp.r_in + T18.W_RING - 0.05, "ring asphalt keeps its width"
    grown = sp.outline.buffer(0.05)
    for c in sp.feeders:                                       # every designed lane lies on the patch, full width
        assert c.meta.get("cr_lane") and c.meta.get("absorbed")
        sv = np.linspace(0.5, c.length - 0.5, 40)
        for sg in (+1, -1):
            assert all(grown.contains(Point(*q)) for q in c.line.offset_point(sv, sg * c.hw_at(sv)))
    for c in j.corners:
        assert c.out is not None and np.allclose(np.hypot(*c.out.T), 1.0, atol=1e-6)


def test_mouth_is_not_wider_than_two_lanes_and_the_splitter():
    """(a): across an arm the asphalt is at most lane + splitter + lane; the ADR 0218 outline followed the outer
    edges of the mapped one-way carriageways (10.7 m apart at the ring here: 14.7 m of asphalt)."""
    net, juncs = _world()
    sp = _spec(juncs).compact
    wmax = 2 * (KERB["splitter_w_m"] / 2 + KERB["lane_w_m"])
    off = KERB["splitter_w_m"] / 2 + KERB["lane_w_m"] / 2
    for c in sp.feeders:                                       # lane axes: never further from the arm axis than off
        far = c.node_b if c.node_a[0] in "xe" else c.node_a  # ring nodes are x<k> / e<k>
        u = net.nodes[far]["xy"] / np.hypot(*net.nodes[far]["xy"])
        lat = np.abs(c.line.p @ np.array([-u[1], u[0]]))
        r = np.hypot(*c.line.p.T)
        assert lat[r > sp.r_out + KERB["exit_r_m"]].max() <= off + 0.05, "parallel to the arm axis"
        assert lat[r > sp.r_out + 0.5].max() <= off + 0.6, "the arc into the ring starts at the kerb return"
    for far, m in sp.mouths.items():
        mid = m["mid"]
        outside = np.hypot(*(mid - sp.center).T) > sp.r_out + 1.0
        assert float(m["half_w"][outside].max()) <= wmax / 2 + 0.3
        for k in range(5, len(mid) - 5, 5):
            if np.hypot(*(mid[k] - sp.center)) < sp.r_out + KERB["exit_r_m"]:
                continue                                       # inside the kerb returns the mouth opens into the ring
            t = mid[k + 1] - mid[k - 1]
            t /= np.hypot(*t)
            n = np.array([-t[1], t[0]])
            cut = LineString([mid[k] - n * 30, mid[k] + n * 30]).intersection(sp.outline)
            seg = min(getattr(cut, "geoms", [cut]), key=lambda g: g.distance(Point(*mid[k])))
            assert seg.length <= wmax + 0.3, (far, k, seg.length)
    net0, juncs0 = _world({"closing_r_m": 6.0})                # the same graph in ADR 0218 mode: wider at the ring
    sp0 = _spec(juncs0).compact
    ring2 = LineString(Point(*sp.center).buffer(sp.r_out + 2.0, 180).exterior.coords)
    assert ring2.intersection(sp.outline).length < 0.9 * ring2.intersection(sp0.outline).length


def test_patches_between_arms_are_bounded_by_the_kerb_radius_and_smaller_than_before():
    """(a): outside the ring disc and the mouth strips the asphalt is only what the kerb returns enclose - no point
    of it is further from a carriageway than a return of the authored radius can reach."""
    net, juncs = _world()
    sp = _spec(juncs).compact
    patch = _between_arms(sp)
    carriage = sp.outline.difference(patch)
    reach = max(KERB["entry_r_m"], KERB["exit_r_m"]) * (math.sqrt(2) - 1) + CR.NOSE_R_M * (math.sqrt(2) - 1) + 0.5
    for g in getattr(patch, "geoms", [patch]):
        if g.area < 0.05:
            continue
        far = max(carriage.distance(Point(*p)) for p in np.asarray(shapely.segmentize(g, 0.5).exterior.coords))
        assert far <= reach, (far, reach)


def test_generated_kerbs_read_back_with_the_orthophoto_ruler():
    """The measuring tool of docs/reports/roundabout-0274 on a raster of the generated outline (0.1 m / px): outer
    ring radius, a kerb return on both sides of every sector and the four splitter islands come back."""
    net, juncs = _world()
    sp = _spec(juncs).compact
    res, half = 0.1, 50.0
    n = int(2 * half / res)
    xs = (np.arange(n) + 0.5) * res - half
    X, Y = np.meshgrid(xs, -xs)
    isl = shapely.union_all([pg for _, pg in sp.splitters] + [Point(*sp.center).buffer(sp.r_in)])
    mask = shapely.contains_xy(sp.outline.difference(isl), X.ravel(), Y.ravel()).reshape(n, n)
    out = RO.measure_mask(mask, res, (n / 2 - 0.5, n / 2 - 0.5), sp.r_axis, [k * math.pi / 2 for k in range(4)])
    assert out["roundabout_visible"] and out["r_out_m"] == pytest.approx(sp.r_out, abs=0.3)
    radii = [s[k]["radius_m"] for s in out["sectors"] for k in ("return_after_from_arm", "return_before_to_arm") if s[k]]
    assert len(radii) == 8
    assert all(0.5 * KERB["entry_r_m"] <= r <= 2.0 * KERB["exit_r_m"] for r in radii), radii
    assert all(a["splitter_len_m"] >= 3.0 for a in out["arms"])
    plain = shapely.contains_xy(Point(0, 0).buffer(30), X.ravel(), Y.ravel()).reshape(n, n)
    assert RO.measure_mask(plain, res, (n / 2 - 0.5, n / 2 - 0.5), sp.r_axis, [0.0])["roundabout_visible"] is False


# ------------------------------------------------------------------------------------------- (b) carriageway split
def test_carriageway_split_moves_the_split_node_and_lengthens_the_island():
    g = _graph()
    before = copy.deepcopy(g)
    net0, juncs0 = _world()
    net, juncs = _world(extra_ov=[SPLIT], graph=g)
    assert g == before, "the ingested graph is not modified"
    assert net.overrides_stale == [] and any(a["id"] == "split0" for a in net.overrides_applied)
    sp0, sp = _spec(juncs0).compact, _spec(juncs).compact
    assert "ns0s" in sp.nodes and "ns0" not in net.nodes and sp.notes == []
    arm = next(a for a in _spec(juncs).arms if a.node == "ns0s")
    assert np.hypot(*net.nodes["ns0s"]["xy"]) == pytest.approx(T18.SPLIT_R + 25.0, abs=0.05)
    assert arm.chain.length == pytest.approx(90.0 - T18.SPLIT_R - 25.0, abs=0.1)

    def island_extent(s):                                      # along the +x arm, nose to tail (crossing gap included)
        xs = [x for _, pg in s.splitters for x, y in pg.exterior.coords if abs(y) < 3.0 and x > 0]
        return max(xs) - min(xs)
    assert island_extent(sp) >= island_extent(sp0) + 18.0
    assert island_extent(sp) >= 30.0, "island from the ring edge almost to the new split node"
    # the two lanes run parallel 3.0 m either side of the old centre line beside the long island
    feeders = [c for c in sp.feeders if "ns0s" in (c.node_a, c.node_b)]
    assert len(feeders) == 2
    for c in feeders:
        P = c.line.p
        par = P[(P[:, 0] > T18.SPLIT_R + 2.0) & (P[:, 0] < T18.SPLIT_R + 25.0 - 14.0 - 1.0)]
        assert len(par) >= 3 and np.allclose(np.abs(par[:, 1]), 3.0, atol=0.15)
    for _, pg in sp.splitters:                                 # lanes clear of every island
        for c in sp.feeders:
            assert pg.distance(LineString(c.line.p)) >= sp.opts["lane_clear_m"] - 0.05


@pytest.mark.parametrize("bad", [
    {"node": "nope", "set": {"length_m": 25.0}},
    {"node": "s0", "set": {"length_m": 70.0}},                 # longer than the two-way edge
    {"node": "s0", "set": {"length_m": "25"}},
    {"node": "s0", "set": {"length_m": float("nan")}},
    {"node": "s0", "set": {"length_m": 25.0, "lane_offset_m": 9.0}},
    {"node": "s0", "set": {"length_m": 25.0, "width": 3.0}},
    {"node": "x0", "set": {"length_m": 5.0}},                  # a ring node: not one two-way + two one-way edges
    {"node": "s0"},
])
def test_bad_carriageway_split_is_stale_and_changes_nothing(bad):
    g = _graph()
    ov = dict(bad, id="bad", kind=CS.KIND)
    applied, stale = [], []
    out = CS.apply(g, [ov], applied, stale)
    assert stale == ["bad"] and applied == []
    assert out["nodes"] == g["nodes"] and out["edges"] == g["edges"]
    net, juncs = _world(extra_ov=[ov])
    assert "bad" in net.overrides_stale and _spec(juncs).compact.notes == []


def test_carriageway_split_is_applied_once():
    applied, stale = [], []
    g1 = CS.apply(_graph(), [SPLIT], applied, stale)
    g2 = CS.apply(g1, [SPLIT], applied, stale)
    assert stale == [] and [a["id"] for a in applied] == ["split0", "split0"]
    assert g2["edges"] == g1["edges"] and CS.apply(_graph(), [], [], []) is not None


# ------------------------------------------------------------------------------------------- (c) centre island
def _tri_angles(V, T):
    P = V[T][:, :, :2]
    out = []
    for k in range(3):
        a, b, c = P[:, k], P[:, (k + 1) % 3], P[:, (k + 2) % 3]
        u, v = b - a, c - a
        out.append(np.degrees(np.arccos(np.clip((u * v).sum(1) / (np.hypot(*u.T) * np.hypot(*v.T)), -1, 1))))
    return np.column_stack(out)


@pytest.mark.parametrize("r0", [2.8, 5.0, 5.05, 1.2, 0.85])
def test_island_fill_has_no_fan_no_slivers_and_no_duplicate_ring(r0):
    n = 65
    V, T = CR.island_fill_mesh((3.0, -2.0), r0, np.zeros(n), 0.1)
    t = V[T]
    e1, e2 = t[:, 1, :2] - t[:, 0, :2], t[:, 2, :2] - t[:, 0, :2]
    area = 0.5 * np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0])
    assert area.min() > 1e-4, "no degenerate triangles (review D18 P2-2: integer r0 doubled a ring)"
    assert area.sum() == pytest.approx(0.5 * n * r0 * r0 * math.sin(2 * math.pi / n), rel=1e-6), "covers the disc once"
    assert (np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])[:, 2] > 0).all(), "faces look up"
    valence = np.bincount(T.ravel(), minlength=len(V))
    assert valence.max() <= 10, "no fan of one triangle per kerb sample"
    assert len(T) <= 5 * n + 2 * math.pi * r0 * r0 / (CR.FILL_RING_M * CR.FILL_SEG_M) + 10, "budget"
    ang = _tri_angles(V, T)
    inner = np.hypot(*(t[:, :, :2] - [3.0, -2.0]).transpose(2, 0, 1)).max(1) < r0 - CR.FILL_RIM_BAND_M + 1e-6
    if inner.any():
        assert ang[inner].min() >= 12.0, "no slivers inside the rim band"
    assert ang.min() >= 5.0


def test_island_fill_is_smooth_inside_a_rough_tilted_kerb_line():
    """(c): a tilted site with an uneven kerb line (junction-patch facets). Inside the rim band the vertex normals
    are the plane's normal within 0.5 deg and the height has no spokes; the old fill (every kerb sample's deviation
    carried along its radius) gave > 2 deg and a radial pattern."""
    n, r0 = 65, 2.8
    a = np.arange(n) * 2 * math.pi / n
    rng = np.random.default_rng(274)
    z_rim = 0.03 * r0 * np.cos(a) + 0.01 * r0 * np.sin(a) + rng.uniform(-0.015, 0.015, n)
    V, T = CR.island_fill_mesh((0.0, 0.0), r0, z_rim, 0.12)
    assert np.allclose(V[:n, 2], z_rim + 0.12), "kerb line kept exactly (watertight against the island kerb)"
    N = smooth_normals(V, T)
    plane = np.array([-0.03, -0.01, 1.0])
    plane /= np.linalg.norm(plane)
    r = np.hypot(*V[:, :2].T)
    inner = r < r0 - CR.FILL_RIM_BAND_M - 0.05
    dev = np.degrees(np.arccos(np.clip(N[inner] @ plane, -1, 1)))
    assert dev.max() < 0.5, dev.max()
    resid = V[inner, 2] - (0.03 * V[inner, 0] + 0.01 * V[inner, 1]) - 0.12
    assert np.abs(resid).max() < 0.006
    # the spoke pattern: the old construction reproduced here on the same kerb line
    pl = np.linalg.lstsq(np.column_stack([r0 * np.cos(a), r0 * np.sin(a), np.ones(n)]), z_rim, rcond=None)[0]
    old_dev = z_rim - r0 * (np.cos(a) * pl[0] + np.sin(a) * pl[1]) - pl[2]
    ring2 = old_dev * (2.0 / r0)                               # heights of the old ring at r = 2 about the plane
    old_slope = np.abs(np.diff(np.append(ring2, ring2[0]))) / (2 * math.pi * 2.0 / n)
    assert np.degrees(np.arctan(old_slope.max())) > 2.0


def test_island_fill_of_the_roundabout_is_meshed_with_rings():
    net, juncs = _world()
    buf, gp, rep = T18._mesh(net, juncs)
    assert rep[0]["built"] and rep[0]["notes"] == [] and rep[0]["mode"] == "kerbs"
    sp = _spec(juncs).compact
    fill = [p for p in buf.parts if p.layer == "road" and p.mat == "island_sand"]
    assert len(fill) == 1 and np.bincount(fill[0].T.ravel()).max() <= 10
    assert np.hypot(*(fill[0].V[:, :2] - sp.center).T).max() < sp.r_in - T18.W_APRON
    assert len(fill[0].T) <= 400, "budget: the old fill of this island was 2 x 2 x n + n = 325 triangles"


# ------------------------------------------------------------------------------------------- (d) P-13 and P-10
def test_p13_lies_along_the_ring_edge_on_every_entry_lane():
    """Dz.U. 2019 poz. 2311 zal. 2 pkt 4.2.4 (P-13 placed like P-12) + pkt 4.2.3 (along the edge of the carriageway
    with priority) + pkt 8.4 (entries of a roundabout marked as subordinate approaches)."""
    net, juncs = _world(extra_ov=[SPLIT])
    sp = _spec(juncs).compact
    assert len(sp.p13) == 4
    for cid, Q in sp.p13:
        r = np.hypot(*(Q - sp.center).T)
        assert np.allclose(r, sp.r_out + CR.P13_INSET_M, atol=0.01), "along the outer edge of the ring carriageway"
        length = float(np.sum(np.hypot(*np.diff(Q, axis=0).T)))
        assert CR.P13_MIN_M <= length <= KERB["lane_w_m"] + 0.5, "one entry lane wide"
        ang = np.unwrap(np.arctan2(*(Q - sp.center).T[::-1]))
        assert ang[-1] > ang[0], "drawn counter-clockwise: triangle tips point at the arriving driver"
        arm = next(a for a in _spec(juncs).arms if a.chain.id == cid)
        u = arm.direction(0.0)
        mid = Q[len(Q) // 2] - sp.center
        assert u[0] * mid[1] - u[1] * mid[0] > 0, "on the entry side (right-hand traffic: left of the outward axis)"
        assert np.hypot(*(Q - net.nodes[arm.node]["xy"]).T).min() > 10.0, "not at the split node"
    buf, gp, rep = T18._mesh(net, juncs)
    mrep = CR.build_markings(buf, net, juncs)
    assert mrep["P-13"] == 4 and mrep["tris_off_carriageway"] == 0
    tips = np.vstack([p.V for p in buf.parts if p.layer == "markings" and p.src.startswith("P-13@cr:")])
    rr = np.hypot(*(tips[:, :2] - sp.center).T)
    assert rr.min() >= sp.r_out + CR.P13_INSET_M - 0.02 and rr.max() <= sp.r_out + CR.P13_INSET_M + S.P13_H + 0.05
    assert np.allclose(tips[:, 2], S.MARKING_LIFT, atol=0.02), "decal just above the asphalt"


def test_crossings_are_offset_from_the_ring_and_cut_the_splitter():
    net, juncs = _world(extra_ov=[SPLIT])
    sp = _spec(juncs).compact
    assert sorted(c["osm_way"] for c in sp.crossings) == sorted(KERB["crossings"])
    isl = shapely.union_all([pg for _, pg in sp.splitters])
    for c in sp.crossings:
        assert c["near_edge_from_ring_m"] == pytest.approx(KERB["crossing_offset_m"], abs=0.05)
        assert len(c["lanes_lat_m"]) == 2, "entry lane and exit lane, the refuge between them"
        assert not isl.intersects(c["band"].buffer(-0.05)), "island cut through at the crossing"
        for g in c["stripes"]:
            assert sp.outline.buffer(-CR.P13_SIDE_M + 0.02).contains(g) and g.distance(isl) > 0.2
            e = np.hypot(*np.diff(np.asarray(g.exterior.coords)[:3], axis=0).T)
            assert sorted(np.round(e, 2)) == [S.P10_STRIPE, S.P10_WIDTH]
        arm = next(a for a in _spec(juncs).arms if a.chain.id == c["arm"])
        assert np.hypot(*(c["center"] - net.nodes[arm.node]["xy"])) > 5.0, "at the ring, not at the split node"
        assert abs(float(np.dot(c["dir"], arm.direction(0.0)))) > 0.95, "perpendicular to the arm"
    no_x = [a for a in _spec(juncs).arms if CR._arm_way(net, a) not in KERB["crossings"]]
    assert len(no_x) == 2 and len(sp.splitters) in (5, 6), "cut islands: two pieces (one, if the tail is < 3 m2)"
    assert sum(sid.startswith("cr:e0:splitter:ns0s:") for sid, _ in sp.splitters) == 2, "the long island: nose + tail"
    buf, gp, rep = T18._mesh(net, juncs)
    mrep = CR.build_markings(buf, net, juncs)
    assert mrep["P-10"] == 2 and mrep["tris_off_carriageway"] == 0
    assert len([i for i in gp.islands if i.built]) == len(sp.splitters)


def test_generic_markings_leave_the_compact_roundabout_alone():
    """No P-13 at the ends of the two-way arms and no zebra snapped to a split node any more."""
    net, juncs = _world()
    buf, gp, rep = T18._mesh(net, juncs)
    sp = _spec(juncs).compact
    s1 = net.nodes["s1"]["xy"]
    ctx = [{"kind": "highway=crossing", "osm_node": 5_000_001, "e": float(s1[0]), "n": float(s1[1])}]
    report = {}
    MK.build_markings(buf, net, juncs, ctx, report)
    src = [p.src for p in buf.parts if p.layer == "markings"]
    assert not any(s.startswith("P-13@c:") for s in src), "P-13 only along the ring"
    assert sum(s.startswith("P-13@cr:") for s in src) > 0
    assert report["markings"].get("P-13 at compact roundabout") == 4
    assert report["markings"].get("P-10 crossing", 0) == 0 and report.get("crossings_snapped") == 0
    # ADR 0218 mode keeps the generic rule
    net0, juncs0 = _world({"closing_r_m": 6.0})
    buf0, _, _ = T18._mesh(net0, juncs0)
    MK.build_markings(buf0, net0, juncs0, [], {})
    assert any(p.src.startswith("P-13@c:") for p in buf0.parts if p.layer == "markings")


def test_crossing_on_a_way_that_is_no_arm_is_reported():
    net, juncs = _world(dict(KERB, crossings=[12345]))
    assert any("12345" in n for n in _spec(juncs).compact.notes)


# ------------------------------------------------------------------------------------------- review s23 D18
@pytest.mark.parametrize("bad", [{"closing_r_m": "6"}, {"closing_r_m": -1}, {"closing_r_m": float("nan")},
                                 {"entry_r_m": 0.5}, {"lane_w_m": True}, {"crossings": ["x"]}, {"crossings": 5},
                                 {"island_fill": "lava"}, {"entry_r_m": 6.0, "unknown": 1}])
def test_option_values_are_validated(bad):
    net, juncs = _world(bad)                                   # no exception anywhere
    assert "compact" in net.overrides_stale and all(j.compact is None for j in juncs)


def test_valid_options_pass_validation():
    assert CR.validate({}) == {} and CR.validate(KERB) == {k: (float(v) if not isinstance(v, list) else v) for k, v in KERB.items()}
    assert CR.validate({"closing_r_m": 6}) == {"closing_r_m": 6.0}


def test_corner_with_one_outline_vertex_does_not_raise():
    ext = np.array([[0.0, 0.0], [5.0, 0.0], [5.0, 5.0], [0.0, 5.0]])
    pts, touch = CR._corner_points(ext, 2, 2, np.array([5.0, 5.0]), np.array([5.0, 5.0]), np.array([1.0, 0.0]))
    assert touch and len(pts) == 2 and np.hypot(*(pts[1] - pts[0])) > 0
    tg = np.gradient(pts, axis=0)                              # what corners() does next
    assert np.isfinite(tg).all()
    pts, touch = CR._corner_points(ext, 3, 1, np.array([0.0, 5.0]), np.array([5.0, 0.0]), np.array([1.0, 0.0]))
    assert not touch and len(pts) == 3


def test_ring_too_small_for_compact_mode_is_stale():
    ov = [{"id": "ring", "target": {"osm_way": [T18.RING_WAY]}, "set": {"width": 15.0}},
          {"id": "compact", "target": {"osm_way": [T18.RING_WAY]}, "set": {"compact_roundabout": {}}}]
    net = Nw.load(_graph(), (0.0, 0.0), ov)
    Nw.assign_sides(net, [], built_up=True, walkways=[], yards=None)
    juncs = J.build_junctions(net, [])                         # r_axis 8.65 - 7.5 < 1.5 m: no island fits
    assert "compact" in net.overrides_stale and all(j.compact is None for j in juncs)


@pytest.mark.parametrize("bad", ["3.4", -1.0, float("nan"), True, 500.0])
def test_edge_line_spacing_value_is_validated(bad):
    ov = [{"id": "els", "target": {"osm_way": [T18.ARM_WAY]}, "set": {"edge_lines": "both", "edge_line_spacing": bad}}]
    net = Nw.load(_graph(), (0.0, 0.0), ov)
    assert "els" in net.overrides_stale and all(s.edge_line_spacing is None for s in net.sec_list)
    ok = Nw.load(_graph(), (0.0, 0.0), [dict(ov[0], set={"edge_lines": "both", "edge_line_spacing": 6.8})])
    assert ok.overrides_stale == [] and any(s.edge_line_spacing == 6.8 for s in ok.sec_list)


@pytest.mark.parametrize("bad", [
    {"id": "d", "line_en": [[40, 0], [80, 0]], "side": "left", "line": "P-99"},
    {"id": "d", "line_en": [[40, 0], [80, 0]], "side": "left", "dash_m": [1.0]},
    {"id": "d", "line_en": [[40, 0], [80, 0]], "side": "left", "dash_m": [1.0, "x"]},
    {"id": "d", "line_en": [[40, 0], [80, 0]], "side": "left", "dash_m": [0.0, 1.0]},
    {"id": "d", "line_en": "nonsense", "side": "left"},
    {"line_en": [[40, 0], [80, 0]], "side": "left"},
])
def test_malformed_edge_line_dashed_is_stale_not_an_exception(bad):
    net = Nw.load(_graph(), (0.0, 0.0), [])
    rep = {}
    out = MK.edge_dashed_spans(net, [dict(bad, kind=MK.EDGE_DASHED_KIND)], rep)
    assert out == {} and rep["edge_line_dashed"]["stale"] == [bad.get("id", "?")]


def test_roads_qa_carries_the_compact_roundabout_report():
    from roads import build_world as BW
    src = inspect.getsource(BW.qa_report)
    assert '"compact_roundabouts": w.stats.get("compact_roundabouts", [])' in src
    from roads import pipeline as PL
    assert 'stats["compact_roundabouts"] = CR.build(' in inspect.getsource(PL.build)


# ------------------------------------------------------------------------------------------- Knyszyn (data in git)
@pytest.fixture(scope="module")
def knyszyn():
    from roads import pipeline as PL
    rid = "knyszyn"
    region = PL.load_region(rid)
    origin = (region["origin"]["x"], region["origin"]["y"])
    ctx = json.loads((PL.REGIONS / rid / "generated" / "osm_context.json").read_text(encoding="utf-8"))
    net, graph, overrides, _ = PL.build_network(rid)
    pts, foot = PL.ctx_local(ctx, origin)
    walk = [LineString(np.array(f["geometry"]) - np.array(origin)) for f in ctx["footways"] if f["highway"] != "path"]
    Nw.assign_sides(net, foot, built_up=True, walkways=walk, yards=None)
    juncs = J.build_junctions(net, pts)
    T18._flat(net)
    j = _spec(juncs)
    buf = M.MeshBuf()                                           # heights flat: Data/raw (NMT) is not in git
    M.build_patch(buf, net, j)
    M.build_patch(buf, net, j, coarse=True)
    rep = CR.build(buf, net, [j])
    mrep = CR.build_markings(buf, net, [j])
    return net, j, buf, rep, mrep, overrides


def test_knyszyn_roundabout_is_built_without_notes(knyszyn):
    net, j, buf, rep, mrep, overrides = knyszyn
    assert [o for o in net.overrides_stale if "roundabout" in o] == []
    assert {"knyszyn-roundabout-dk65-split-s", "knyszyn-roundabout-dk65-split-n"} <= {a["id"] for a in net.overrides_applied}
    assert len(rep) == 1 and rep[0]["built"] is True and rep[0]["notes"] == [], rep
    assert rep[0]["mode"] == "kerbs" and rep[0]["ring_asphalt_m"] == pytest.approx(5.0, abs=0.05)
    assert rep[0]["apron_m"] == pytest.approx(3.2) and rep[0]["p13_entries"] == 4 and len(rep[0]["crossings"]) == 4
    assert mrep["P-13"] == 4 and mrep["P-10"] == 4 and mrep["tris_off_carriageway"] == 0
    poly = Polygon([p for p, _ in j.boundary])
    assert poly.is_valid and poly.is_simple and len(j.arms) == 4
    # budget: the star-shaped kerb-mode outline must not be meshed as polar rings (25 194 triangles); ADR 0218: 732
    patch = sum(len(p.T) for p in buf.parts if p.layer == "road" and p.src == j.id and p.mat.startswith("road_"))
    assert patch <= 2500, patch                                 # 1 840 on flat heights


def test_knyszyn_islands_have_the_authored_lengths(knyszyn):
    """(b): S about 30 m, N about 20 m from the ring edge (ESTIMATED / WORKING_VALUE in overrides.yaml: the 2025
    orthophoto predates the roundabout), W / E as mapped."""
    net, j, buf, rep, mrep, overrides = knyszyn
    sp = j.compact
    ext = {}
    for a in j.arms:
        m = sp.mouths[a.node]
        own = [pg for _, pg in sp.splitters if pg.distance(LineString(m["mid"])) < 0.5]
        r = [np.hypot(*(np.asarray(pg.exterior.coords) - sp.center).T) for pg in own]
        ext[CR._arm_way(net, a)] = (min(x.min() for x in r) - sp.r_out, max(x.max() for x in r) - sp.r_out, len(own))
    assert 28.0 <= ext[286990127][1] <= 33.0, ext                # DK65 south
    assert 33.0 <= ext[232511646][1] <= 38.0, ext                # DK65 north (rynek-s23: photo 9, >= 34 m)
    assert all(lo == pytest.approx(sp.opts["splitter_gap_m"], abs=0.3) for lo, hi, n in ext.values()), ext
    assert all(n in (1, 2) for lo, hi, n in ext.values()) and ext[286990127][2] == ext[232511646][2] == 2
    isl = shapely.union_all([pg for _, pg in sp.splitters])
    assert all(not isl.intersects(c["band"].buffer(-0.05)) for c in sp.crossings), "islands cut through at the crossings"
    assert ext[1478765548][1] < 20.0 and ext[1464342641][1] < 20.0
    for _, pg in sp.splitters:
        e = np.hypot(*np.diff(np.asarray(pg.minimum_rotated_rectangle.exterior.coords)[:3], axis=0).T)
        assert min(e) <= sp.opts["splitter_w_m"] + 0.2
        for c in sp.feeders:
            assert pg.distance(LineString(c.line.p)) >= sp.opts["lane_clear_m"] - 0.05


def _knyszyn_adr0218():
    """The int-dk65-s22 build of this roundabout: same graph, the ADR 0218 key, no DK65 split."""
    from roads import pipeline as PL
    region = PL.load_region("knyszyn")
    origin = (region["origin"]["x"], region["origin"]["y"])
    graph = json.loads((PL.REGIONS / "knyszyn" / "roads.graph.json").read_text(encoding="utf-8"))
    ov = [copy.deepcopy(o) for o in PL.load_overrides("knyszyn") if o.get("kind") != CS.KIND]
    next(o for o in ov if o["id"] == "knyszyn-roundabout-compact")["set"] = {
        "compact_roundabout": {"closing_r_m": 6.0, "splitter_w_m": 3.6, "lane_w_m": 4.0}}
    net = Nw.load(graph, origin, ov)
    ctx = json.loads((PL.REGIONS / "knyszyn" / "generated" / "osm_context.json").read_text(encoding="utf-8"))
    pts, foot = PL.ctx_local(ctx, origin)
    Nw.assign_sides(net, foot, built_up=True, walkways=[], yards=None)
    return _spec(J.build_junctions(net, pts)).compact


def _mouths_on(sp, d):
    """Lengths of the pieces of the circle r_out + d that lie on the outline: one per arm."""
    th = np.radians(np.arange(0, 360, 0.25))
    P = sp.center + (sp.r_out + d) * np.column_stack([np.cos(th), np.sin(th)])
    on = np.roll(shapely.contains_xy(sp.outline, P[:, 0], P[:, 1]), -int(np.argmin(shapely.contains_xy(sp.outline, P[:, 0], P[:, 1]))))
    runs, cur = [], 0
    for v in on:
        if v:
            cur += 1
        elif cur:
            runs.append(cur)
            cur = 0
    if cur:
        runs.append(cur)
    return [r * math.radians(0.25) * (sp.r_out + d) for r in runs]


def test_knyszyn_outline_is_tighter_than_adr_0218(knyszyn):
    """(a): mouths 2 m outside the ring kerb 13.1 / 11.8 / 12.9 / 13.4 m -> 10.9-11.5 m, asphalt within 3 m of the
    ring kerb 165.5 -> 141.3 m2, and the mouths no longer narrow away from the ring (funnels)."""
    net, j, buf, rep, mrep, overrides = knyszyn
    sp, sp0 = j.compact, _knyszyn_adr0218()
    m2, m2_old = _mouths_on(sp, 2.0), _mouths_on(sp0, 2.0)
    assert len(m2) == len(m2_old) == 4
    assert max(m2) <= 11.6 and min(m2_old) >= 11.7, (m2, m2_old)
    near = [s.outline.intersection(Point(*s.center).buffer(s.r_out + 3.0)).area - math.pi * s.r_out ** 2 for s in (sp, sp0)]
    assert near[0] < 0.88 * near[1], near
    assert all(b - a < -1.0 for a, b in zip(sorted(_mouths_on(sp0, 2.0)), sorted(_mouths_on(sp0, 8.0)))), "0218: funnels"
    assert all(abs(b - a) <= 0.8 for a, b in zip(sorted(m2), sorted(_mouths_on(sp, 5.0)))), "0274: parallel mouths"
    patch = _between_arms(sp)
    carriage = sp.outline.difference(patch)
    reach = 8.0 * (math.sqrt(2) - 1) + CR.NOSE_R_M * (math.sqrt(2) - 1) + 0.5
    far = max(carriage.distance(Point(*p)) for g in getattr(patch, "geoms", [patch]) if g.area > 0.05
              for p in np.asarray(shapely.segmentize(g, 0.5).exterior.coords))
    assert far <= reach, far


def test_knyszyn_route_keeps_clear_of_the_islands(knyszyn):
    net, j, buf, rep, mrep, overrides = knyszyn
    sp = j.compact
    route = json.loads((ROOT / "Data/Regions/knyszyn/route_start.json").read_text(encoding="utf-8"))
    P = np.array(route["points_en"])
    near = P[np.hypot(*(P - sp.center).T) < 60.0]
    assert len(near) > 20
    line = LineString(near)
    assert min(line.distance(pg) for _, pg in sp.splitters) >= 1.5, "truck half width 1.275 m + margin"
    inside = [p for p in near if np.hypot(*(p - sp.center)) < 30.0]
    assert all(sp.outline.contains(Point(*p)) for p in inside)
    assert "n4898926854" in route["graph_nodes"], "route nodes stay ids of the ingested graph"


def test_knyszyn_overrides_and_probe_are_consistent():
    import yaml
    ovs = yaml.safe_load((ROOT / "Data/Regions/knyszyn/overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    o = next(o for o in ovs if o["id"] == "knyszyn-roundabout-compact")
    assert CR.validate(o["set"]["compact_roundabout"]) is not None and o["confidence"] == "low"
    assert "8 m kerb returns" not in o["reason"] and "gravel island" not in o["reason"], "review D18 P2-11"
    assert sum(1 for o in ovs if o.get("kind") == CS.KIND) == 2
    probe = json.loads((ROOT / "docs/reports/roundabout-0274/knyszyn_ortho_probe.json").read_text(encoding="utf-8"))
    assert probe["roundabout_visible"] is False, "when a newer orthophoto shows the roundabout, measure and re-author"
    assert max(s["date"] for s in probe["source"]["sheets_at_centre"]) == "2025-05-27"


# ------------------------------------------------------------------------------------------- (c) plants and stones
def _island_buf(center=(0.0, 0.0), r=3.0, z=0.3):
    buf = M.MeshBuf()
    V, T = CR.island_fill_mesh(center, r, np.full(48, z))
    buf.add("road", "island_sand", V, V[:, :2].copy(), T, src="island:test:fill")
    return buf


def _plant(buf, ov, origin=(0.0, 0.0)):
    from streetscape import plantings as PT
    rep = {}
    before = len(buf.parts)
    PT.build(buf, [ov], origin, Polygon(), buf.parts[:before], lambda e, n: np.zeros(len(np.atleast_1d(e))),
             lambda e, n: False, rep)
    return rep["plantings"], buf.parts[before:]


def test_authored_clumps_and_stones_stand_on_the_island_top():
    buf = _island_buf()
    ov = {"id": "isl", "kind": "plantings",
          "clumps": [{"at": [1.0, 0.5], "r_m": 0.35, "height_m": 0.4, "plant": "privet"}],
          "stones": [{"at": [-1.0, 0.2], "r_m": 0.3, "height_m": 0.25}, {"at": [0.0, -1.5], "r_m": 0.2, "height_m": 0.15}]}
    rep, parts = _plant(buf, ov)
    assert rep["stale"] == [] and rep["clumps"] == 1 and rep["stones"] == 2
    stones = [p for p in parts if p.mat == "bed_stones"]
    assert len(stones) == 2 and all(len(p.T) == 49 for p in stones)
    for p in stones:
        assert p.V[:, 2].min() < 0.3 < p.V[:, 2].max() <= 0.3 + 0.25 * 1.07, "half sunk in the bed, authored height"
        t = p.V[p.T]
        c = p.V.mean(0)
        assert (np.einsum("ij,ij->i", np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), t.mean(1) - c) > 0).all()
    shrub = [p for p in parts if p.mat.startswith("hedge")]
    top = max(p.V[:, 2].max() for p in shrub)
    assert shrub and 0.3 + 0.25 <= top <= 0.3 + 0.65, "a low shrub on the island top, not on the terrain"
    assert all(np.hypot(*(p.V[:, :2] - [1.0, 0.5]).T).max() < 1.0 for p in shrub)


@pytest.mark.parametrize("item,kind", [({"at": [9.0, 9.0], "r_m": 0.3, "height_m": 0.3}, "stones"),      # off the island
                                       ({"at": [0.0, 0.0], "r_m": 5.0, "height_m": 0.3}, "stones"),
                                       ({"at": [0.0, 0.0], "r_m": 0.3, "height_m": 2.5}, "clumps"),
                                       ({"at": [0.0], "r_m": 0.3, "height_m": 0.3}, "clumps"),
                                       ({"at": [0.0, 0.0], "r_m": "x", "height_m": 0.3}, "stones"),
                                       ({"r_m": 0.3, "height_m": 0.3}, "clumps")])
def test_bad_island_item_is_stale(item, kind):
    rep, parts = _plant(_island_buf(), {"id": "isl", "kind": "plantings", kind: [item]})
    assert rep["stale"] == [f"isl:{kind[:-1]}0"] and parts == []


def test_knyszyn_island_plantings_are_low_clear_of_the_kerb_and_in_budget(knyszyn):
    import yaml
    net, j, buf, rep, mrep, overrides = knyszyn
    sp = j.compact
    ov = next(o for o in overrides if o["id"] == "knyszyn-roundabout-island-plantings")
    origin = net.origin
    r_island = sp.r_in - sp.apron[2]                           # island kerb face
    items = [(it, "clump") for it in ov["clumps"]] + [(it, "stone") for it in ov["stones"]]
    assert 3 <= len(ov["clumps"]) <= 6 and 3 <= len(ov["stones"]) <= 8
    P = np.array([[it["at"][0] - origin[0], it["at"][1] - origin[1]] for it, _ in items])
    for (it, kind), p in zip(items, P):
        d = float(np.hypot(*(p - sp.center)))
        assert d + it["r_m"] * 1.3 <= r_island - 0.5, (kind, d, "0.5 m inside the kerb face: trailer overhang")
        assert it["height_m"] <= (0.6 if kind == "clump" else 0.35), "low: nothing hides a car across the island"
    dd = np.hypot(*(P[:, None] - P[None]).transpose(2, 0, 1)) + np.eye(len(P)) * 9
    rr = np.array([it["r_m"] for it, _ in items])
    assert (dd >= (rr[:, None] + rr[None]) * 0.9).all(), "no two items in each other"
    prep, parts = _plant(buf, ov, origin)                       # on the island fill built from the git data
    assert prep["stale"] == [] and prep["clumps"] == len(ov["clumps"]) and prep["stones"] == len(ov["stones"])
    tris = sum(len(p.T) for p in parts)
    assert tris <= 1300, tris
    assert len({p.mat for p in parts}) <= 4
    assert ov["confidence"] == "low" and "ESTIMATED" in ov["reason"]
