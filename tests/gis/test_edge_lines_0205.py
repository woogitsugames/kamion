"""ADR 0205: edge lines on a road below class GP only by authored override (rural G road, dk65-01)."""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "worldgen"))

from roads import standards as S  # noqa: E402
from roads.markings import edge_line_width, edge_lines  # noqa: E402


def _sec(cls, el=None, strip=0.0, lane_edges=None, oneway=False):
    return SimpleNamespace(roundabout=False, edge_lines=el, lane_edges=lane_edges, oneway=oneway, cls=cls,
                           edge_strip=strip, width=6.0)


def test_class_g_has_no_edge_lines_by_default():
    assert edge_lines(_sec("G"), 3.0, 1) == []
    assert edge_lines(_sec("G", "none"), 3.0, 1) == []


def test_class_g_override_paints_narrow_lines_inside_the_edge():
    out = edge_lines(_sec("G", "both"), 3.0, 1)
    assert sorted(lat for lat, _ in out) == pytest.approx([-(3.0 - S.EDGE_LINE_INSET_MINOR), 3.0 - S.EDGE_LINE_INSET_MINOR])
    assert {k for _, k in out} == {"P-7b"}
    assert [lat for lat, _ in edge_lines(_sec("G", "right"), 3.0, 1)] == pytest.approx([-(3.0 - S.EDGE_LINE_INSET_MINOR)])
    assert edge_line_width(_sec("G", "both")) == S.LINE_W_NARROW


def test_class_gp_rule_unchanged():
    out = edge_lines(_sec("GP", None, strip=0.5), 4.0, 1)
    assert sorted(lat for lat, _ in out) == pytest.approx([-(4.0 - 0.5 + S.LINE_W_WIDE / 2), 4.0 - 0.5 + S.LINE_W_WIDE / 2])
    assert edge_line_width(_sec("GP", None, strip=0.5)) == S.LINE_W_WIDE


def test_dk65_01_route_edges_carry_the_override():
    import yaml
    ov = yaml.safe_load((Path(__file__).resolve().parents[2] / "Data/Regions/dk65-01/overrides.yaml").read_text(encoding="utf-8"))
    route = [o for o in ov["overrides"] if o.get("set", {}).get("edge_lines") == "both"   # ADR 0220: kind entries have no set
             and not str(o.get("id", "")).startswith("s8-xsec-")]                    # ADR 0288: S8 corner, not the route
    assert len(route) == 5 and route[0]["set"]["width"] == 6.0
