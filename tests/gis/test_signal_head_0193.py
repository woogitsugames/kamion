"""ADR 0193 (updated for M66 / Dz.U. 2019 poz. 2311 zał. 3): signal head proportions, contrast plate only on overhead
mast arms, 0.85 x 1.40 m R70 plate BEHIND the 280 mm housing, 40 mm white border with 20 mm margin, 220 mm visors,
and 7 deg downward tilt on overhead heads."""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "worldgen"))
from streetscape import props  # noqa: E402
from streetscape.materials import M as MATERIALS  # noqa: E402


def _tris(mesh):
    return sum(len(p["T"]) for p in mesh.out())


def _normals(p):
    V, T = np.asarray(p["V"]), np.asarray(p["T"])
    n = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    return n / np.maximum(ln, 1e-12)


def _untilt(V, deg):
    V = np.asarray(V, float).copy()
    if not deg:
        return V
    a = math.radians(-deg)
    ca, sa = math.cos(a), math.sin(a)
    y, z = V[:, 1].copy(), V[:, 2].copy()
    V[:, 1] = y * ca + z * sa
    V[:, 2] = -y * sa + z * ca
    return V


@pytest.mark.parametrize("var", list(props.SIGNAL_VARIANTS))
@pytest.mark.parametrize("lit", ["red", "yellow", "green", "off"])
def test_variant_geometry(var, lit):
    n, d, plate, order = props.SIGNAL_VARIANTS[var]
    m, l1, col = props.signal_head(lit, var)
    pr = {p.get("mat", p.get("material")): p for p in m.out()}
    assert len(order) == n
    tilt_deg = props.SIGNAL_OVERHEAD_TILT_DEG if plate else 0.0

    # lenses face +y (and tilt 7 deg down when overhead), one disc per chamber
    lens = [k for k in pr if k.startswith("signal_") and k.endswith(("_on", "_off"))]
    assert len(lens) == n
    for k in lens:
        nrm = _normals(pr[k])
        assert (nrm[:, 1] > 0.98).all(), k
        pitch = np.degrees(np.arctan2(-nrm[:, 2], nrm[:, 1]))
        assert np.allclose(pitch, tilt_deg, atol=0.05)

    # exactly one chamber lit when lit != off and colour exists in order
    assert sum(k.endswith("_on") for k in lens) == (1 if (lit != "off" and lit in order) else 0)

    H = _untilt(pr["signal_housing"]["V"], tilt_deg)
    zspan = H[:, 2].max() - H[:, 2].min()
    assert zspan >= n * (d + 0.06) - 1e-6
    assert abs(H[:, 2].max() + H[:, 2].min()) < 0.2
    # 280 mm housing (-0.080..+0.200) + 220 mm visors (+0.200..+0.420) on LOD0
    assert H[:, 1].min() == pytest.approx(-0.080, abs=1e-6)
    assert H[:, 1].max() == pytest.approx(0.200 + props.SIGNAL_VISOR_L_M, abs=1e-6)
    assert props.SIGNAL_VISOR_L_M == pytest.approx(0.22, abs=1e-6)

    H1 = _untilt({p["mat"]: p for p in l1.out()}["signal_housing"]["V"], tilt_deg)
    assert np.ptp(H1[:, 1]) == pytest.approx(0.280, abs=1e-6)

    if plate:
        B = _untilt(pr["signal_backplate"]["V"], tilt_deg)
        w, h = np.ptp(B[:, 0]), np.ptp(B[:, 2])
        assert w == pytest.approx(0.85, abs=1e-6)
        if n == 3:
            assert h == pytest.approx(1.40, abs=1e-6)
        # R70 rounded corners: no point reaches the sharp (ph, pz) rectangle corner
        ph, pz, r = w / 2, h / 2, props.SIGNAL_PLATE_R_M
        in_corner = (np.abs(B[:, 0]) > ph - r + 1e-6) & (np.abs(B[:, 2]) > pz - r + 1e-6)
        assert np.all(np.hypot(np.abs(B[in_corner, 0]) - (ph - r), np.abs(B[in_corner, 2]) - (pz - r)) <= r + 1e-5)

        # Contrast plate lies BEHIND the housing (-0.085..-0.075), housing & visors protrude in front (+0.200 / +0.420)
        assert B[:, 1].min() == pytest.approx(-0.085, abs=1e-6)
        assert B[:, 1].max() == pytest.approx(-0.075, abs=1e-6)
        assert H1[:, 1].max() - B[:, 1].max() >= 0.270

        # White border: 40 mm strip inset by 20 mm black margin from outer plate edge, 3 mm in front of plate face
        E = _untilt(pr["signal_border"]["V"], tilt_deg)
        assert E[:, 1].min() == pytest.approx(-0.072, abs=1e-6)
        assert E[:, 0].max() == pytest.approx(ph - 0.020, abs=1e-6)
        assert E[:, 2].max() == pytest.approx(pz - 0.020, abs=1e-6)
        # Inner edge of the 40 mm border is at ph - 0.060 = 0.365 (vertical sides) and pz - 0.060 (horizontal sides)
        assert np.any(np.isclose(np.abs(E[:, 0]), ph - 0.060, atol=1e-6))
        assert np.any(np.isclose(np.abs(E[:, 2]), pz - 0.060, atol=1e-6))
        en = _normals(pr["signal_border"])
        assert (en[:, 1] > 0.98).all()
    else:
        assert "signal_backplate" not in pr and "signal_border" not in pr

    assert _tris(m) <= 270 and _tris(l1) <= 115


def test_border_material_is_white_like_marking_white():
    c = MATERIALS["signal_border"]["color"]
    mw = MATERIALS["marking_white"]["color"]
    assert c == mw and abs(c[0] - c[2]) <= 0.02 and c[0] >= 0.50
    assert "signal_yellow_on" in MATERIALS


def test_all_variants_and_lit_states_registered():
    names = set(props.SIGNAL_VARIANTS)
    assert {"signal_head", "signal_head_side", "signal_head1", "signal_head2", "signal_ped", "signal_bike"} == names
    assert props.SIGNAL_VARIANTS["signal_head"][2] is True
    assert props.SIGNAL_VARIANTS["signal_head_side"][2] is False
    assert props.SIGNAL_VARIANTS["signal_ped"][2] is False
    assert props.SIGNAL_VARIANTS["signal_bike"][2] is False
    P = props.build_all(set(), {})
    for var in ("signal_head", "signal_head_side"):
        for lit in ("green", "yellow", "red", "off"):
            assert f"{var}_{lit}" in P
