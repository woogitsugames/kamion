"""Ground-cover context regressions: a road verge is not automatically a lawn."""
from types import SimpleNamespace

import numpy as np
import pytest
from shapely.geometry import box, mapping

from streetscape.vegetation import ground_masks
from streetscape.plantings import hedge_mass, hedge_mats


def test_verge_keeps_patch_variation_beside_a_mapped_lawn_without_invented_bare_soil():
    hf = SimpleNamespace(z=np.zeros((129, 129)), x0=-64., y1=64.)
    src = {"osm": {"areas": [{"geometry": mapping(box(-70, -70, 0, 70)),
                             "tags": {"landuse": "grass"}}]},
           "bdot10k": {"OT_PTNZ_A": []}}
    masks = ground_masks(src, np.zeros(2), hf, np.full(hf.z.shape, 2.), [])
    lawn, verge = masks[8:-8, 8:56, 2], masks[8:-8, 73:-8, 2]
    assert verge.std() > 1.5 * lawn.std()
    assert np.ptp(verge) > .5
    assert not masks[..., 1].any()  # no mapped forest
    assert not masks[..., 3].any()  # proximity alone cannot invent exposed soil
    assert np.isfinite(masks).all() and masks.min() >= 0 and masks.max() <= 1


def test_mapped_forest_and_exposed_soil_survive_ground_variation():
    hf = SimpleNamespace(z=np.zeros((129, 129)), x0=-64., y1=64.)
    src = {"osm": {"areas": []}, "bdot10k": {"OT_PTNZ_A": [
        {"geometry": mapping(box(10, -40, 40, 40))}]}}
    dist = np.full(hf.z.shape, 6.)
    dist[:, 64] = 0
    masks = ground_masks(src, np.zeros(2), hf, dist, [box(-50, -50, -10, 50)])
    assert masks[64, 34, 1] > .99
    assert masks[64, 94, 3] > .35
    assert masks[64, 34, 3] == 0
    assert (masks[:, 64, 0] == 0).all()  # road channel remains exactly zero on road


@pytest.mark.parametrize("plant", ["berberis_red", "privet", "hornbeam", "thuja"])
def test_hedge_core_stays_below_the_actual_triangulated_leaf_shell(plant):
    class Capture:
        def __init__(self):
            self.parts = []

        def add(self, layer, material, vertices, uv, triangles, **kwargs):
            self.parts.append((material, np.asarray(vertices), np.asarray(triangles)))

    buf = Capture()
    hedge_mass(buf, box(0, 0, 8, 1.3), lambda x, y: np.zeros_like(x),
               ("qa", "local-top"), h=.65, plant=plant)
    core_m, shell_m, sprig_m = hedge_mats(plant)
    assert {p[0] for p in buf.parts} <= {core_m, shell_m, sprig_m}
    core = [p for p in buf.parts if p[0] == core_m][-1][1]
    # The rounded shoulder also covers corner vertices outside the flat top's
    # footprint. Test the actual complete leaf shell, not only its top cap.
    triangles = np.concatenate([vertices[indices] for material, vertices, indices in buf.parts
                                if material == shell_m])
    a, b, c = (triangles[:, i, :2] for i in range(3))
    ab, ac = b-a, c-a
    ap = core[:, None, :2]-a[None, :, :]
    cross = lambda x, y: x[..., 0]*y[..., 1]-x[..., 1]*y[..., 0]
    den = cross(ab, ac)
    valid = abs(den) > 1e-10
    w1 = cross(ap, ac)/np.where(valid, den, 1)
    w2 = cross(ab, ap)/np.where(valid, den, 1)
    w0 = 1-w1-w2
    inside = valid & (w0 >= -1e-7) & (w1 >= -1e-7) & (w2 >= -1e-7)
    heights = w0*triangles[:, 0, 2]+w1*triangles[:, 1, 2]+w2*triangles[:, 2, 2]
    surface = np.where(inside, heights, -np.inf).max(axis=1)
    assert np.isfinite(surface).all(), "core top must lie inside the leaf shell footprint"
    assert np.max(core[:, 2]-surface) <= .005, "opaque core pokes through the leaf top"
