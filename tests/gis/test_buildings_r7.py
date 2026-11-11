"""ADR 0114 (zabudowa r7): house plots as chunk geometry in one atlas material - plan, fence typology, gate / wicket,
driveway with a dropped kerb, lawn, garden; the plot kit atlas."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import shapely
from shapely.geometry import LineString, box

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "worldgen"))


def _scene():
    road = box(-100, -6, 100, 0)                               # street along x, houses north of it
    houses = [{"id": f"h{k}", "poly": box(20 * k, 6, 20 * k + 10, 14), "props": {"storeys": 1 + k % 2, "height_m": 6.0 + k}}
              for k in range(4)]
    return road, houses


class _Buf:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, **kw):
        self.parts.append(SimpleNamespace(layer=layer, mat=mat, V=np.asarray(V, float), UV=np.asarray(UV, float),
                                          T=np.asarray(T).reshape(-1, 3)))


def _region(road, houses):
    from streetscape import plots as PL
    plots = PL.plan(houses, road, [], [])
    near = PL._Near()
    for p in plots:
        p["garages"] = []
        p["lay"] = PL.layout(p, road.buffer(0.3), near)
        near.add(p["lay"]["segs"])
        g = p["lay"]["gate"]
        p["access"] = None if g is None else {"q": g["m"] + g["n"] * 1.5, "d_cw": 1.5, "chain": None, "walk": "sidewalk_paving",
                                              "kind": 0}
    return {"plots": plots, "drops": [], "roads_poly": road}


def test_plots_are_deterministic_disjoint_and_face_the_road():
    from streetscape import plots as PL
    road, houses = _scene()
    p1 = PL.plan(houses, road, [], [])
    p2 = PL.plan(houses, road, [], [])
    assert len(p1) == 4 and [p["poly"].wkt for p in p1] == [p["poly"].wkt for p in p2]
    for i, p in enumerate(p1):
        assert p["front"] @ np.array([0.0, -1.0]) > 0.99                    # the street side
        assert p["poly"].distance(road) >= PL.ROAD_CLEAR_M - 1e-6            # lawn strip between footway and fence
        assert 1.0 <= PL.ROAD_CLEAR_M <= 2.0
        assert p["poly"].contains(houses[i]["poly"])
        assert p["age"] in PL.FRONT_BY_AGE and p["front_style"] in PL.STYLES and p["side_style"] in PL.STYLES
        lo, hi = PL.STYLES[p["front_style"]][1]
        assert lo <= p["front_h"] <= hi
        for q in p1[i + 1:]:
            assert p["poly"].intersection(q["poly"]).area < 0.3


def test_fence_typology_follows_the_age_class():
    """Old houses: wood and chain-link; new ones: brick + wrought bars, walls, lamellae (docs/refs/posesje-bialystok.md)."""
    from streetscape import plots as PL
    cls = [PL.age_class({"storeys": 1, "height_m": 5.0}, 80.0, f"a{k}") for k in range(300)]
    assert cls.count("old") / 300 > 0.7 and "new" not in cls
    cls = [PL.age_class({"storeys": 2, "height_m": 9.5}, 170.0, f"b{k}") for k in range(300)]
    assert cls.count("new") / 300 > 0.7 and "old" not in cls
    old = {s for s, _ in PL.FRONT_BY_AGE["old"]}
    new = {s for s, _ in PL.FRONT_BY_AGE["new"]}
    assert {"picket", "boards_rust", "boards_brown", "chainlink"} <= old and not ({"wall", "lamella", "brick_bars"} & old)
    assert {"brick_bars", "wall", "lamella"} <= new and not ({"picket", "boards_brown"} & new)
    for age in PL.FRONT_BY_AGE:
        assert sum(w for _, w in PL.FRONT_BY_AGE[age]) == pytest.approx(1.0)
        assert sum(w for _, w in PL.SIDE_BY_AGE[age]) == pytest.approx(1.0)
    # heights from the reference document (WORKING_VALUE ranges)
    assert PL.STYLES["picket"][1] == (1.2, 1.4) and 1.6 <= PL.STYLES["boards_brown"][1][0] and PL.STYLES["wall"][1][1] <= 2.2


def test_layout_has_gate_wicket_and_a_closed_fence():
    from streetscape import plots as PL
    road, houses = _scene()
    rp = _region(road, houses)
    total = 0
    for p in rp["plots"]:
        lay = p["lay"]
        g, w = lay["gate"], lay["wicket"]
        assert g is not None and w is not None and g["kind"] in ("swing", "slide") and w["kind"] == "wicket"
        assert g["n"] @ p["front"] > 0.99 and g["w"] in (PL.GATE_W_M, PL.SLIDE_W_M) and w["w"] == PL.WICKET_W_M
        # the wicket stands right beside the gate (one post between them)
        assert float(np.hypot(*(g["m"] - w["m"]))) == pytest.approx((g["w"] + w["w"]) / 2 + 2 * g["ph"], abs=1e-6)
        length = sum(float(np.hypot(*(r["b"] - r["a"]))) for r in lay["runs"]) + g["w"] + w["w"] + 6 * g["ph"]
        assert length <= p["poly"].length + 1e-6
        total += length / p["poly"].length
        assert {r["style"] for r in lay["runs"]} <= {p["front_style"], p["side_style"]}
        for r in lay["runs"]:                                                  # no run across the gate opening
            assert LineString([r["a"], r["b"]]).distance(shapely.Point(*g["m"])) >= g["w"] / 2 - 1e-6
    assert total / len(rp["plots"]) > 0.7                                      # the rest: a neighbour's fence closes it


def test_plot_shrinks_to_an_existing_fence_and_does_not_double_it():
    from streetscape import plots as PL
    road = box(-100, -6, 100, 0)
    house = [{"id": "h0", "poly": box(0, 6, 10, 14)}]
    fence = LineString([(12.5, 0), (12.5, 40)])               # a real fence 2.5 m east of the house
    p = PL.plan(house, road, [], [fence])[0]
    assert p["poly"].bounds[2] <= 12.5 - 0.4
    near = PL._Near()
    near.add(PL._segments(fence))
    lay = PL.layout(p, road.buffer(0.3), near)
    east = [r for r in lay["runs"] if abs(r["n"][0] - 1.0) < 1e-6]
    assert not [r for r in east if abs(0.5 * (r["a"][0] + r["b"][0]) - 12.5) < PL.PARALLEL_SKIP_M]


def test_terrace_gets_a_wicket_per_house_and_no_gate():
    from streetscape import plots as PL
    road = box(-100, -6, 100, 0)
    row = [{"id": f"t{k}", "poly": box(7 * k, 6, 7 * k + 7, 14)} for k in range(4)]
    plots = PL.plan(row, road, [], [])
    assert len(plots) == 1 and len(plots[0]["houses"]) == 4
    lay = PL.layout(plots[0], road.buffer(0.3), PL._Near())
    assert lay["gate"] is None and len(lay["wickets"]) == 4


def test_house_without_a_road_gets_no_gate():
    """review 0107 P2-r7-a: a plot in a field has no gate onto nothing."""
    from streetscape import plots as PL
    road = box(500, 500, 600, 506)
    p = PL.plan([{"id": "h0", "poly": box(0, 6, 10, 14)}], road, [], [])[0]
    assert p["road_d"] is None
    lay = PL.layout(p, road.buffer(0.3), PL._Near())
    assert lay["gate"] is None and lay["wicket"] is not None


def test_ground_is_one_continuous_driveway_a_path_and_a_lawn():
    """review 0107 P1-r7-c / d: no driveway tiles - one draped polygon per plot from the gate past the house, a path
    from the wicket to the house, and the rest of the plot is the mown lawn (its own surface, not the meadow)."""
    from streetscape import plots as PL
    road, houses = _scene()
    rp = _region(road, houses)
    bpoly = shapely.union_all([h["poly"] for h in houses])
    items = PL.paved_items(rp, road, bpoly, [])
    assert {i["mat"] for i in items} <= {"plot_lawn", "yard_paving"} and all(i["source"] == "plot" for i in items)
    polys = [i["poly"] for i in items]
    for i, a in enumerate(polys):
        assert a.intersection(road).area < 0.05 and a.intersection(bpoly).area < 0.05
        for b in polys[i + 1:]:
            assert a.intersection(b).area < 0.05
    for p in rp["plots"]:
        g = p["lay"]["gate"]
        drive = [i["poly"] for i in items if i["id"].startswith(f"plot:{p['id']}:drive")]
        assert drive
        d = shapely.union_all(drive)
        assert d.distance(road) < 0.1                                           # reaches the road footprint ...
        assert d.buffer(0.1).contains(shapely.Point(*(g["m"] - g["n"] * 4.0)))  # ... and runs in through the gate
        assert max(q.area for q in drive) > PL.DRIVE_W_M * 6.0                  # one slab, not tiles
        lawn = p["lawn"]
        assert lawn is not None and lawn.area > 0.45 * (p["poly"].area - p["foot"].area)
        assert lawn.intersection(d).area < 0.05 and p["path"] is not None


def test_kerb_drop_lowers_the_kerb_only_at_the_driveway():
    from roads import network as NW
    from streetscape import plots as PL
    s = np.arange(0.0, 60.0, 0.5)
    side = {"kind": np.full(len(s), NW.URBAN), "h": np.full(len(s), 0.13), "mat": np.full(len(s), 1)}
    c = SimpleNamespace(id="c1", line=SimpleNamespace(s=s), side={"L": side, "R": {k: v.copy() for k, v in side.items()}})
    net = SimpleNamespace(chains=[c])
    n = PL.apply_drops(net, [{"chain": "c1", "side": "L", "s": 30.0, "half": 2.15, "plot": "p"}])
    assert n == 1
    h = c.side["L"]["h"]
    assert np.all(h[np.abs(s - 30.0) <= 2.15] == pytest.approx(PL.DROP_H_M))    # 2-4 cm lip
    assert 0.02 <= PL.DROP_H_M <= 0.04
    assert np.all(h[np.abs(s - 30.0) >= 2.15 + PL.DROP_RAMP_M] == pytest.approx(0.13))
    ramp = h[(np.abs(s - 30.0) > 2.15) & (np.abs(s - 30.0) < 2.15 + PL.DROP_RAMP_M)]
    assert len(ramp) and np.all((ramp > PL.DROP_H_M) & (ramp < 0.13))
    assert np.all(c.side["R"]["h"] == pytest.approx(0.13))                      # the other side keeps its kerb


def test_plot_is_one_material_and_no_instances():
    """Budget (review 0107 P1-r7-a): the whole plot is chunk geometry in ONE material; nothing is instanced."""
    from streetscape import plot_kit as PK
    from streetscape import plots as PL
    road, houses = _scene()
    rp = _region(road, houses)
    PL.paved_items(rp, road, shapely.union_all([h["poly"] for h in houses]), [])
    buf, rep = _Buf(), {}
    PL.build(buf, rp, lambda q: 100.0, None, rep)
    assert {(p.layer, p.mat) for p in buf.parts} == {("furniture", "plot_kit"), ("collision", "collision_fence")}
    r = rep["plots"]
    assert r["instances"] == 0 and r["gates"] == 4 and r["wickets"] == 4
    kit = [p for p in buf.parts if p.mat == "plot_kit"]
    assert len(kit) == 4                                                        # one mesh part per plot
    for p in kit:
        assert len(p.T) < 6000
        assert p.UV[:, 1].min() >= 0.0 and p.UV[:, 1].max() <= 1.0              # v never leaves the atlas rows
        assert p.V[:, 2].min() > 99.5 and p.V[:, 2].max() < 100.0 + 12.0
    assert not hasattr(PL, "protos")                                            # no instanced prototypes left
    assert PK.atlas().size == (PK.N, PK.N)


def test_thuja_rows_are_irregular():
    """review 0107 P1-r7-e: no row of identical cones every 0.9 m."""
    from streetscape import plots as PL
    hs, rs = [], []
    for k in range(40):
        kit = PL.Kit()
        h = 2.4 * (0.7 + 0.6 * PL.hfloat("row", k))
        PL.thuja(kit, np.array([k * 0.9, 0.0]), 0.0, h, 0.26 + 0.07 * h, ("t", k))
        V = kit.out()[0]
        hs.append(V[:, 2].max())
        rs.append(np.hypot(V[:, 0] - k * 0.9, V[:, 1]).max())
    assert max(hs) / min(hs) > 1.5 and np.std(rs) / np.mean(rs) > 0.08
    assert len(kit.out()[2]) <= 40                                              # 5 sides x <= 4 bands x 2


def test_plot_kit_atlas_rows_and_matt_colours():
    from streetscape import plot_kit as PK
    im = np.asarray(PK.atlas()).astype(float)
    assert im.shape == (PK.N, PK.N, 4)
    last = 0
    for name, (y0, h) in PK.ROW_Y.items():
        assert y0 >= last and y0 + h <= PK.N
        last = y0 + h
        v0, v1 = PK.row(name)
        assert 0.0 < v0 < v1 < 1.0
    cov = PK.coverage()
    assert cov["concrete"] == 1.0 and cov["wall"] == 1.0 and cov["brick"] == 1.0
    assert 0.25 < cov["chainlink"] < 0.6 and 0.1 < cov["bars"] < 0.35 and cov["picket"] > 0.5
    # review 0107 P1-r7-b: the mesh must not glow - opaque chain-link texels are dark green, far from white
    y0, h = PK.ROW_Y["chainlink"]
    row = im[y0:y0 + h]
    on = row[..., 3] > 200
    rgb = row[on][:, :3]
    assert rgb.max() < 140 and rgb[:, 1].mean() > rgb[:, 0].mean() + 20
    for name, (u, v) in PK.SWATCH.items():
        x, y = int(u * PK.N), int((1 - v) * PK.N)
        assert im[y, x, 3] == 255 and np.abs(im[y, x, :3] - np.array(PK._SW_RGB[name])).max() < 30


def test_materials_plot_kit_is_matt_and_lawn_is_lighter_than_the_verge():
    from roads import standards as S
    from streetscape import materials as M
    kit = M.M["plot_kit"]
    assert kit.get("metal", 0.0) == 0.0 and kit["rough"] >= 0.8 and kit["alpha_cutoff"] == 0.5 and kit["texture"] == "plot_kit"
    lawn = M.M["plot_lawn"]
    assert lawn["texture_set"] == "grass_verge" and S.SURFACE_OF["plot_lawn"] == "grass"

    def lum(c):
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    assert 1.15 < lum(lawn["color"]) / lum([0.08, 0.105, 0.038]) < 2.2
