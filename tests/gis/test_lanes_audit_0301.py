"""ADR 0301: lane widths and lane layout on the start route (DK8 Maczka / Kleeberga, Białystok) against the GUGiK
orthophoto 0.08 m (tools/worldgen/qa/lane_width_audit.py, ortho_lane_fit.py, measured 2026-11-19).

Real cross-sections used below (route stations, frame = left of travel from the route point / OSM way):
  * Maczka eastbound, 3 lanes, way 249740773: asphalt -7.35 ... +4.50 m, paint lines -6.90 | -3.35 | +0.30 | +3.90
    (edge lines 10.8 m apart, lanes 3.55 / 3.65 / 3.60 m); BDOT10k 10.5 m.
  * Maczka, 2 lanes, way 257358866: lines -2.15 | +1.60 | +5.65 (3.75 / 4.05 m); BDOT10k 7.0 m.
  * Kleeberga, 2 lanes, way 249740778: lines -2.80 | +0.85 | +4.65 (3.65 / 3.80 m), hatched median beyond; BDOT 7.5 m."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "Data" / "Regions"
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
sys.path.insert(0, str(ROOT / "tools" / "worldgen" / "qa"))


def _edge(tags):
    attrs = {k: {"v": v, "src": "bdot10k" if k == "width" else "osm", "conf": "high"} for k, v in tags.items()}
    attrs.setdefault("oneway", {"v": "no", "src": "osm", "conf": "high"})
    return {"id": "x", "attrs": attrs}


@pytest.mark.parametrize("tags,lane_w", [
    # BDOT under-reads multi-lane trunk carriageways: never below the class standard (PTB2022 § 17 ust. 1 pkt 3)
    ({"highway": "trunk", "oneway": "yes", "lanes": "3", "width": 10.5}, 3.50),
    ({"highway": "trunk", "oneway": "yes", "lanes": "2", "width": 7.0}, 3.50),
    ({"highway": "trunk", "oneway": "yes", "lanes": "2", "width": 7.5}, 3.50),
    # ... and may widen it up to the widest value (GP: std + 0.25, WORKING_VALUE)
    ({"highway": "trunk", "oneway": "yes", "lanes": "2", "width": 10.0}, 3.75),
    # two-way class G with BDOT 6.0 m (Szosa Knyszyńska): 3.00 m lanes as painted, floor unchanged
    ({"highway": "secondary", "lanes": "2", "width": 6.0}, 3.00),
    # Z / L: § 17 ust. 1 pkt 5-6 allow up to 3.50 m (was capped at std + 0.25)
    ({"highway": "tertiary", "lanes": "2", "width": 7.0}, 3.50),
    ({"highway": "residential", "lanes": "2", "width": 6.6}, 3.30),
    # Z / L floor unchanged (no measurement): the difficult-conditions value
    ({"highway": "residential", "lanes": "2", "width": 4.8}, 2.50),
])
def test_bdot_lane_width_rule(tags, lane_w):
    from roads.network import edge_section
    sec = edge_section(_edge(tags))
    assert sec.lane_w == pytest.approx(lane_w, abs=1e-3)
    assert sec.lane_w <= 3.75 + 1e-9


def test_standards_follow_ptb2022_17_1():
    from roads import standards as S
    for cls, (std, diff) in S.LANE_WIDTH.items():
        for ow in (True, False):
            assert diff <= S.bdot_lane_floor(cls, ow) <= std
        assert S.LANE_WIDTH_MAX[cls] >= std
    assert S.bdot_lane_floor("G", False) == 3.00          # two-way G: BDOT right (Szosa Knyszyńska, edge lines 6.3-6.5 m)
    assert S.LANE_WIDTH_MAX["Z"] == S.LANE_WIDTH_MAX["L"] == S.LANE_WIDTH_MAX["D"] == 3.50   # "dopuszcza się ... 3,50"
    assert S.LANE_WIDTH_MAX["S"] == 3.75


@pytest.mark.parametrize("asph,lines,lanes,flags", [
    ((-7.35, 4.50), [-6.90, -3.35, 0.30, 3.90], 3, [True, True]),          # Maczka 3 lanes, both edge lines
    ((-2.75, 5.80), [-2.15, 1.60, 5.65], 2, [True, True]),                 # Maczka 2 lanes
    ((-3.40, 12.0), [-2.80, 0.85, 4.65], 2, [True, True]),                 # Kleeberga, hatched median: its border line
    ((-5.00, 5.95), [-1.75, 1.75, 5.35], 3, [False, True]),                # lane to the kerb, no right edge line
])
def test_station_layout_real_profiles(asph, lines, lanes, flags):
    import ortho_lane_fit as F
    lay = F.station_layout(asph, lines)
    assert lay is not None
    assert len(lay["b"]) - 1 == lanes
    assert lay["flags"] == flags
    for a, b in zip(lay["b"], lay["b"][1:]):
        assert 2.6 <= b - a <= 4.4


def test_station_layout_rejects_missed_line():
    import ortho_lane_fit as F
    # a 5 m gap between the last line and the kerb = a missed lane line, not a lane: no guess
    assert F.station_layout((-7.0, 4.0), [-1.0, 2.6]) is None or len(F.station_layout((-7.0, 4.0), [-1.0, 2.6])["b"]) < 3


def test_generated_lane_overrides_loaded_before_authored():
    from roads import pipeline
    assert "overrides.ortho_lanes.json" in pipeline.GENERATED_OVERRIDES
    ov = pipeline.load_overrides("bialystok-maczka")
    ids = [o.get("id", "") for o in ov]
    gen = [i for i, x in enumerate(ids) if x.startswith("ortho-lanes-")]
    auth = [i for i, x in enumerate(ids) if not x.startswith("ortho-lanes-")]
    assert gen, "bialystok-maczka/overrides.ortho_lanes.json missing (qa/ortho_lane_fit.py)"
    assert max(gen) < min(auth)


@pytest.mark.parametrize("region,edge", [
    ("bialystok-maczka", "w249740773:2563060452-2357583396"),
    ("bialystok-maczka", "w257357743:2629158252-2357583392"),
])
def test_maczka_three_lanes_as_painted(region, edge, measured_widths):
    """The 3-lane DK8 carriageway is built with the painted lanes (3.4-4.0 m each; a lane to the kerb includes the gutter) and its centre
    1.0-2.2 m right of the OSM way (the way is drawn along the lane lines, toward the median)."""
    from roads import pipeline
    net = pipeline.build_network(region)[0]
    sec = net.sections[edge]
    assert sec.lane_edges, sec.width_src
    widths = [b - a for a, b in zip(sec.lane_edges, sec.lane_edges[1:])]
    assert len(widths) == 3
    assert all(3.4 <= w <= 4.0 for w in widths), widths   # lane to the kerb (no edge line) includes the gutter
    assert -2.2 <= sec.center_offset <= -1.0
    assert sec.edge_lines in ("both", "left")       # P-7 at the median; the right lane may run to the kerb


def test_fit_file_is_reproducible_schema():
    for f in sorted(REG.glob("*/overrides.ortho_lanes.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        assert d["schema"] == "truck-sim-pl/overrides/1"
        for o in d["overrides"]:
            le = o["set"]["lane_edges"]
            assert le == sorted(le) and le[0] >= 0
            assert all(2.6 <= b - a <= 4.4 for a, b in zip(le, le[1:]))
            assert o["set"]["width"] >= le[-1] - 1e-6
