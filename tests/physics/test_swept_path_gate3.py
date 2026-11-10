"""Gate 3 swept path: the 16.47 m combination drives G3-A / G3-B and a full lap of Rondo Bieżeństwa inside the
generated carriageway (details in swept_path_gate3.py, docs/PHYSICS_VALIDATION.md section 9).

Run:  uv run --project tools/worldgen pytest tests/physics/test_swept_path_gate3.py -q   (needs the world build and
the .NET SDK; ~2-4 min). Tolerance: the raster cell is 0.10 m and the kerb top strip 0.15 m, so a tyre point
-0.15 m "over" the edge is within the resolution (WORKING_VALUE).
"""
from __future__ import annotations

import shutil

import pytest

import swept_path_gate3 as SP

TOL = 0.15


@pytest.fixture(scope="module")
def summary(tmp_path_factory):
    if not (SP.WORLD / "chunk_0_0.glb").exists():
        pytest.skip("world not built (tools/worldgen/roads/build_world.py)")
    if not shutil.which(SP.dotnet()[0]):
        pytest.skip(".NET SDK not found")
    return SP.run(tmp_path_factory.mktemp("swept"))["segments"]


def _tyres(res):
    return {k: v["min_clear_m"] for k, v in res["tyres"].items()}


@pytest.mark.parametrize("key", ["G3-A_wide-v15", "G3-A_wide-v25", "G3-B_wide-v15", "G3-B_wide-v25",
                                 "G3-B_lane-v15", "G3-B_lane-v25", "RING-B_lane-v15", "RING-B_lane-v25"])
def test_no_kerb_mounting(summary, key):
    bad = {k: v for k, v in _tyres(summary[key]).items() if v < -TOL}
    assert not bad, f"{key}: tyres over the kerb line (min clearance m): {bad}"


@pytest.mark.parametrize("key", ["G3-A_wide-v15", "G3-B_wide-v25", "RING-B_lane-v15", "RING-B_lane-v25"])
def test_body_clears_props(summary, key):
    b = {k: v["min_prop_clear_m"] for k, v in summary[key]["body"].items()}
    assert min(b.values()) > 0.3, f"{key}: body corner to prop collider: {b}"


def test_follower_stays_on_line(summary):
    for key, res in summary.items():
        assert res["path_err_m"] < 1.0, f"{key}: steer-axle path error {res['path_err_m']} m"
        assert res["kingpin_consistency_m"] < 0.05, key


def test_lane_centre_driver_cuts_bieżeństwa_exit(summary):
    """Known result, not a geometry defect: with the steer axle on the lane centre the tridem cuts the inner corner
    of the right turn at Rondo Bieżeństwa (s ~ 366 m) by ~1 m; a driver who swings out (wide line) clears it.
    Guards the driver-line dependence so a geometry change that removes or worsens it is noticed."""
    m = min(_tyres(summary["G3-A_lane-v15"]).values())
    assert -1.6 < m < -0.5, m
