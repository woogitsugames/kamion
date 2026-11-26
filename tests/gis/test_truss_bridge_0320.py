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

    def add(self, layer, mat, vertices, uv, triangles, src="", UV1=None, footprint=False, COL=None):
        self.parts.append((layer, mat, np.asarray(vertices, float), np.asarray(triangles), src))
        self.cols = getattr(self, "cols", {})
        if COL is not None:
            assert len(COL) == len(vertices) and len(uv) == len(vertices)
            self.cols[(layer, mat)] = np.asarray(COL, float)


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
    assert rep[TY.ASSET_ID] is r and r["status"] == "applied"
    # ten orthophoto marks: six benches in three variants and four planter boxes; eight more planters at the monument
    assert len(r["benches"]) == 6 and len(r["planters"]) == 4 + len(TY.MONUMENT_PLANTERS)
    assert {b["variant"] for b in r["benches"]} == set(TY.BENCH_VARIANTS)
    # nothing is lined up with a string: every bench is turned by 2-9 degrees, and not all the same way
    yaws = [b["yaw_off_deg"] for b in r["benches"]]
    assert all(2.0 <= abs(y) <= 9.0 for y in yaws) and min(yaws) < 0 < max(yaws) and len(set(yaws)) == len(yaws)
    # budget (ADR 0320 dopisek): the monument is the landmark of the square - hero asset <= 27 k, everything <= 36 k
    assert 7.0 <= r["monument"]["height_m"] <= 8.0 and r["tris"]["buildings"] <= 36000
    assert r["tris"]["buildings_low"] <= 0.10 * r["tris"]["buildings"]
    for layer, mat, v, t, src in buf.parts:
        assert np.isfinite(v).all() and src == TY.ASSET_ID
        assert (np.linalg.norm(np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]]), axis=1) > 1e-9).all()
    gilt = next(v for layer, m, v, t, _ in buf.parts if layer == "buildings" and m == TY.GILT)
    # the mace is held out to the figure's right (west when it faces south) and forward (south), head high
    assert gilt[:, 0].mean() < TY.MONUMENT_EN[0] - 0.6 and gilt[:, 1].mean() < TY.MONUMENT_EN[1] - 0.3
    assert gilt[:, 2].max() - 104.0 > r["monument"]["height_m"] - 0.3
    low = {m for layer, m, *_ in buf.parts if layer == "buildings_low"}
    assert not low & {TY.GILT, TY.IRON, TY.STONE, "bench_wood"}
    # weathering / wear travels in COLOR_0 (a = 1) on the stone, the bench wood and the flowers - in both LODs
    for layer in TY.LAYERS:
        for mat in (TY.SAND, TY.WOOD, TY.FLOWERS):
            col = buf.cols[(layer, mat)]
            assert col.min() >= 0.0 and col.max() <= 1.0 and (col[:, 3] > 0.99).all()
    stone = buf.cols[("buildings", TY.SAND)][:, :3].mean(1)
    assert np.percentile(stone, 95) - np.percentile(stone, 5) > 0.25, "the stone must not be one flat tone"
    wood = buf.cols[("buildings", TY.WOOD)][:, :3].mean(1)
    assert len(np.unique(np.round(wood, 3))) >= 20, "every board has its own tone"
    r = TY.build(Buffer(), "tykocin", [751371.0, 600319.0], [], lambda e, n: np.full_like(e, np.nan), {})
    assert r["status"] == "skipped" and r["monument"] is None


