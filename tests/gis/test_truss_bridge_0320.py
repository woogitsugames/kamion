"""ADR 0320: truss_bridge rule (Narew bridge, Tykocin) and the Tykocin square objects - geometry contract, not looks."""
import json
from pathlib import Path

import numpy as np
import yaml

from streetscape import monument_kit as MK
from streetscape import truss_bridge as TB
from streetscape import tykocin_rynek_0320 as TY
from streetscape.buildings_mesh import Acc

ROOT = Path(__file__).resolve().parents[2]
REGION = ROOT / "Data/Regions/tykocin"


class Buffer:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, vertices, uv, triangles, src="", UV1=None, footprint=False):
        self.parts.append((layer, mat, np.asarray(vertices, float), np.asarray(triangles), src))


class FakeDeck:
    """Straight level deck running north: half width 4.5 m to the cap edge, cap top 0.2 m above the axis."""
    L = 60.0

    def at(self, x):
        c = np.array([0.0, x, 10.0])
        return {"t": np.array([0.0, 1.0, 0.0]), "n": np.array([-1.0, 0.0, 0.0]), "c": c, "hw": 4.5,
                "l": c + [-4.5, 0, 0.2], "r": c + [4.5, 0, 0.2]}

    def edge(self, x, sgn, out=0.0, dz=0.0):
        st = self.at(x)
        p = (st["l"] if sgn > 0 else st["r"]).copy()
        p[:2] += st["n"][:2] * sgn * out
        p[2] += dz
        return p


def _checked(acc):
    buf = Buffer()
    acc.flush(buf, "t")
    for layer, mat, v, t, _ in buf.parts:
        assert np.isfinite(v).all() and t.min() >= 0 and t.max() < len(v)
        area = np.linalg.norm(np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]]), axis=1)
        assert (area > 1e-9).all(), (layer, mat)
    return buf


def _volume(v, t):
    return float(np.einsum("ij,ij->i", v[t[:, 0]], np.cross(v[t[:, 1]], v[t[:, 2]])).sum() / 6.0)


def test_override_spans_follow_the_orthophoto_and_fill_the_osm_length():
    ovs = yaml.safe_load((REGION / "overrides.yaml").read_text(encoding="utf8"))["overrides"]
    o = next(x for x in ovs if x.get("kind") == TB.KIND)
    assert o["target"] == {"osm_way": [96942026]} and o["first_span_at"] == "south"
    lengths = [s["length_m"] for s in o["spans"]]
    assert abs(sum(lengths) - 194.8) < 1.0                       # OSM way w96942026: 194.8 m
    assert [bool(s.get("truss", True)) for s in o["spans"]] == [False, True, True, True, True, False]
    spans, k = TB.span_layout(o, 194.4)
    assert abs(k - 1.0) < 0.01 and abs(spans[-1][1] - 194.4) < 1e-6
    assert spans[1][3] == 12 and all(s[3] == 9 for s in spans[2:5])
    assert 7.0 < spans[1][4] < 8.5                               # main span rise about 1 : 6.5


def test_member_and_strip_are_closed_outward():
    acc = Acc()
    TB._member(acc, "buildings", "m", [0, 0, 0], [0, 3, 4], [1, 0, 0], 0.3, 0.4, skip=())
    part = _checked(acc).parts[0]
    assert np.isclose(_volume(part[2], part[3]), 0.3 * 0.4 * 5.0)
    for side in ([1.0, 0, 0], [-1.0, 0, 0]):
        acc = Acc()
        nodes = np.array([[0, 0, 0], [0, 4, 1], [0, 8, 1.5]], float)
        TB._strip(acc, "buildings", "m", nodes, np.array(side), 0.5, 0.2)
        buf = _checked(acc)
        v, t = buf.parts[0][2], buf.parts[0][3]
        n = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
        cen = v[t].mean(axis=1) - [0, 0, 0]
        axis_pt = np.column_stack([np.zeros(len(cen)), cen[:, 1], np.interp(cen[:, 1], nodes[:, 1], nodes[:, 2])])
        assert (np.einsum("ij,ij->i", n, cen - axis_pt) > 0).all()      # every face looks away from the axis


