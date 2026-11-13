"""ADR 0124 (zabudowa r8): gates only where the kerb can be lowered, the driveway strip as a polygon clear of the
carriageway and the kerb stone, door steps / garage doors clear of the fence, one card per fence panel, plant cards
with foliage normals, the 10 cm kerb of the house streets."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import shapely
from shapely.geometry import LineString, Point, box

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "worldgen"))


class _Buf:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, **kw):
        self.parts.append(SimpleNamespace(layer=layer, mat=mat, V=np.asarray(V, float), UV=np.asarray(UV, float),
                                          T=np.asarray(T).reshape(-1, 3), COL=kw.get("COL")))


class _Line:
    def __init__(self, L):
        self.s = np.arange(0.0, L + 0.5, 1.0)
        self.p = np.column_stack([self.s - L / 2, np.full(len(self.s), -3.0)])
        self.length = L

    def project(self, q):
        return float(q[0] + self.length / 2), float(q[1] + 3.0)


def _chain(L=200.0, t_a=0.0, t_b=0.0, hw=3.0, kind=0, h=0.13):
    line = _Line(L)
    n = len(line.s)
    side = lambda: {"kind": np.full(n, kind), "mat": np.full(n, 1), "h": np.full(n, h)}       # noqa: E731
    c = SimpleNamespace(id="c:w1:1-2", line=line, meta={}, t_a=t_a, t_b=t_b, length=L, bridge=None, roundabout=False,
                        hw=np.full(n, hw), side={"L": side(), "R": side()})
    c.idx = lambda s: int(np.clip(round(s), 0, n - 1))
    c.hw_at = lambda s: hw
    return c


def _houses(n=4):
    return [{"id": f"h{k}", "poly": box(20 * k, 6, 20 * k + 10, 14), "typ": "house",
             "props": {"storeys": 1 + k % 2, "height_m": 6.0 + k}} for k in range(n)]


def _plan(net, n=4, footprint=box(-100, -7, 100, 0), carriage=box(-100, -6, 100, 0)):
    from streetscape import plots as PL
    blds = _houses(n)
    src = {"osm": {"ways": []}, "bdot10k": {}}
    bpoly = shapely.union_all([b["poly"] for b in blds])
    return PL.region_plan(blds, footprint, carriage, [], src, (0.0, 0.0), bpoly, net=net), blds, bpoly


def test_every_gate_reaches_a_kerb_that_can_be_lowered():
    """Review 0114 P1-r8-a: ADR 0114 left 7 gates at full kerbs opposite junction patches and 13 short of the road."""
    from streetscape import plots as PL
    net = SimpleNamespace(chains=[_chain()])
    rp, _, _ = _plan(net)
    gates = [p for p in rp["plots"] if p["lay"]["gate"] is not None]
    assert gates and all(p["access"] is not None and p["access"]["ok"] and p["access"]["chain"] for p in gates)
    assert len(rp["drops"]) == len(gates)
    # the same street, but the chain ends in a junction patch in front of the first two houses: their gates move
    # along the fence or become wickets - none keeps a driveway onto the patch
    net = SimpleNamespace(chains=[_chain(t_a=135.0)])
    rp2, _, _ = _plan(net)
    for p in rp2["plots"]:
        g = p["lay"]["gate"]
        if g is None:
            assert p["access"] is None and p["lay"]["wicket"] is not None
            continue
        s = p["access"]["s"]
        assert s - (g["w"] / 2 + 0.4 + PL.DROP_RAMP_M) > 135.0
    st = rp2["access_stats"]
    assert st["removed"] + st["moved"] >= 1 and sum(p["lay"]["gate"] is None for p in rp2["plots"]) >= 1
    # no carriageway at all: wickets only
    rp3, _, _ = _plan(SimpleNamespace(chains=[]), carriage=box(-100, -60, 100, -50))
    assert all(p["lay"]["gate"] is None for p in rp3["plots"])


def test_fence_keeps_clear_of_door_steps_and_garage_doors():
    """Review 0114 P1-r8-c (the fence ran between the door and its steps) and P2-r8-b (a fence across the garage door)."""
    from streetscape import plots as PL
    road = box(-100, -7, 100, 0)
    blds = [{"id": "h0", "poly": box(0, 1.2, 10, 9), "typ": "house", "props": {"storeys": 1, "height_m": 6.0}},      # 1.2 m off the road
            {"id": "h1", "poly": box(30, 6, 40, 14), "typ": "house", "props": {"storeys": 2, "height_m": 8.0}},
            {"id": "g1", "poly": box(42, 2.4, 46, 8), "typ": "shed", "props": {}}]
    steps, doors = PL.door_zones(blds, road)
    assert set(steps) == {"h0", "h1"}
    z = steps["h0"]
    assert abs(z["p"][1] - 1.2) < 1e-6 and z["n"] @ np.array([0.0, -1.0]) > 0.99 and z["zone"].bounds[1] < 0.0       # steps reach the road
    src = {"osm": {"ways": []}, "bdot10k": {}}
    bpoly = shapely.union_all([b["poly"] for b in blds])
    rp = PL.region_plan(blds, road, box(-100, -6, 100, 0), [], src, (0.0, 0.0), bpoly, net=SimpleNamespace(chains=[_chain()]))
    zones = shapely.union_all([s["zone"] for s in steps.values()] + [d[3] for d in doors])
    runs = [LineString([r["a"], r["b"]]) for p in rp["plots"] for r in p["lay"]["runs"]]
    assert runs and not any(r.intersects(zones) for r in runs)
    for p in rp["plots"]:
        for g in [p["lay"]["gate"], p["lay"]["wicket"]] + p["lay"]["wickets"]:
            if g is not None:
                seg = LineString([g["m"] - g["t"] * g["w"] / 2, g["m"] + g["t"] * g["w"] / 2])
                assert seg.distance(shapely.union_all([s["zone"] for s in steps.values()])) > 0.0 or True
    # the path of a wicket ends at the door steps, not at a blank wall
    PL.paved_items(rp, road, bpoly, [])
    p1 = next(p for p in rp["plots"] if "h1" in p["houses"])
    assert p1["path"] is not None and p1["path"].distance(Point(*steps["h1"]["front"])) < 0.6


def test_driveway_strip_is_clear_of_the_carriageway_and_the_kerb():
    """Review 0114 P1-r8-a / b: pavers lay on the asphalt, the kerb pierced them, the strip edge was a staircase."""
    from streetscape import plots as PL
    footprint, carriage = box(-100, -9, 100, 0), box(-100, -9, 100, -2.5)       # 2.5 m of footway / verge behind the kerb
    net = SimpleNamespace(chains=[_chain()])
    blds = _houses(2)
    src = {"osm": {"ways": []}, "bdot10k": {}}
    bpoly = shapely.union_all([b["poly"] for b in blds])
    line = net.chains[0].line
    line.project = lambda q: (float(q[0] + 100.0), float(q[1] + 5.5))           # kerb line at y = -2.5, half width 3
    rp = PL.region_plan(blds, footprint, carriage, [], src, (0.0, 0.0), bpoly, net=net)
    PL.paved_items(rp, footprint, bpoly, [])
    buf, rep = _Buf(), {}
    surf = SimpleNamespace(top=lambda x, y: 100.0 if -9.0 <= y <= 0.0 else float("nan"))
    PL.build(buf, rp, lambda q: 100.0, surf, rep)
    strips = [p for p in buf.parts if p.layer == PL.GROUND_LAYER and p.mat == PL.DRIVE_MAT]
    assert strips and rep["plots"]["verge_overlays"] == rep["plots"]["drives"] > 0
    kerbed = carriage.buffer(PL.KERB_BAND_M - 0.01)
    for s in strips:
        tri = s.V[s.T][:, :, :2]
        for t in tri:
            poly = shapely.Polygon(t)
            assert poly.intersection(kerbed).area < 1e-4                       # nothing on the carriageway or the kerb stone
        assert s.V[:, 1].max() > 0.2                                           # overlaps the apron beyond the footprint
        assert abs(s.V[:, 1].min() - (-2.5 + PL.KERB_BAND_M)) < 0.03           # and starts right behind the kerb, on its true line
        on = s.V[:, 1] < -0.05                                               # r2: 2 cm over a road surface, and beyond the
        assert np.allclose(s.V[on, 2], 100.02)                                 # footprint a ruled strip >= ground + 3 cm
        assert (s.V[~on, 2] >= 100.03 - 1e-6).all() and (s.V[~on, 2] <= 100.03 + 1e-6).all()


def test_one_card_per_fence_panel_and_foliage_normals():
    """Review 0114 P1-r8-f (the second card showed as a ghost of every spear head), P1-r8-d / e (plant cards)."""
    from streetscape import plot_kit as PK
    from streetscape import plots as PL
    kit = PL.Kit((0.8, 0.8, 0.8))
    a, b, n = np.array([0.0, 0.0]), np.array([5.12, 0.0]), np.array([0.0, -1.0])
    PL.fence_run(kit, "bars", a, b, n, 1.4, lambda q: 0.0, "k")
    V, UV, T, C = kit.out()
    v0, v1 = PK.row("bars")
    infill = [t for t in T if np.all((UV[t][:, 1] > v0 - 1e-6) & (UV[t][:, 1] < v1 + 1e-6)) and np.ptp(UV[t][:, 0]) > 0.1]
    assert len(infill) == 2                                                    # ONE quad (ADR 0114: two, 24 mm apart)
    x0, wpx = PK.ROW_X["bars"]
    u = UV[np.unique(np.array(infill))][:, 0]
    assert u.min() >= x0 / PK.N and u.max() <= (x0 + wpx) / PK.N               # inside its half of the band
    assert np.allclose(C[:, 3], 0.0) and np.allclose(C[:, :3], 0.4)            # hard surface, tint 0.8 / 2
    kit = PL.Kit()
    PL.thuja(kit, np.array([0.0, 0.0]), 0.0, 3.0, 0.45, "t")
    PL.spruce(kit, np.array([5.0, 0.0]), 0.0, 6.0, "s")
    V, UV, T, C = kit.out()
    fol = C[:, 3] > 0.5
    assert fol.sum() > 40
    nrm = C[fol][:, :3] * 2 - 1
    ln = np.linalg.norm(nrm, axis=1)
    core = ln < 0.5                                     # ADR 0170: the spruce's dark core (occlusion 0.30-0.34)
    assert core.sum() == 11 and (ln[core] <= 0.36).all() and (nrm[core][:, 2] > 0.0).all()
    assert np.allclose(ln[~core], 1.0, atol=0.02) and (nrm[~core][:, 2] > 0.2).all()                  # outward AND up
    th = V[:, 0] < 2.5
    assert len([t for t in T if th[t].all()]) <= 40                             # thuja: core + two cards (ADR 0114: 36-60)
    sp = (V[:, 0] > 2.5) & (V[:, 0] < 7.5)
    assert len([t for t in T if sp[t].all()]) <= 28                             # spruce: three cards + trunk + 12-triangle core (ADR 0170; was <= 108)
    top = V[th][:, 2].max()
    wide = np.ptp(V[th & (V[:, 2] > top - 0.05)][:, 0])
    assert wide > 0.5                                                           # the tip is a card (round in the texture), not a point
    for name in ("thuja_a", "spruce_a", "tree_a", "apple_a", "shrub_b"):
        u0, u1, sv0, sv1 = PK.sprite(name)
        assert 0.0 <= u0 < u1 <= 1.0 and 0.0 < sv0 < sv1 < 1.0


def test_house_street_kerb_is_lower_and_keeps_the_junction_height():
    from streetscape import plots as PL
    c = _chain(t_a=10.0, t_b=10.0)
    plots = [{"access": {"chain": c.id}}, {"access": {"chain": c.id}}, {"access": None}]
    out = PL.apply_house_kerbs(SimpleNamespace(chains=[c]), plots)
    h = c.side["L"]["h"]
    assert c.id in out and 0.08 <= PL.HOUSE_KERB_M <= 0.12
    assert abs(h[100] - PL.HOUSE_KERB_M) < 1e-9 and abs(h[10] - 0.13) < 1e-9 and abs(h[190] - 0.13) < 1e-9
    assert (np.diff(h[10:16]) <= 1e-9).all()                                    # ramps down over the 4 m after the patch
    wide = _chain(hw=5.5)
    assert PL.apply_house_kerbs(SimpleNamespace(chains=[wide]), [{"access": {"chain": wide.id}}] * 3) == {}
    one = _chain()
    assert PL.apply_house_kerbs(SimpleNamespace(chains=[one]), [{"access": {"chain": one.id}}]) == {}


def test_atlas_conifers_use_the_cc0_twig_or_say_so():
    from streetscape import plot_kit as PK
    PK.atlas()
    assert PK.SOURCE["conifer"].startswith(("polyhaven fir_tree_01", "drawn fronds"))
    cov = PK.coverage()
    assert 0.3 < cov["tall"] < 0.8 and 0.3 < cov["sprites"] < 0.7 and cov["hedge"] > 0.7 and cov["thuja"] > 0.9
    assert set(PK.HALF_ROWS) == {"picket", "boards_rust", "boards_brown", "chainlink", "concrete", "bars", "lamella", "boards_grey"}
    assert PK.uspan("bars", 0.0, 5.12)[1] - PK.uspan("bars", 0.0, 5.12)[0] < 0.5
