"""Review r6 streetscape fixes (ADR 0049): worn road paint data, dock tyre-scrub shapes, Bieżeństwa plantings,
transparent noise screens, poles never above the terrain collider.

Unit tests run without raw data; output tests read the generated files of the last build_world.py run."""

from __future__ import annotations

import json

import numpy as np
import pytest

from conftest import REGION_DIR


def _manifest():
    p = REGION_DIR / "generated" / "world_manifest.json"
    if not p.exists():
        pytest.skip("world_manifest.json missing: run roads/build_world.py")
    m = json.loads(p.read_text(encoding="utf-8"))
    return m.get("materials", m)


def _qa():
    p = REGION_DIR / "generated" / "streetscape_qa.json"
    if not p.exists():
        pytest.skip("streetscape_qa.json missing: run roads/build_world.py")
    return json.loads(p.read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------ units
def test_paint_uv1_lane_coordinate_and_exposure():
    """TEXCOORD_1 of the paint: x = lane coordinate on the carriageway convention, y = exposure + age."""
    from roads import markings as MK

    class Sec:
        lane_w, edge_strip, oneway, roundabout = 3.5, 0.0, False, False

    class Chain:
        id = "c:test"
        def section(self, s, secs):
            return Sec()
        def hw_at(self, s):
            return np.full(np.shape(s), 7.0)

    MK._SECS[:] = [Sec()]
    try:
        uv = MK._paint_uv1(Chain(), [10.0, 10.0], [-1.75, 5.25], "P-14")
        assert np.allclose(uv[:, 0], [0.5, 1.5])                 # |lat| / lane width, two-way road
        assert np.all((uv[:, 1] >= 2.0) & (uv[:, 1] < 3.0))      # transverse
        uv = MK._paint_uv1(Chain(), [10.0, 12.0], [0.0, 0.0], "lane")
        assert np.all((uv[:, 1] >= 0.0) & (uv[:, 1] < 1.0))      # longitudinal
        uv2 = MK._paint_uv1(Chain(), [10.0, 12.0], [0.0, 0.0], "lane")
        assert np.array_equal(uv, uv2)                           # deterministic age
    finally:
        MK._SECS.clear()


def test_tyre_scrub_neighbours_never_share_a_shape():
    from roads.meshing import MeshBuf
    from streetscape import life as LF
    docks = []
    for r in range(6):
        docks.append({"id": f"row{r}", "edge": [[0.0, 100.0 * r], [60.0, 100.0 * r]],
                      "docks": [{"u": 3.0 + 3.6 * k, "num": k + 1} for k in range(15)]})
    buf = MeshBuf()
    rep = {}
    LF.tyre_scrub(buf, docks, lambda e, n: np.zeros(len(e)), rep)
    shapes = rep["tyre_scrub_shapes"]
    assert len(shapes) >= 4 and 0.12 <= shapes.get("none", 0) / sum(shapes.values()) <= 0.40
    by_dock = {}
    for p in buf.parts:
        _, row, num, k, shape = p.src.split(":")
        by_dock[(row, int(num))] = shape
        s = float(p.UV1[0, 1])
        assert LF.TYRE_STRENGTH[0] <= s <= LF.TYRE_STRENGTH[1]
    for r in range(6):
        seq = [by_dock.get((f"row{r}", k + 1), "none") for k in range(15)]
        assert all(a != b for a, b in zip(seq, seq[1:])), seq


def test_hedge_mass_is_closed_and_tall_enough():
    from shapely.geometry import Polygon
    from roads.meshing import MeshBuf
    from streetscape import plantings as PT
    buf = MeshBuf()
    poly = Polygon([(0, 0), (8, 0), (9, 2), (7, 3.5), (1, 3), (-0.5, 1.5)]).buffer(0.3)
    assert PT.hedge_mass(buf, poly, lambda e, n: np.zeros(len(np.atleast_1d(e))), ("t",)) == 1
    V = np.vstack([p.V for p in buf.parts])
    assert PT.HEDGE_H[0] - 0.1 <= V[:, 2].max() <= PT.HEDGE_H[1] + 0.15
    assert V[:, 2].min() < 0.0                                   # foot tucked into the ground
    assert all(p.mat == "hedge_berberis" for p in buf.parts)


# ------------------------------------------------------------------------------------------ outputs
def test_marking_paint_material():
    m = _manifest()["marking_white"]
    assert m["texture_set"] == "asphalt_worn" and isinstance(m.get("paint"), dict)
    assert 0.55 <= max(m["color"][:3]) <= 0.65                   # film albedo 0.55-0.65 (r6 W-H6)


def test_noise_screen_is_glass_with_dust():
    m = _manifest()["noise_glass"]
    assert m.get("blend") and m.get("shader") == "car_glass" and m.get("dust", 0) > 0
    assert max(m["color"]) < 0.1 and m["alpha"] <= 0.2           # clear sheet, no mint slab


def test_biezenstwa_plantings_applied():
    pl = _qa().get("plantings")
    assert pl, "plantings report missing"
    assert not pl["stale"], pl["stale"]
    assert pl["hedges"] >= 4 and pl["hedge_m2"] > 40.0
    fills = {i["fill"] for i in pl["islands"]}
    assert fills == {"paving", "soil"} and pl["shrubs"] >= 3
