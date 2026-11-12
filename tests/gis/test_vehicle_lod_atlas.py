"""ADR0153: consolidation must preserve geometry and surface parameters."""
import numpy as np
import pytest
from PIL import Image

from streetscape import life_cars as cars
from streetscape import life_props as yard
from streetscape import vehicle_lod_atlas as atlas
from streetscape.export import crease_normals
from streetscape.materials import M


@pytest.mark.parametrize("name,build", [
    ("car_hatch_white", lambda: cars.car("hatch", "white")),
    ("car_suv_black", lambda: cars.car("suv", "black")),
    ("van_white", lambda: cars.van("white")),
    ("tractor_white", lambda: yard.tractor("white")),
    ("trailer_curtain_0", lambda: yard.trailer("curtain", "grey")),
    ("trailer_reefer_0", lambda: yard.trailer("reefer", None)),
])
def test_two_submeshes_preserve_positions_normals_and_triangles(name, build):
    levels = build()
    for mesh in [levels[1]] + list(levels[3:]):
        before = crease_normals(mesh.out())
        after = atlas.consolidate(before, name)
        assert len(after) <= 2
        keep = atlas.primary(name)
        assert next(p for p in after if p["mat"] == keep) is next(p for p in before if p["mat"] == keep)
        source = [p for p in before if p["mat"] != keep]
        target = next(p for p in after if p["mat"] == atlas.NAME)
        for attr in ("V", "N"):
            np.testing.assert_array_equal(target[attr], np.concatenate([p[attr] for p in source]))
        original_triangles = np.concatenate([p["V"][p["T"]] for p in source])
        np.testing.assert_array_equal(target["V"][target["T"]], original_triangles)
        assert np.isfinite(target["UV"]).all()
        assert (target["UV"] >= 0).all() and (target["UV"] <= 1).all()


def test_atlas_keeps_linear_albedo_metallic_and_smoothness(tmp_path):
    dest = atlas.generate(tmp_path)
    base = np.asarray(Image.open(dest / f"{atlas.NAME}_BaseColor.png")) / 255
    mask = np.asarray(Image.open(dest / f"{atlas.NAME}_MaskMap.png")) / 255
    for name in atlas.DETAILS:
        u, v = atlas.center(name)
        x, y = int(u * 1024), 511 - int(v * 512)
        rgb = base[y, x]
        linear = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
        np.testing.assert_allclose(linear, M[name]["color"], atol=.004)
        source_metal = M[name].get("metal", 0)
        assert mask[y, x, 0] == pytest.approx(source_metal if source_metal > .5 else 0, abs=1/255)
        assert mask[y, x, 3] == pytest.approx(1 - M[name]["rough"], abs=1/255)


def test_refrigeration_grille_keeps_60mm_stripes_and_source_smoothness(tmp_path):
    dest = atlas.generate(tmp_path)
    base = np.asarray(Image.open(dest / f"{atlas.NAME}_BaseColor.png")) / 255
    mask = np.asarray(Image.open(dest / f"{atlas.NAME}_MaskMap.png")) / 255
    sample = base[264:376, 512, 0]
    linear = np.where(sample <= .04045, sample/12.92, ((sample+.055)/1.055)**2.4)
    assert linear.min() == pytest.approx(.012, abs=.001)
    assert linear.max() == pytest.approx(.085, abs=.002)
    # 0.78 m / 0.06 m = 13 authored periods, two boundaries each.
    assert np.count_nonzero(np.diff(linear > .04)) == 26
    assert mask[300, 512, 3] == pytest.approx(.45, abs=1/255)
    source = crease_normals(yard.trailer('reefer', None)[1].out())
    result = atlas.consolidate(source, 'trailer_reefer_0')
    old = next(p for p in source if p['mat'] == 'reefer_grille')
    detail = next(p for p in result if p['mat'] == atlas.NAME)
    # The rectangle spans atlas UV, unlike the solid palette cells.
    index = next(i for i,p in enumerate([p for p in source if p['mat'] != atlas.primary('trailer_reefer_0')]) if p is old)
    offset = sum(len(p['V']) for p in [p for p in source if p['mat'] != atlas.primary('trailer_reefer_0')][:index])
    assert np.all(np.ptp(detail['UV'][offset:offset+len(old['V'])],axis=0) > .1)


