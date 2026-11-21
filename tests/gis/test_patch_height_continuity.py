"""Road influence must fade continuously into the junction background."""
from types import SimpleNamespace
import numpy as np
import pytest
from roads import meshing as M

pytestmark = pytest.mark.unit


def test_patch_height_is_continuous_at_half_metre_influence_boundary():
    ph = M.PatchHeight.__new__(M.PatchHeight)
    ph.internal, ph.arms = [], []
    for y, z in ((0., 140.), (10., 140.4)):
        line = SimpleNamespace(project=lambda p, y=y: (float(p[0] + 20.), float(p[1] - y)))
        chain = SimpleNamespace(line=line, length=40., hw_at=lambda s: 3.,
                                crossfall_z=lambda s, lat, z=z: z + .02 * lat)
        arm = SimpleNamespace(chain=chain, end='a', lat_sign=lambda: 1.)
        ph.arms.append((arm, 20., np.array([0., y]), np.array([1., 0.]),
                        np.array([0., 1.]), 3., 0., z))
    p = np.array([-10., 3.5])
    below, above = (ph.blend(p + [0., d]) for d in (-1e-6, 1e-6))
    assert abs(above - below) < 1e-6
    # The extra influence vanishes smoothly, including its first derivative.
    dz = 1e-5
    mid = ph.blend(p)
    left = (mid - ph.blend(p - [0., dz])) / dz
    right = (ph.blend(p + [0., dz]) - mid) / dz
    assert abs(left - right) < 1e-5