def test_truss_span_geometry_headroom_and_lods():
    prm, dk = dict(TB.DEFAULTS), FakeDeck()
    acc = Acc()
    tops = {}
    for sgn in (1.0, -1.0):
        top, bot, xs, dzt = TB._truss(acc, dk, 4.0, 55.0, 12, 7.8, sgn, prm, (True, True))
        tops[sgn] = top
        assert len(top) == 13 and np.isclose(top[6][2] - top[0][2], 7.8)
        assert np.allclose(np.abs(top[:, 0]), 4.5 + prm["truss_out_m"])        # stands outside the cap edge
        assert np.isclose(bot[:, 2].max() + prm["bottom_d_m"] / 2, 10.2 + prm["bottom_top_m"])
    braced = TB._bracing(acc, dk, tops[1.0], tops[-1.0], xs, dzt, prm)
    assert braced and braced == sorted(braced) and braced[0] >= 2 and braced[-1] <= 10
    for k in braced:      # nothing of the bracing below the headroom over the carriageway
        assert tops[1.0][k][2] - dzt[k] - prm["strut_d_m"] - 10.0 >= prm["headroom_m"]
    buf = _checked(acc)
    tris = {}
    for layer, mat, v, t, _ in buf.parts:
        tris[layer] = tris.get(layer, 0) + len(t)
        if mat == TB.STEEL and layer == "buildings":
            inner = v[(np.abs(v[:, 0]) < 4.0) & (v[:, 1] > 6.0) & (v[:, 1] < 53.0)]
            assert inner[:, 2].min() - 10.0 >= prm["headroom_m"] - 1.3          # knee braces only, above a truck cab
    assert tris["buildings_low"] < 0.35 * tris["buildings"]
    assert {m for layer, m, *_ in buf.parts} == {TB.STEEL, TB.BOARD}


def test_footway_and_pier_are_valid_and_pier_reaches_the_ground():
    prm, dk = dict(TB.DEFAULTS), FakeDeck()
    acc, buf = Acc(), Buffer()
    spans = [(0.0, 60.0, True, 12, 7.8)]
    for sgn in (1.0, -1.0):
        TB._footway(acc, dk, sgn, prm, spans)
    pier = TB._pier(acc, buf, dk, 30.0, prm, lambda e, n: 4.0, 1.0, "truss:t")
    out = _checked(acc)
    assert pier["kind"] == "pier" and pier["ground"] == 4.0 and pier["top"] < 10.2
    conc = np.concatenate([v for layer, m, v, t, _ in out.parts if m == TB.CONC and layer == "buildings"])
    assert conc[:, 2].min() <= 3.0 + 1e-9                                       # piles go 1 m into the bed
    picket = next(v for layer, m, v, t, _ in out.parts if m == TB.PICKET)
    assert np.abs(picket[:, 0]).min() > 4.5 + prm["footway_w_m"]                # railing at the outer footway edge
    assert len(buf.parts) == 1 and buf.parts[0][0] == "collision"


def test_generated_qa_keeps_limit_signs_and_reports_the_truss():
    qa = json.loads((REGION / "generated/streetscape_qa.json").read_text(encoding="utf8"))
    tb = [x for x in qa.get("truss_bridges", []) if x["status"] == "applied"]
    assert len(tb) == 1 and abs(tb[0]["run_m"] - 194.8) < 1.5 and len(tb[0]["spans"]) == 4
    assert sum(1 for p in tb[0]["piers"] if p["kind"] == "pier") == 5
    assert tb[0]["tris"]["buildings"] <= 30000 and tb[0]["tris"]["buildings_low"] <= 6000
    assert all(p["top"] - p["ground"] > (1.5 if p["kind"] == "pier" else 0.3) for p in tb[0]["piers"])
    placed = qa["furniture"]["limit_signs"]["placed"]                          # ADR 0307 untouched
    assert placed == {"B-18_12": 2, "B-16_3.7": 2}


