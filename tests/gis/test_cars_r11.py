"""ADR0089 close wheel silhouette, grounding and neutral material constraints."""
import math
import numpy as np
import pytest

@pytest.mark.parametrize("body", ["hatch", "sedan", "estate", "suv"])
def test_close_wheel_outline_error_below_four_mm_and_grounded(body):
    from streetscape import life_cars as LC
    d = LC.CARS[body]
    shell = LC._Shell(d, 0)
    parts = LC.car(body, "black")
    for lod, limit in ((0, .004), (1, .020)):
        tyre = [p["V"] for p in parts[lod].out() if p["mat"] in ("car_tyre", "car_tyre_dusty", "tyre", "tyre_dusty")]
        v = np.concatenate(tyre)
        front = v[np.abs(v[:, 1] - shell.yfa) <= d["r"] + .001]
        rad = np.hypot(front[:, 1] - shell.yfa, front[:, 2] - d["r"])
        outer = front[np.abs(rad - d["r"]) < 1e-6]
        angles = np.unique(np.round(np.arctan2(outer[:, 2] - d["r"], outer[:, 1] - shell.yfa), 6))
        gaps = np.diff(np.r_[angles, angles[0] + 2 * math.pi])
        error = d["r"] * (1 - math.cos(gaps.max() / 2))
        assert error <= limit, (body, lod, error)
        if lod == 0:
            assert abs(v[:, 2].min()) < 1e-6, (body, "tyre floats above prototype ground")
        else:
            assert len(angles) == 10, (body, "existing LOD1 outline changed")

def test_rubber_and_dusty_rim_are_neutral_with_a_dark_dish():
    from streetscape.materials import M
    for name in ("car_tyre", "car_tyre_dusty", "tyre_dusty", "rim_dusty"):
        rgb = np.array(M[name]["color"])
        assert np.ptp(rgb) < .002, (name, rgb)
    assert M["car_tyre_dusty"]["rough"] >= .9
    assert np.mean(M["rim_dark"]["color"]) < np.mean(M["rim_dusty"]["color"]) * .3
