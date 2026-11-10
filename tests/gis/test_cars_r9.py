"""Parked cars r9 (ADR 0073, REVIEW r8 "soap-bar cars"): budgets, silhouette features, paint and lamp materials."""

from __future__ import annotations

import numpy as np


def _protos():
    from streetscape import life_cars as LC
    for b in LC.CARS:
        yield f"car_{b}_grey", LC.CARS[b], LC.car(b, "grey")
    yield "van_white", LC.VAN, LC.van("white")


def _tris(mesh):
    return sum(len(p["T"]) for p in mesh.out())


def test_lod0_within_4200_and_lod1_within_900():
    """r10 (ADR 0078): modelled lamp buckets, openings, tyre shoulders: LOD0 <= 4200 (r9: 3500; draped lamp wraps and seams), LOD2 <= 96 (r9: 60)."""
    for name, _, P in _protos():
        assert _tris(P[0]) <= 4200, (name, _tris(P[0]))
        assert _tris(P[1]) <= 900, (name, _tris(P[1]))
        assert _tris(P[3]) <= 96, name


def test_front_is_a_face_not_a_wedge():
    """Lamp band >= 0.25 m tall and leaning <= 0.09 m; the bonnet is clearly flatter than the windscreen."""
    from streetscape import life_cars as LC
    for name, d, _ in _protos():
        f = LC.FACES[d["face"]]
        assert f["band"] >= 0.25 and f["lean"] <= 0.09, name
        hood = np.degrees(np.arctan2(d["belt"] - d["nose"], d["hood"] - f["lean"]))
        screen = np.degrees(np.arctan2(d["H"] - 0.035 - d["belt"], d["ws"]))
        assert screen - hood >= 12.0, (name, hood, screen)
        assert 24.0 <= screen <= 50.0, (name, screen)


def test_plan_corners_are_not_a_boat_bow():
    """Half width 0.35 m behind the nose is still >= 86 % of the body (r8: 73-78 %)."""
    from streetscape import life_cars as LC
    for name, d, _ in _protos():
        sh = LC._Shell(d, 0)
        assert sh.plan(sh.y1 - 0.35) >= 0.86 * sh.hw, (name, sh.plan(sh.y1 - 0.35) / sh.hw)


def test_arch_flares_shoulder_and_details():
    from streetscape import life_cars as LC
    for name, d, P in _protos():
        sh = LC._Shell(d, 0)
        ymid = (sh.yra + sh.yfa) / 2
        zt = sh.ztop(ymid)
        # flare at the arch lip, shoulder facet under the belt, tuck at the sill
        assert sh.X(sh.yfa, sh.r + sh.ra) - sh.plan(sh.yfa) >= 0.012, name
        assert sh.X(ymid, zt - 0.06) - sh.X(ymid, zt) >= 0.006, name
        assert sh.X(ymid, zt - 0.3) - sh.X(ymid, d["sill"]) >= 0.03, name
        m0 = {p["mat"]: p for p in P[0].out()}
        lens = _area(m0["car_light_head"])
        housing = _area(m0["car_lamp"])
        assert lens >= 0.04 and housing > 0.02, (name, lens, housing)  # reflector + projector in a housing, not a slit
        assert _area(m0["car_light_tail"]) >= 0.07, name                # r10: the tray behind the opening (tapered)
        tyre = m0.get("car_tyre_dusty") or m0["car_tyre"]
        x = np.abs(tyre["V"][:, 0])
        assert x.max() - x.min() >= 0.20, name                          # tyre has width and a sidewall bulge


def _area(p):
    V, T = np.asarray(p["V"]), np.asarray(p["T"])
    return float(np.linalg.norm(np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]), axis=1).sum() / 2)


def test_van_is_a_panel_van_and_paint_is_glossy():
    from streetscape import life_cars as LC
    from streetscape.materials import M
    assert LC.VAN["H"] >= 1.9 and 4.8 <= LC.VAN["L"] <= 5.0 and LC.VAN.get("cargo")
    for c in LC.CAR_COLOURS + LC.VAN_COLOURS:
        assert 0.15 <= M[f"car_paint_{c}"]["rough"] <= 0.40, c
    red, tail = M["car_paint_red"]["color"], M["car_light_tail"]["color"]
    assert tail[0] < 0.8 * red[0]                                       # the lens reads on a red car
