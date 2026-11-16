"""ADR 0218 section 5c: compact roundabout built as ONE junction (roads/compact_roundabout.py).

Synthetic 4-arm roundabout whose arms split into one-way entry / exit carriageways (the Knyszyn layout: 8 ring nodes),
pure Python, no Data/raw:
  * without the key the generic machinery runs (several junctions on the ring) - nothing changes;
  * with `compact_roundabout` on the ring way: one junction, ring + feeders absorbed, a simple (not self-intersecting)
    outline, ring asphalt of the authored width everywhere, a full apron annulus of the authored width / material,
    island fill inside, 4 kerbed splitter islands clear of the lanes;
  * a malformed key / a key on a way that is not a ring is stale.
Run: uv run --project tools/worldgen python -m pytest tests/gis/test_compact_roundabout_0218.py -q
"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import LineString, Point, Polygon

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "worldgen"))

from roads import compact_roundabout as CR  # noqa: E402
from roads import gores as GO  # noqa: E402
from roads import junctions as J  # noqa: E402
from roads import meshing as M  # noqa: E402
from roads import network as Nw  # noqa: E402

R_AXIS, W_RING, W_APRON, LIP = 8.65, 5.0, 3.2, 0.04
RING_WAY, ARM_WAY, FEED_WAY = 900, 910, 920
SPLIT_R = 30.0          # split node of each arm, m from the centre
HALF_GAP = 0.62         # entry / exit ring nodes this angle (rad) either side of the arm axis (~10.7 m apart)


def _a(v, src="osm"):
    return {"v": v, "src": src, "conf": "high"}


def _graph():
    nodes, edges = [], []
    ring_pts = []
    for k in range(4):
        t = k * math.pi / 2
        ax = np.array([math.cos(t), math.sin(t)])
        nodes.append({"id": f"s{k}", "x": float(SPLIT_R * ax[0]), "y": float(SPLIT_R * ax[1])})
        nodes.append({"id": f"o{k}", "x": float(90 * ax[0]), "y": float(90 * ax[1])})
        for nm, dt in (("x", -HALF_GAP), ("e", +HALF_GAP)):      # counter-clockwise ring: exit node first, then entry
            nodes.append({"id": f"{nm}{k}", "x": R_AXIS * math.cos(t + dt), "y": R_AXIS * math.sin(t + dt)})
            ring_pts.append((t + dt, f"{nm}{k}"))
        two = {"highway": _a("secondary"), "oneway": _a("no"), "lanes": _a(2), "width": _a(7.0),
               "surface": _a("asphalt"), "maxspeed": _a(50)}
        sp = [float(SPLIT_R * ax[0]), float(SPLIT_R * ax[1])]
        edges.append({"id": f"w{ARM_WAY + k}:s{k}-o{k}", "from": f"s{k}", "to": f"o{k}", "attrs": two,
                      "osm_way": ARM_WAY + k, "length_m": 90.0 - SPLIT_R,
                      "geometry": [sp, [float(90 * ax[0]), float(90 * ax[1])]]})
        one = {"highway": _a("secondary"), "oneway": _a("yes"), "lanes": _a(1), "width": _a(4.0),
               "surface": _a("asphalt"), "maxspeed": _a(50)}
        pe = [R_AXIS * math.cos(t + HALF_GAP), R_AXIS * math.sin(t + HALF_GAP)]
        px = [R_AXIS * math.cos(t - HALF_GAP), R_AXIS * math.sin(t - HALF_GAP)]
        # right-hand traffic, counter-clockwise ring: leave the ring at x (before the arm axis), enter at e (after it)
        edges.append({"id": f"w{FEED_WAY + 2 * k}:x{k}-s{k}", "from": f"x{k}", "to": f"s{k}", "attrs": dict(one),
                      "osm_way": FEED_WAY + 2 * k, "length_m": 24.0,
                      "geometry": [px, sp]})
        edges.append({"id": f"w{FEED_WAY + 2 * k + 1}:s{k}-e{k}", "from": f"s{k}", "to": f"e{k}", "attrs": dict(one),
                      "osm_way": FEED_WAY + 2 * k + 1, "length_m": 24.0,
                      "geometry": [sp, pe]})
    ring_pts.sort()
    ra = {"highway": _a("secondary"), "junction": _a("roundabout"), "oneway": _a("yes", "derived"), "lanes": _a(1),
          "width": _a(4.0), "surface": _a("asphalt"), "maxspeed": _a(50)}
    for i, (t0, n0) in enumerate(ring_pts):
        t1, n1 = ring_pts[(i + 1) % len(ring_pts)]
        if t1 < t0:
            t1 += 2 * math.pi
        tt = np.linspace(t0, t1, max(3, int((t1 - t0) * R_AXIS / 0.8) + 2))
        edges.append({"id": f"w{RING_WAY}:{n0}-{n1}", "from": n0, "to": n1, "attrs": dict(ra),
                      "osm_way": RING_WAY, "length_m": float((t1 - t0) * R_AXIS),
                      "geometry": [[R_AXIS * math.cos(t), R_AXIS * math.sin(t)] for t in tt]})
    return {"nodes": nodes, "edges": edges}


def _ov(compact=True, extra=None):
    ov = [{"id": "ring", "target": {"osm_way": [RING_WAY]},
           "set": {"width": W_RING, "truck_apron": {"width_m": W_APRON, "height_m": LIP, "material": "kostka_jasna"}}}]
    if compact:
        ov.append({"id": "compact", "target": {"osm_way": [RING_WAY]},
                   "set": {"compact_roundabout": extra if extra is not None else {"closing_r_m": 6.0}}})
    return ov


def _flat(net):
    for c in net.chains:
        c.z = np.zeros(len(c.line.s))
        c.e = np.zeros(len(c.line.s))


def _world(compact=True, extra=None):
    net = Nw.load(_graph(), (0.0, 0.0), _ov(compact, extra))
    Nw.assign_sides(net, [], built_up=True, walkways=[], yards=None)
    juncs = J.build_junctions(net, [])
    _flat(net)
    return net, juncs


def _mesh(net, juncs):
    buf = M.MeshBuf()
    gp = GO.GorePlan()
    CR.plan_islands(net, juncs, gp)
    for c in net.chains:
        M.build_ribbon(buf, net, c)
        M.build_ribbon(buf, net, c, coarse=True)
    for j in juncs:
        M.build_patch(buf, net, j)
        M.build_patch(buf, net, j, coarse=True)
    GO.build(buf, net, gp)
    rep = CR.build(buf, net, juncs)
    return buf, gp, rep


def test_without_the_key_nothing_changes():
    net, juncs = _world(compact=False)
    assert all(j.compact is None for j in juncs)
    assert len([j for j in juncs if j.roundabout]) > 1, "generic machinery: several junctions on the ring"
    assert CR.specs(net) == [] and net.overrides_stale == []
    assert CR.build(M.MeshBuf(), net, juncs) == []


def test_one_junction_with_a_simple_outline():
    net, juncs = _world()
    assert net.overrides_stale == []
    cj = [j for j in juncs if j.compact is not None]
    assert len(cj) == 1
    j, sp = cj[0], cj[0].compact
    assert len(j.arms) == 4 and j.roundabout and sp.notes == []
    assert len(sp.ring) == 8 and len(sp.feeders) == 8
    assert all(c.meta.get("absorbed") for c in sp.ring + sp.feeders), "ring and feeders build no ribbons"
    assert np.hypot(*sp.center) < 0.05 and sp.r_axis == pytest.approx(R_AXIS, abs=0.1)
    poly = Polygon([p for p, _ in j.boundary])
    assert poly.is_valid and poly.is_simple, "junction patch outline does not self-intersect"
    assert poly.exterior.is_ccw
    # ring asphalt: the outer kerb is nowhere closer to the centre than apron lip + authored ring width
    assert poly.exterior.distance(Point(*sp.center)) >= sp.r_in + W_RING - 0.05
    assert sp.r_out - sp.r_in == pytest.approx(W_RING, abs=0.05)
    # every feeder lane lies on the patch
    grown = poly.buffer(0.05)
    for c in sp.feeders:
        s = np.linspace(0.5, c.length - 0.5, 30)
        for sg in (+1, -1):
            for p in c.line.offset_point(s, sg * c.hw_at(s)):
                assert grown.contains(Point(*p))
    # corners carry explicit unit outward normals pointing out of the patch
    for c in j.corners:
        assert c.out is not None and len(c.out) == len(c.arc)
        assert np.allclose(np.hypot(*c.out.T), 1.0, atol=1e-6)
        mid = len(c.arc) // 2
        assert not poly.contains(Point(*(c.arc[mid] + 0.3 * c.out[mid])))


def test_four_splitter_islands_clear_of_the_lanes():
    net, juncs = _world()
    sp = next(j for j in juncs if j.compact is not None).compact
    assert len(sp.splitters) == 4
    for _, pg in sp.splitters:
        assert pg.is_valid and pg.area >= CR.SPLITTER_MIN_M2
        assert sp.outline.contains(pg), "island on the patch"
        assert pg.distance(Point(*sp.center)) >= sp.r_out + 0.5, "nose outside the ring carriageway"
        e = np.hypot(*np.diff(np.asarray(pg.minimum_rotated_rectangle.exterior.coords)[:3], axis=0).T)
        assert min(e) <= CR.DEFAULTS["splitter_w_m"] + 0.3 and max(e) >= 1.8 * min(e), "narrow and elongated"
        for c in sp.feeders:                                  # the lane about every feeder axis stays clear
            assert pg.distance(LineString(c.line.p)) >= CR.DEFAULTS["lane_clear_m"] - 0.05


def test_apron_annulus_island_and_kerbs_are_meshed():
    net, juncs = _world()
    buf, gp, rep = _mesh(net, juncs)
    assert len(rep) == 1 and rep[0]["built"] and rep[0]["splitters"] == 4
    assert rep[0]["ring_asphalt_m"] == pytest.approx(W_RING, abs=0.05) and rep[0]["apron_m"] == pytest.approx(W_APRON)
    sp = next(j for j in juncs if j.compact is not None).compact
    ap = [p for p in buf.parts if p.layer == "road" and p.mat == "apron_paving_light"]
    assert ap, "light apron surface"
    V = np.vstack([p.V[p.T].reshape(-1, 3) for p in ap])
    r = np.hypot(*(V[:, :2] - sp.center).T)
    assert r.max() == pytest.approx(sp.r_in, abs=0.03) and r.min() == pytest.approx(sp.r_in - W_APRON, abs=0.03)
    ang = np.degrees(np.arctan2(V[:, 1] - sp.center[1], V[:, 0] - sp.center[0])) % 360
    assert np.diff(np.sort(ang)).max() < 12.0, "a full ring, no gaps"
    assert V[r > sp.r_in - 0.05, 2].max() == pytest.approx(LIP, abs=0.005), "lip height at the asphalt"
    assert V[r < sp.r_in - W_APRON + 0.05, 2].min() == pytest.approx(LIP + 0.02 * W_APRON, abs=0.005)
    for p in ap:                                              # top faces look up
        t = p.V[p.T]
        assert (np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])[:, 2] > 0).all()
    fill = [p for p in buf.parts if p.layer == "road" and p.mat == "island_sand"]
    assert fill and max(np.hypot(*(p.V[:, :2] - sp.center).T).max() for p in fill) < sp.r_in - W_APRON
    for p in fill:
        t = p.V[p.T]
        assert (np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])[:, 2] > 0).all()
    # nothing of the patch asphalt stands above the apron
    for p in buf.parts:
        if p.layer == "road" and p.mat.startswith("road_") and p.src.startswith("j:"):
            U = p.V[np.unique(p.T)]                           # vertices in use
            rr = np.hypot(*(U[:, :2] - sp.center).T)
            assert U[rr < sp.r_in - 0.3, 2].max(initial=-1.0) < 0.0
    assert any(p.layer == "collision" and p.src.startswith("island:cr:") for p in buf.parts)
    assert len([i for i in gp.islands if i.built]) == 4, "splitters built with kerbs"
    from roads import build_world as BW

    def lum(c):
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    assert lum(BW.MATERIALS["island_sand"]["color"]) < 0.7 * lum(BW.MATERIALS["apron_paving_light"]["color"])


@pytest.mark.parametrize("bad", [{"closing": 3}, [1, 2], "yes"])
def test_malformed_key_is_stale(bad):
    net, juncs = _world(extra=bad)
    assert "compact" in net.overrides_stale and all(j.compact is None for j in juncs)


def test_key_on_a_way_that_is_not_a_ring_is_stale():
    ov = _ov(compact=False) + [{"id": "arm", "target": {"osm_way": [ARM_WAY, ARM_WAY + 1]}, "set": {"compact_roundabout": {}}}]
    net = Nw.load(_graph(), (0.0, 0.0), ov)
    assert "arm" in net.overrides_stale


def test_knyszyn_override_is_authored():
    import yaml
    root = Path(__file__).resolve().parents[2]
    ovs = yaml.safe_load((root / "Data/Regions/knyszyn/overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    o = next(o for o in ovs if o["id"] == "knyszyn-roundabout-compact")
    assert o["target"] == {"osm_way": [1426801304]} and set(o["set"]) == {"compact_roundabout"}
    others = [p for p in sorted((root / "Data/Regions").glob("*/overrides.yaml"))
              if p.parent.name != "knyszyn" and "compact_roundabout" in p.read_text(encoding="utf-8")]
    assert others == [], "only the Knyszyn ring is built in compact mode"
