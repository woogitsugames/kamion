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
    solid = [p for p in buf.parts if p.mat != "hedge_sprig_berberis"]
    V = np.vstack([p.V for p in solid])
    assert PT.HEDGE_H[0] - 0.1 <= V[:, 2].max() <= PT.HEDGE_H[1] + 0.2
    assert V[:, 2].min() < 0.0                                   # foot tucked into the ground
    assert {p.mat for p in buf.parts} == {"hedge_berberis", "hedge_shell_berberis", "hedge_sprig_berberis"}


def test_hedge_reads_as_plants_not_a_box():
    """ADR 0049 addendum: alpha shell outside a darker core, open foot, lumpy top, loose shoots above the top."""
    from shapely.geometry import Polygon
    from roads.meshing import MeshBuf
    from streetscape import plantings as PT
    buf = MeshBuf()
    poly = Polygon([(0, 0), (12, 0), (12, 1.6), (0, 1.6)])
    st = {}
    PT.hedge_mass(buf, poly, lambda e, n: np.zeros(len(np.atleast_1d(e))), ("box",), h=0.7, stats=st)
    core = np.vstack([p.V for p in buf.parts if p.mat == "hedge_berberis"])
    shell = np.vstack([p.V for p in buf.parts if p.mat == "hedge_shell_berberis"])
    sprig = np.vstack([p.V for p in buf.parts if p.mat == "hedge_sprig_berberis"])
    assert shell[:, 2].min() > 0.04                              # shell open at the foot: dark core / stems
    assert core[:, 2].max() < shell[:, 2].max() - 0.03           # core inside the leaf shell
    assert sprig[:, 2].max() > shell[:, 2].max() + 0.03          # shoots break the top silhouette
    top = shell[shell[:, 2] > 0.5]
    assert np.std(top[:, 2]) > 0.02                              # lumpy, not a flat slab
    # ADR 0060 (review r7 N-4): clipped berberis = a straight cut face, no "sausage" lumps along it
    ring = shell[(np.abs(shell[:, 1] - 0.8) > 0.7) & (np.abs(shell[:, 2] - 0.3 * 0.7) < 0.02)
                 & (shell[:, 0] > 1.0) & (shell[:, 0] < 11.0)]
    assert len(ring) > 20 and np.ptp(np.abs(ring[:, 1] - 0.8)) < 0.05
    assert 500 < st["tris"] < 6000                               # 12 m hedge: budget per metre ~40-500 tris


def test_osm_hedge_gaps_at_gates_and_species():
    from roads.meshing import MeshBuf
    from streetscape import plantings as PT
    buf = MeshBuf()
    src = {"osm": {"ways": [{"osm_way": 1, "part": 0, "tags": {"barrier": "hedge", "species": "Thuja occidentalis"},
                             "geometry": {"coordinates": [[0, 0], [30, 0]]}}],
                   "nodes": [{"tags": {"barrier": "gate"}, "geometry": {"coordinates": [10, 0]}},
                             {"tags": {"barrier": "sliding_gate"}, "geometry": {"coordinates": [20, 0.3]}}]}}
    rep = {}
    PT.osm_hedges(buf, src, (0.0, 0.0), None, lambda e, n: np.zeros(len(np.atleast_1d(e))), rep)
    r = rep["osm_hedges"]
    assert r["gaps"] == 2 and r["hedges"] == 3
    assert abs(r["m"] - (30 - 1.2 - 4.0)) < 0.2
    assert {p.mat for p in buf.parts} == {"hedge_thuja", "hedge_shell_thuja", "hedge_sprig_thuja"}
    V = np.vstack([p.V for p in buf.parts if p.mat == "hedge_shell_thuja"])
    assert not np.any((np.abs(V[:, 0] - 10) < 0.3)) and not np.any(np.abs(V[:, 0] - 20) < 1.5)   # open gates
    assert 1.4 < V[:, 2].max() < 2.6
    assert PT._hedge_species({"genus": "Ligustrum"}) == "privet" and PT._hedge_species({}) == "privet"


def test_hedge_textures_alpha_coverage():
    from streetscape import hedge_textures as HT
    tx = HT.textures()
    for sp in HT.SPECIES:
        assert 0.5 < HT.coverage(tx[f"hedge_shell_{sp}"]) < 0.92      # holes: the dark core shows through
        a = np.asarray(tx[f"hedge_sprig_{sp}"])[..., 3]
        assert 0.15 < (a > 127).mean() < 0.7
        assert a[:2].max() == 0 and a[:, :2].max() == 0 and a[:, -2:].max() == 0   # no straight clip edges


# ------------------------------------------------------------------------------------------ outputs
def test_marking_paint_material():
    m = _manifest()["marking_white"]
    assert m["texture_set"] == "asphalt_worn" and isinstance(m.get("paint"), dict)
    assert 0.55 <= max(m["color"][:3]) <= 0.65                   # film albedo 0.55-0.65 (r6 W-H6)
    # under the traffic film the mean effective albedo stays in EN 1436 white B2..B3 (0.30-0.40); the display caps
    # are relative since D37 (docs/11, ADR 0060): paint / asphalt 1.7-2.3 in sun, <= 235 sRGB in sun, <= 217 overcast
    # (measured on renders by scripts/paint-contrast.py, not here)
    eff = max(m["color"][:3]) * (1.0 - m["paint"]["dirt"])
    assert 0.30 <= eff <= 0.40


def test_asphalt_albedo_matches_set_and_contrast():
    """ADR 0049 addendum r7: aged AC 0.08 (paint/asphalt contrast >= ~1.8 display); the manifest colour equals the
    asphalt_worn set mean (engine tint ~1) so the paint shader's untinted base under worn marks matches the road."""
    spec = json.loads((REGION_DIR.parents[2] / "art-source" / "world" / "materials" / "materials_spec.json")
                      .read_text(encoding="utf-8"))
    target = spec["sets"]["asphalt_worn"]["albedo_target_mean_lum_linear"]
    mats = _manifest()
    for k in ("road_asphalt", "yard_asphalt", "path_asphalt"):
        c = mats[k]["color"]
        lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
        assert abs(lum / target - 1.0) < 0.03, (k, lum, target)
    assert 0.07 <= target <= 0.12                                  # aged AC (arXiv:2409.12242: new 0.05 -> aged 0.15)
    paint = mats["marking_white"]
    assert max(paint["color"][:3]) * (1.0 - paint["paint"]["dirt"]) / target >= 4.0   # nominal linear ratio


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
