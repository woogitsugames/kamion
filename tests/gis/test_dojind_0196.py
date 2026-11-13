"""ADR 0196 - plant at Kuronia 2 as a dark hall with low annexes, authored wall gates, run-off streaks that do not
repeat per period, runway paint and the `krywlany_runway` place camera. All of it is opt-in: the reference region C
has none of the overrides, so its output cannot change (asserted on the data and on the no-table code path)."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
sys.path.insert(0, str(REPO / "tools" / "worldgen" / "roads"))

DOJ = REPO / "Data" / "Regions" / "bialystok-dojlidy"
C = REPO / "Data" / "Regions" / "bialystok-industrial-c"
NEW_KINDS = {"wall_gates", "facade_rules", "runway_markings"}
ORIGIN = (780043.0, 590079.0)


def _ov(d):
    return (yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides", [])


def test_region_c_has_no_0196_overrides():
    assert not [o["id"] for o in _ov(C) if o.get("kind") in NEW_KINDS]
    assert not (C / "control_cameras_place.authored.json").exists()


# ------------------------------------------------------------------------------------------------ run-off
def test_runoff_cells_without_table_is_the_old_quad():
    from streetscape import buildings_mesh as BM
    ro = (10.0, 7.3, 0.9)
    cells = BM.runoff_cells(ro, 30.0, 90.0, 2.0, 9.6)
    assert cells == [(30.0, 90.0, 2.0, 9.6, BM.runoff_uv1(ro, 30.0, 90.0, 2.0, 9.6))]
    assert BM.runoff_cells(None, 0.0, 5.0, 0.0, 3.0) == [(0.0, 5.0, 0.0, 3.0, None)]


def test_runoff_blocks_cover_the_wall_and_never_repeat_in_step():
    from streetscape import buildings_mesh as BM
    P = BM.RUNOFF_PERIOD_M
    assert sum(w for _, w in BM.RUNOFF_BLOCKS) == pytest.approx(P)
    bl = BM.runoff_blocks("bdot:some-hall", 400.0)
    assert bl == BM.runoff_blocks("bdot:some-hall", 400.0)                 # deterministic
    assert bl != BM.runoff_blocks("bdot:other-hall", 400.0)
    assert bl[0][0] == 0.0 and bl[-1][1] >= 400.0
    quiet = set(round(q, 2) for q in BM.RUNOFF_QUIET_U)
    for (a0, a1, t0, t1, mul), nxt in zip(bl, bl[1:] + [None]):
        assert a1 - a0 == pytest.approx(abs(t1 - t0)) and 2.2 < a1 - a0 < 6.2   # unit scale: streak widths unchanged
        assert {round(t0 % P, 2), round(t1 % P, 2)} <= quiet               # seams sit on quiet columns of the layer
        assert 0.29 < mul <= BM.RUNOFF_LEN_MUL[1]
        if nxt:
            assert nxt[0] == pytest.approx(a1)
            assert {round(min(t0, t1), 2)} != {round(min(nxt[2], nxt[3]), 2)}   # never the same block twice in a row
    # the old layout showed the same texture column at u and u + 24 m everywhere; now on a small share of the wall only
    def tex(u):
        for a0, a1, t0, t1, _ in bl:
            if a0 <= u < a1:
                return (t0 + (t1 - t0) * (u - a0) / (a1 - a0)) % P
    us = np.arange(0.5, 370.0, 0.5)
    same = np.mean([abs(tex(u) - tex(u + P)) < 0.3 for u in us])
    assert same < 0.2, same
    short = np.mean([b[4] < 0.31 for b in bl])
    assert 0.05 < short < 0.4


def test_runoff_cells_with_table_cut_only_the_streak_zone():
    from streetscape import buildings_mesh as BM
    bl = BM.runoff_blocks("k", 100.0)
    ro = (12.0, 0.0, 0.8, bl)
    cells = BM.runoff_cells(ro, 10.0, 40.0, 0.0, 12.0)
    low = [c for c in cells if c[2] == 0.0]
    assert len(low) == 1 and low[0][:2] == (10.0, 40.0)                    # one quad below the layer
    zs = low[0][3]
    assert zs == pytest.approx(12.0 - 4.0 * 0.8 * BM.RUNOFF_LEN_MUL[1] - 0.05)
    assert min(v for _, v in low[0][4]) - 1.0 > 4.0                        # depth beyond the layer: its empty row
    top = [c for c in cells if c[2] != 0.0]
    assert sum(c[1] - c[0] for c in top) == pytest.approx(30.0)
    assert all(c[2] == pytest.approx(zs) and c[3] == 12.0 for c in top)
    for c0, c1, _, _, uv1 in top:
        assert abs(uv1[1][0] - uv1[0][0]) == pytest.approx(c1 - c0)        # metres stay metres
        assert uv1[2][1] == pytest.approx(1.0) and 0.0 <= min(u for u, _ in uv1) and max(u for u, _ in uv1) < 30.0
        assert max(v for _, v in uv1) < 48.0                               # below the sill-mode threshold of the shader


def test_quiet_columns_match_the_layer_texture():
    png = REPO / "art-source" / "world" / "materials" / "parapet_runoff" / "High" / "T_parapet_runoff.png"
    if not png.exists():
        pytest.skip("generated texture not present (art-source/world/materials/_src/build_all.py)")
    Image = pytest.importorskip("PIL.Image")
    from streetscape import buildings_mesh as BM
    a = np.asarray(Image.open(png).convert("RGB"), float) / 255.0
    H, W, _ = a.shape
    rows = np.arange(H) * 4.0 / H
    col = a[rows > 0.45, :, 0].mean(0) + a[rows > 0.45, :, 1].mean(0)
    for q in BM.RUNOFF_QUIET_U_ALL:
        i0, i1 = int((q - 0.25) / 24.0 * W), int((q + 0.25) / 24.0 * W)
        assert col[i0:i1 + 1].max() <= 0.01, q                    # streak columns reach 0.23
    assert col.mean() > 0.012


# ------------------------------------------------------------------------------------------------ gates
def _hall(pid="bdot:h", ovr=None):
    from shapely.geometry import Polygon
    return {"id": pid, "poly": Polygon([(0, 0), (60, 0), (60, 20), (0, 20)]), "props": {"function": "produkcyjny",
            "height_m": 12.0}, "ovr": ovr or {}, "typ": "hall"}


def test_wall_gate_snaps_to_the_nearest_hall_wall():
    from streetscape import buildings_mesh as BM
    h = _hall()
    BM.wall_gates([h], [{"id": "g", "kind": "wall_gates", "gates": [{"at_en": [20.0, -1.0], "width_m": 4.5, "height_m": 5.0}]}])
    assert len(h["gates"]) == 1
    ops = [(18.0, 19.0, 3.0, 4.0, 0.12, "window", "x"), (40.0, 41.0, 3.0, 4.0, 0.12, "window", "x")]
    BM.gate_openings(h["gates"], np.array([0.0, 0.0]), np.array([1.0, 0.0]), 60.0, 100.0, 112.0, ops)
    gate = [o for o in ops if o[5] == "gate"]
    assert gate == [(17.75, 22.25, 100.02, 105.0, 0.2, "gate", "dock_door")]
    assert [o[0] for o in ops if o[5] == "window"] == [40.0]              # the rule window under the gate is gone
    assert h["gates"][0]["done"]
    # the far wall does not take it
    h2 = _hall()
    BM.wall_gates([h2], [{"id": "g", "kind": "wall_gates", "gates": [{"at_en": [20.0, -1.0]}]}])
    ops2 = []
    BM.gate_openings(h2["gates"], np.array([60.0, 20.0]), np.array([-1.0, 0.0]), 60.0, 100.0, 112.0, ops2)
    assert not ops2 and not h2["gates"][0].get("done")


def test_wall_gate_without_a_wall_is_an_error():
    from streetscape import buildings_mesh as BM
    with pytest.raises(ValueError, match="no hall wall"):
        BM.wall_gates([_hall()], [{"id": "g", "kind": "wall_gates", "gates": [{"at_en": [20.0, -9.0]}]}])
    BM.wall_gates([_hall()], [])                                           # no override: nothing


# ------------------------------------------------------------------------------------------------ runway
class _Buf:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, src=None, UV1=None):
        self.parts.append((layer, mat, np.asarray(V, float), np.asarray(T), src, UV1))


def test_runway_paint_lies_on_the_runway_and_faces_up():
    from shapely.geometry import Point, Polygon
    from roads import standards as S
    from streetscape import runway_paint as RWP
    ov = _ov(DOJ)
    rw = next(o for o in ov if o["id"] == "krywlany-runway-09r-27l")
    asphalt = Polygon(np.asarray(rw["polygon_epsg2180"], float) - ORIGIN)
    buf, rep = _Buf(), {}
    RWP.build(buf, ov, lambda e, n: np.full(len(e), 150.0), rep)
    r = rep["runway_markings"][0]
    assert r["id"] == "krywlany-runway-paint" and 915.0 < r["length_m"] < 925.0
    tris = sum(len(p[3]) for p in buf.parts)
    assert tris == r["triangles"] and 1500 < tris < 4000
    area = 0.0
    for layer, mat, V, T, src, uv1 in buf.parts:
        assert layer == "markings" and mat == "marking_white" and src.startswith("runway:") and uv1 is not None
        assert np.allclose(V[:, 2], 150.0 + S.MARKING_LIFT)
        A = V[T]
        a2 = (A[:, 1, 0] - A[:, 0, 0]) * (A[:, 2, 1] - A[:, 0, 1]) - (A[:, 2, 0] - A[:, 0, 0]) * (A[:, 1, 1] - A[:, 0, 1])
        assert (a2 > 0).all(), src                                         # CCW seen from above
        area += 0.5 * a2.sum()
        assert all(asphalt.buffer(0.3).contains(Point(*q[:2])) for q in V), src
    # two side stripes 918 x 0.9 m carry most of the paint
    assert 2 * 917 * 0.9 < area < 2 * 918 * 0.9 + 700.0
    buf2, rep2 = _Buf(), {}
    RWP.build(buf2, _ov(C), lambda e, n: np.zeros(len(e)), rep2)
    assert not buf2.parts and not rep2


# ------------------------------------------------------------------------------------------------ data
def test_kuronia2_is_a_dark_hall_with_low_light_annexes():
    from streetscape import buildings_mesh as BM
    from streetscape import frontage as FR
    from streetscape import materials as MT
    fc = json.loads((DOJ / "buildings.geojson").read_text(encoding="utf-8"))
    ov = _ov(DOJ)
    assert "kuronia2-hall-dark-band" not in {o["id"] for o in ov}
    blds = {b["id"]: b for b in BM.load(fc, ORIGIN, ov)}
    host = blds["bdot:941cfc23-bd8b-40d5-a49b-d1bba751d5bd"]
    assert host["typ"] == "hall" and host["ovr"]["wall_material"] == "hall_wall_graphite"
    assert host["props"]["height_m"] == pytest.approx(12.72)
    parts = {k: b for k, b in blds.items() if k.startswith("override:kuronia2-")}
    assert len(parts) == 5
    for k in ("override:kuronia2-corner-portal", "override:kuronia2-front-portal"):
        assert parts[k]["typ"] == "hall" and parts[k]["ovr"]["wall_material"] == "hall_wall_graphite"
        assert 7.2 < parts[k]["props"]["height_m"] < host["props"]["height_m"]
    for k in ("override:kuronia2-front-bay", "override:kuronia2-office-wing", "override:kuronia2-street-annex"):
        assert parts[k]["typ"] == "office" and parts[k]["props"]["height_m"] == pytest.approx(7.2)
        assert FR.plan(parts[k]["ovr"]["frontage"], MT.M)["wall"] == "plaster_white"
    polys = [host["poly"]] + [b["poly"] for b in parts.values()]
    for i, p in enumerate(polys):
        for q in polys[i + 1:]:
            assert p.intersection(q).area < 0.5
    assert sum(p.area for p in polys) == pytest.approx(11214.5, abs=40.0)   # BDOT10k outline, parts 0.3 m proud
    assert not [k for k in blds if k.startswith("bdot:941cfc23") and "#cut" in k]   # the host stays one piece
    rosti = blds["bdot:2BE4B431-BC59-1BF0-E053-CC2BA8C0D140"]
    assert len(rosti["gates"]) == 2 and all(b.get("runoff_shuffle") for b in blds.values())
    for o in ov:
        if o["id"].startswith("kuronia2-") or o.get("kind") in NEW_KINDS:
            assert o.get("reason") and o.get("confidence") and o.get("verify"), o["id"]
            assert "ravilor" not in json.dumps(o) and "osti " not in o["reason"]   # no brands in the data


def test_runway_camera_is_authored_and_stands_at_the_fence():
    cams = json.loads((DOJ / "control_cameras_place.authored.json").read_text(encoding="utf-8"))["cameras"]
    c = next(c for c in cams if c["id"] == "krywlany_runway")
    assert c["eye_m"] == 1.7
    from shapely.geometry import LineString, Point
    fence = LineString([(188.7, -146.6), (212.8, -196.9)])                 # OSM barrier=fence (metal) of the aerodrome
    assert fence.distance(Point(*c["pos_en"])) < 1.5
    gen = DOJ / "generated" / "control_cameras.json"
    g = {x["id"]: x for x in json.loads(gen.read_text(encoding="utf-8"))["cameras"]}
    if "krywlany_runway" not in g:
        pytest.skip("generated/control_cameras.json older than ADR 0196 (build_world not run)")
    k = g["krywlany_runway"]
    d = np.array(k["look_at"][:2]) - np.array(k["pos"][:2])
    assert d[0] < -90.0 and abs(d[1]) < 5.0                                # looks west along the runway axis
    assert k["fov_deg"] == 12.0 and k["look_at"][2] < k["pos"][2]
