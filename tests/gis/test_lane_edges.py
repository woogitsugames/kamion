"""Cross-sections measured on the orthophoto and authored paint (ADR 0095).

Unit checks of the override semantics (no build needed) + checks of the built region (roads_qa.json)."""
from __future__ import annotations

import json

import numpy as np
import pytest
import yaml

from conftest import REGION_DIR

QA = REGION_DIR / "generated" / "roads_qa.json"


def _net(set_, oneway="yes", lanes=3):
    from roads import network as Nw
    attrs = {k: {"v": v, "src": "osm", "conf": "high"} for k, v in
             dict(highway="trunk", oneway=oneway, lanes=lanes, width=8.0).items()}
    e = {"id": "w1:1-2", "attrs": attrs, "osm_way": 1}
    net = Nw.Network(nodes={}, sections={"w1:1-2": Nw.edge_section(e)}, sec_list=[], chains=[], origin=(0, 0))
    Nw.apply_edge_overrides(net, {"w1:1-2": (e, None, "1", "2")}, [{"id": "ov", "target": {"edge": "w1:1-2"}, "set": set_}])
    return net, net.sections["w1:1-2"]


def test_lane_edges_set_lanes_width_and_strips():
    net, sec = _net({"lane_edges": [0.65, 4.0, 7.4, 10.9]})
    assert sec.lanes == 3 and sec.width == pytest.approx(10.9) and sec.edge_strip == pytest.approx(0.65)
    assert not net.overrides_stale
    # last interval narrower than 2 m = right edge strip, not a lane
    _, sec = _net({"lane_edges": [0.5, 3.7, 7.35, 8.2]})
    assert sec.lanes == 2 and sec.width == pytest.approx(8.2) and sec.lane_edges == [0.5, 3.7, 7.35]
    # explicit width: carriageway beyond the last lane (hatching / island)
    _, sec = _net({"lane_edges": [0.5, 4.2, 7.65], "width": 11.0})
    assert sec.lanes == 2 and sec.width == pytest.approx(11.0)


def test_lane_edges_rejected_on_two_way_or_narrow_lane():
    net, sec = _net({"lane_edges": [0.5, 4.0, 7.5]}, oneway="no", lanes=2)
    assert net.overrides_stale == ["ov"] and sec.lane_edges is None
    net, sec = _net({"lane_edges": [0.5, 2.0, 5.5, 9.0]})
    assert net.overrides_stale == ["ov"] and sec.lane_edges is None


def test_lane_layout_follows_measured_edges_in_travel_direction():
    from roads.markings import edge_lines, lane_layout
    _, sec = _net({"lane_edges": [0.65, 4.0, 7.4, 10.9]})
    hw = sec.width / 2
    _, b, c = lane_layout(sec, hw, 1)           # travel along the chain: left edge = +hw
    assert b == pytest.approx([hw - 4.0, hw - 7.4])
    assert c["fwd"] == pytest.approx([hw - 2.325, hw - 5.7, hw - 9.15])
    _, b2, c2 = lane_layout(sec, hw, -1)        # travel against the chain: mirrored
    assert b2 == pytest.approx([-x for x in b]) and c2["fwd"] == pytest.approx([-x for x in c["fwd"]])
    assert edge_lines(sec, hw, 1) == []         # measured section: only the edge lines the override names
    _, sec = _net({"lane_edges": [0.5, 3.7, 7.35, 8.2], "edge_lines": "both"})
    lats = sorted(lat for lat, kind in edge_lines(sec, 4.1, 1))
    assert lats == pytest.approx([4.1 - 7.35 - 0.12, 4.1 - 0.5 + 0.12])


def test_width_and_offset_profiles_parse():
    _, sec = _net({"width": [[0.0, 3.6], [1.0, 6.5]], "center_offset": [[1.0, 0.2], [0.0, -4.65]]})
    assert sec.width == pytest.approx(6.5) and sec.width_profile == [(0.0, 3.6), (1.0, 6.5)]
    assert sec.center_offset_profile == [(0.0, -4.65), (1.0, 0.2)]
    _, sec = _net({"center_offset": [-1.6, -0.8]})
    assert (sec.center_offset, sec.center_offset_end) == (-1.6, -0.8)


def test_route_avoids_turn_only_lane():
    from roads.route import _through_lane
    _, sec = _net({"lane_edges": [0.7, 4.2, 7.7, 11.05], "turn_lanes": "through|through|right"})
    assert _through_lane(sec) == 1
    _, sec = _net({"lane_edges": [0.7, 4.2, 7.7, 11.05], "turn_lanes": "through|through|through;right"})
    assert _through_lane(sec) is None


def test_authored_line_is_densified_through_its_points():
    from roads.authored_paint import LINES, _densify
    P = np.array([[0.0, 0.0], [10.0, 0.0], [20.0, 5.0]])
    Q = _densify(P)
    assert np.allclose(Q[0], P[0]) and np.allclose(Q[-1], P[-1])
    assert min(np.hypot(*(Q - P[1]).T)) < 1e-6
    assert max(np.hypot(*np.diff(Q, axis=0).T)) <= 1.3
    assert LINES["P-7a"] == (0.24, (1.0, 1.0)) and LINES["P-2b"][1] is None


# ------------------------------------------------------------------------------------------------ built region
@pytest.fixture(scope="module")
def qa():
    if not QA.exists():
        pytest.skip("roads_qa.json not built")
    q = json.loads(QA.read_text(encoding="utf-8"))
    if "authored_paint" not in q["summary"]:
        pytest.fail("old roads_qa.json: rebuild the region (ADR 0095)")
    return q


@pytest.fixture(scope="module")
def overrides():
    return yaml.safe_load((REGION_DIR / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]


def test_no_override_is_stale(qa):
    assert qa["summary"]["overrides_stale"] == []


def test_authored_paint_is_built(qa, overrides):
    want = {o["id"] for o in overrides if o.get("kind") in ("painted_line", "painted_arrow", "painted_crossing")}
    assert want, "ADR 0095 authored paint missing from overrides.yaml"
    built = {r["id"] for r in qa["summary"]["authored_paint"] if r["built"]}
    assert want <= built, sorted(want - built)


def test_measured_sections_have_evidence(overrides):
    n = 0
    for o in overrides:
        st = o.get("set") or {}
        if "lane_edges" in st:
            n += 1
            le = st["lane_edges"]
            assert le == sorted(le) and 2.5 <= le[-1] <= 16.0, o["id"]
            assert o.get("reason") and "xsec/" in o["reason"] and o.get("verify"), o["id"]
    assert n >= 15


def test_andersa_median_stays_open(overrides):
    """REVIEW 0093 P0-L: the median between the Andersa carriageways ran to zero at n10015785253 (both carriageways
    11.5 m centred on OSM ways drawn towards the median). Measured sections: 10.5-11.3 m, centres right of the way."""
    ov = [o for o in overrides if o["id"].startswith(("andersa-nw-xsec", "andersa-se-xsec"))]
    widths = [o["set"].get("width", o["set"]["lane_edges"][-1]) for o in ov]
    widths = [max(v for _, v in w) if isinstance(w, list) else w for w in widths]
    assert len(widths) == 9 and min(widths) >= 10.5
    assert sorted(widths)[-2] <= 11.3 and max(widths) <= 13.5     # only the edge before the fork widens (exit lane)
    for o in ov:      # every carriageway centre lies right of its OSM way (scalar or [[t, m], ...] profile)
        co = o["set"]["center_offset"]
        vals = [v for _, v in co] if isinstance(co, list) else [co]
        assert all(-2.2 <= v <= -0.5 for v in vals), o["id"]
