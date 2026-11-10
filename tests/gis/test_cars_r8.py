"""Parked cars r8 (ADR 0041 r8, REVIEW r7 N-13 / N-14): no see-through panels on any body x LOD, LOD1 detail."""

from __future__ import annotations

import sys

import pytest

from conftest import REPO

sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))


def _protos():
    from streetscape import life_cars as LC
    # one prototype per body; red hatch = clear glass, the others privacy glass; the van has no rear glazing
    for b in LC.CARS:
        yield f"car_{b}_red", LC.car(b, "red")
    yield "van_white", LC.van("white")


@pytest.mark.parametrize("lod", [0, 1, 2])
def test_no_background_inside_the_silhouette(lod):
    """REVIEW r7 N-13 acceptance: every body x LOD from 8 directions (x 3 elevations: a car seen from the kerb, from
    the cab 2.5 m up and from a viaduct) shows no pixel where the ray enters or leaves through the back of a panel and
    no cabin part outside the glass (tools/worldgen/qa/car_holes_qa.py, 25 mm pixels, blobs >= 3 px)."""
    import car_holes_qa as Q
    for name, P in _protos():
        d = Q.defects(P[{0: 0, 1: 1, 2: 3}[lod]], res=0.025)
        bad = {k: v for k, v in d.items() if v[0] + v[1] > 0}
        assert not bad, (name, lod, bad)


def test_lod1_keeps_wheels_lamps_and_its_own_plate():
    """REVIEW r7 N-14: LOD1 (Low 16-45 m) has head-lamp lenses, spoke windows on the alloys, round 10-gon tyres and
    the prototype's own registration plate."""
    import numpy as np
    from streetscape import life_cars as LC
    for name, P in _protos():
        m1 = {p["mat"]: p for p in P[1].out()}
        assert "car_light_head" in m1 and "car_lamp" in m1 and "car_light_tail" in m1, name
        assert {"rim_dark", "rim_steel", "rim", "rim_dusty"} & set(m1), name    # spoke windows / hub / wheel cover
        tyre = m1.get("tyre_dusty") or m1["tyre"]
        assert len(tyre["T"]) >= 4 * 10 * 2, name                              # 4 wheels x 10 sidewall quads
        u0, v0, u1, v1 = LC.plate_uv(LC._plate_index(name[4:] if name.startswith("car_") else name))
        uv = np.asarray(m1["car_plate"]["UV"])
        assert uv[:, 0].min() >= u0 - 1e-6 and uv[:, 0].max() <= u1 + 1e-6, name
