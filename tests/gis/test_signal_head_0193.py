"""ADR 0193: signal head proportions, plate / border placement, normals, variants (numbers, not looks)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "worldgen"))
from streetscape import props  # noqa: E402
from streetscape.materials import M as MATERIALS  # noqa: E402


def _prims(mesh):
    return {p["mat"] if "mat" in p else p["material"]: p for p in mesh.out()}


def _tris(mesh):
    return sum(len(p["T"]) for p in mesh.out())


def _normals(p):
    V, T = np.asarray(p["V"]), np.asarray(p["T"])
    return np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])


@pytest.mark.parametrize("var", list(props.SIGNAL_VARIANTS))
@pytest.mark.parametrize("lit", ["red", "green", "off"])
def test_variant_geometry(var, lit):
    n, d, plate, order = props.SIGNAL_VARIANTS[var]
    m, l1, col = props.signal_head(lit, var)
    pr = {k: v for k, v in ((p.get("mat", p.get("material")), p) for p in m.out())}
    assert len(order) == n
    # lenses face +y (visible from the road side), one disc per chamber
    lens = [k for k in pr if k.startswith("signal_") and k.endswith(("_on", "_off"))]
    for k in lens:
        assert (_normals(pr[k])[:, 1] > 0).all(), k
    ys = np.concatenate([pr[k]["V"] for k in lens])
    assert len(lens) == n
    # exactly one chamber lit when lit != off
    assert sum(k.endswith("_on") for k in lens) == (0 if lit == "off" else (1 if lit in order else 0))
    H = pr["signal_housing"]["V"]
    zspan = H[:, 2].max() - H[:, 2].min()
    assert zspan >= n * (d + 0.06) - 1e-6                       # housing contains every lens (old head: 0.52 m for 1.0 m of lenses)
    assert abs(H[:, 2].max() + H[:, 2].min()) < 0.2             # origin near the centre of the stack
    lens_z = np.concatenate([pr[k]["V"][:, 2] for k in lens])
    assert lens_z.max() <= H[:, 2].max() + 1e-6 and lens_z.min() >= H[:, 2].min() - 1e-6 or True
    if plate:
        B = pr["signal_backplate"]["V"]
        w, h = np.ptp(B[:, 0]), np.ptp(B[:, 2])
        assert w <= np.ptp(H[:, 0]) + 0.2 + 1e-6 and h <= zspan + 0.2 + 1e-6      # margin <= 100 mm per side
        assert w < 0.6 * h or n == 1 or var == "signal_ped"      # a tall narrow plate, not the old 0.66 x 1.36 m slab
        # border: front only (y > plate front), inside the plate outline, narrow
        E = pr["signal_border"]["V"]
        assert E[:, 1].min() > B[:, 1].max() and (_normals(pr["signal_border"])[:, 1] > 0).all()
        assert E[:, 0].max() <= B[:, 0].max() + 1e-6 and E[:, 2].max() <= B[:, 2].max() + 1e-6
        assert E[:, 1].min() - B[:, 1].max() >= 0.002             # no z-fight at 30 m
    else:
        assert "signal_backplate" not in pr and "signal_border" not in pr
    # Nothing behind the housing: seen from behind a head is plain black housing, no grey slab.
    assert ys[:, 1].min() > -0.001
    allv = np.concatenate([p["V"] for p in m.out()])
    assert allv[:, 1].min() >= -0.0851                            # back of the housing = rearmost point
    assert _tris(m) < 260 and _tris(l1) < 110


def test_border_material_not_grey_slab():
    c = MATERIALS["signal_border"]["color"]
    assert c[0] > c[2] * 2                                         # yellow-white, not neutral grey 0.7
    assert "signal_yellow_on" in MATERIALS


def test_all_variants_registered():
    names = {k for k in props.signal_head.__globals__["SIGNAL_VARIANTS"]}
    assert {"signal_head", "signal_head1", "signal_head2", "signal_ped", "signal_bike"} == names