def test_czarniecki_hero_asset_budget_and_provenance():
    """The Blender asset is in plain git, was built from the committed generator + dims and keeps its LOD budgets."""
    import hashlib
    parts, meta = TY.hero()
    d = TY.HERO_DIR
    gen = ROOT / "tools" / "blender" / "world" / "landmarks" / "make_czarniecki.py"
    sha = lambda f: hashlib.sha256(f.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert meta["generator_sha256"] == sha(gen), "re-run make_czarniecki.py (generator changed after the asset was built)"
    assert meta["dims_sha256"] == sha(d / "dims.json")
    tris = {lod: sum(len(m["T"]) for m in parts[lod].values()) for lod in ("lod0", "lod1")}
    assert 15000 <= tris["lod0"] <= 27000 and tris["lod1"] <= 2000 and tris["lod1"] <= 0.08 * tris["lod0"]
    assert (d / f"{TY.HERO}.npz").stat().st_size < 1_000_000
    v = np.concatenate([m["V"] for m in parts["lod0"].values()])
    assert 7.0 <= v[:, 2].max() <= 8.0 and np.abs(v[:, :2]).max() <= 2.5
    stone = parts["lod0"][TY.SAND]
    assert stone["COL"].dtype == np.uint8 and (stone["COL"][:, 3] == 255).all() and len(stone["UV"]) == len(stone["V"])
    # the figure stands on the cornice: plenty of geometry above it (head, arms, fur), not a lathed bottle
    assert (stone["V"][:, 2] > meta["figure_base_z"]).sum() > 4000


def test_square_paving_overrides_are_valid_polygons_around_the_monument():
    from shapely.geometry import Point, Polygon
    ovs = yaml.safe_load((REGION / "overrides.yaml").read_text(encoding="utf8"))["overrides"]
    areas = {o["id"]: o for o in ovs if o.get("kind") == "paved_area"}
    border = {f"tykocin-rynek-plaza-border-{k}-0325" for k in "nesw"}          # ADR 0325: red sett band round the plaza
    aprons = {"tykocin-rynek-apron-n-0325", "tykocin-rynek-apron-s-0325"}           # setts between the plaza and the streets
    assert set(areas) == {"tykocin-rynek-plaza-0320", "tykocin-rynek-walk-east-0320", "tykocin-rynek-walk-west-0320"} | border | aprons
    origin = np.array([751371.0, 600319.0])
    polys = {}
    for k, o in areas.items():
        outer = Polygon(np.asarray(o["polygon_epsg2180"]) - origin)
        holes = [Polygon(np.asarray(h) - origin) for h in o.get("holes_epsg2180", [])]
        assert outer.is_valid and all(h.is_valid and outer.contains(h) for h in holes)
        polys[k] = Polygon(outer.exterior.coords, [h.exterior.coords for h in holes])
        # ADR 0325: stone setts - lattice on the plaza, red band, grey granite walks (was yard_paving)
        assert o["material"] == ("plaza_sett_lattice" if k == "tykocin-rynek-plaza-0320" else
                                 "plaza_sett_red" if k in border else "plaza_sett_grey")
    plaza = polys["tykocin-rynek-plaza-0320"]
    assert 1100 < plaza.area < 1400 and plaza.contains(Point(TY.MONUMENT_EN).buffer(3.5))
    # the band is 0.75 m wide, joins the lattice without a gap or an overlap
    ring = Polygon(np.asarray([areas[f"tykocin-rynek-plaza-border-{k}-0325"]["polygon_epsg2180"][0] for k in "nesw"]) - origin)
    band = ring.difference(plaza)
    assert abs(sum(polys[k].area for k in border) - band.area) < 0.5 and 0.70 < band.area / ring.length < 0.80
    assert all(polys[k].intersection(plaza).area < 0.05 for k in border)
    east = polys["tykocin-rynek-walk-east-0320"]
    assert not east.contains(Point(TY.WELL_EN)) and not east.contains(Point(TY.BED_EN))    # they stand on the lawn


def test_plaza_lattice_frame_matches_the_measured_band_families_0325():
    """ADR 0325: uv_frame = one lattice crossing + the lattice diagonal; in that frame the bands of the set
    (tile diagonals) fall on the two families measured on the orthophoto."""
    import math
    from streetscape import paved, materials
    ovs = yaml.safe_load((REGION / "overrides.yaml").read_text(encoding="utf8"))["overrides"]
    o = next(x for x in ovs if x.get("id") == "tykocin-rynek-plaza-0320")
    fr = o["uv_frame"]
    period, a1 = 2.255, math.radians(53.75)
    ref = np.array([751808.0, 600236.0])
    n1, n2 = np.array([math.cos(a1), math.sin(a1)]), np.array([-math.sin(a1), math.cos(a1)])
    d = np.asarray(fr["origin_epsg2180"]) - ref
    for n, phase in ((n1, -18.488), (n2, -18.020)):                 # measured phases of the two families
        k = (d @ n - phase) / period
        assert abs(k - round(k)) * period < 0.02
    assert abs(fr["angle_deg"] - (53.75 - 45.0)) < 1e-9
    origin = np.array([751371.0, 600319.0])
    src = {"osm": {"areas": []}, "bdot10k": {"OT_PTPL_A": [], "OT_KUKO_A": [], "OT_SKRP_L": []}}
    from shapely.geometry import Polygon
    items = paved.collect(src, origin, [o], [], Polygon(), None, {})
    assert len(items) == 1 and items[0]["mat"] == "plaza_sett_lattice"
    ox, oy, ang = items[0]["uv_frame"]
    assert np.allclose([ox, oy], np.asarray(fr["origin_epsg2180"]) - origin) and math.isclose(ang, math.radians(8.75))

    class Buf:
        def __init__(self): self.parts = []
        def add(self, layer, mat, V, UV, T, **kw): self.parts.append((layer, mat, np.asarray(V), np.asarray(UV)))

    class HF:
        x0, y1 = 0.0, 0.0
        z = np.zeros((400, 800))
    buf = Buf()
    paved.build_meshes(buf, items, np.full((400, 800), 104.0), HF)
    layer, mat, V, UV = next(p for p in buf.parts if p[0] == "paved" and p[1] == "plaza_sett_lattice")
    # a point one period along family 1 from the crossing lands on a band line of the tile: (u + v) / sqrt 2 = period
    p = (np.asarray(fr["origin_epsg2180"]) - origin) + n1 * period
    c, s_ = math.cos(-ang), math.sin(-ang)
    q = p - [ox, oy]
    uv = np.array([q[0] * c - q[1] * s_, q[0] * s_ + q[1] * c])
    assert math.isclose((uv[0] + uv[1]) / math.sqrt(2), period, abs_tol=1e-9) and abs(uv[0] - uv[1]) < 1e-9
    # mesh UV0 is that same frame (metres), not the dominant axis of the outline
    k = 0
    q = V[k, :2] - [ox, oy]
    assert np.allclose(UV[k], [q[0] * c - q[1] * s_, q[0] * s_ + q[1] * c])
    assert materials.M["plaza_sett_lattice"]["texture_set"] == "sett_lattice_tykocin" and materials.M["plaza_sett_lattice"]["set_tile"]
    spec = __import__("json").loads((REGION.parents[2] / "art-source/world/materials/materials_spec.json").read_text(encoding="utf8"))
    lat = spec["sets"]["sett_lattice_tykocin"]
    assert math.isclose(lat["tile_m"][0], period * math.sqrt(2), abs_tol=1e-3) and lat["uv"].startswith("mesh_uv0")
    assert lat["kind"] == "tiling_set" and spec["sets"]["sett_rows_tint"]["kind"] == "modulation_set"