def test_monument_kit_bodies_are_closed_outward():
    acc = Acc()
    MK.lathe(acc, "buildings", "m", [0, 0, 0], (0.0, 1.0), [(0, 1, 1), (2, 1, 1)], sides=24, bottom=True)
    MK.limb(acc, "buildings", "l", [[5, 0, 0], [5, 0, 2]], [0.5, 0.5], sides=24)
    MK.sphere(acc, "buildings", "s", [9, 0, 0], 1.0, sides=16, stacks=12)
    buf = _checked(acc)
    vol = {m: _volume(v - v.mean(axis=0), t) for _, m, v, t, _ in buf.parts}
    assert 0.95 * 2 * np.pi < vol["m"] < 2 * np.pi and 0.95 * np.pi / 2 < vol["l"] < np.pi / 2
    assert 0.85 * 4 / 3 * np.pi < vol["s"] < 4 / 3 * np.pi
    assert MK.thin(range(5)) == (0, 2, 4) and MK.thin(range(4)) == (0, 2, 3)


def test_tykocin_square_objects():
    assert TY.build(Buffer(), "knyszyn", [0, 0], [], None, {}) is None
    buf, rep = Buffer(), {}
    r = TY.build(buf, "tykocin", [751371.0, 600319.0], [], lambda e, n: np.zeros_like(e) + 104.0, rep)
    assert rep[TY.ASSET_ID] is r and r["status"] == "applied" and len(r["benches"]) == 10
    assert 7.0 <= r["monument"]["height_m"] <= 8.0 and r["tris"]["buildings"] <= 3500
    assert r["tris"]["buildings_low"] <= 0.6 * r["tris"]["buildings"]
    for layer, mat, v, t, src in buf.parts:
        assert np.isfinite(v).all() and src == TY.ASSET_ID
        assert (np.linalg.norm(np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]]), axis=1) > 1e-9).all()
    gilt = next(v for layer, m, v, t, _ in buf.parts if layer == "buildings" and m == TY.GILT)
    # the mace is held out to the figure's right (west when it faces south) above its head
    assert gilt[:, 0].mean() < TY.MONUMENT_EN[0] - 0.6 and gilt[:, 2].max() - 104.0 > r["monument"]["height_m"] - 0.3
    low = {m for layer, m, *_ in buf.parts if layer == "buildings_low"}
    assert not low & {TY.SAND, TY.GILT, TY.IRON, TY.STONE, "bench_wood"}
    r = TY.build(Buffer(), "tykocin", [751371.0, 600319.0], [], lambda e, n: np.full_like(e, np.nan), {})
    assert r["status"] == "skipped" and r["monument"] is None


def test_square_paving_overrides_are_valid_polygons_around_the_monument():
    from shapely.geometry import Point, Polygon
    ovs = yaml.safe_load((REGION / "overrides.yaml").read_text(encoding="utf8"))["overrides"]
    areas = {o["id"]: o for o in ovs if o.get("kind") == "paved_area"}
    assert set(areas) == {"tykocin-rynek-plaza-0320", "tykocin-rynek-walk-east-0320", "tykocin-rynek-walk-west-0320"}
    origin = np.array([751371.0, 600319.0])
    polys = {}
    for k, o in areas.items():
        outer = Polygon(np.asarray(o["polygon_epsg2180"]) - origin)
        holes = [Polygon(np.asarray(h) - origin) for h in o.get("holes_epsg2180", [])]
        assert outer.is_valid and all(h.is_valid and outer.contains(h) for h in holes)
        polys[k] = Polygon(outer.exterior.coords, [h.exterior.coords for h in holes])
        assert o["material"] == "yard_paving"
    plaza = polys["tykocin-rynek-plaza-0320"]
    assert 1100 < plaza.area < 1400 and plaza.contains(Point(TY.MONUMENT_EN).buffer(3.5))
    east = polys["tykocin-rynek-walk-east-0320"]
    assert not east.contains(Point(TY.WELL_EN)) and not east.contains(Point(TY.BED_EN))    # they stand on the lawn
