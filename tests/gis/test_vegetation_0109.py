"""Ground-cover context regressions: a road verge is not automatically a lawn."""
from types import SimpleNamespace

import numpy as np
from shapely.geometry import box, mapping

from streetscape.vegetation import ground_masks


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
