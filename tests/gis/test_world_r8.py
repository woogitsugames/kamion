"""Review r7 N-2 / N-4 (ADR 0060): dark accents (sky occlusion data, ground grime) and the clipped berberis band.

Unit tests run without raw data; output tests read the generated files of the last build_world.py run."""

from __future__ import annotations

import json

import numpy as np
import pytest

from conftest import REGION_DIR


def _manifest():
    p = REGION_DIR / "generated" / "world_manifest.json"
    if not p.exists():
        pytest.skip("world_manifest.json missing: run roads/build_world.py")
    m = json.loads(p.read_text(encoding="utf-8"))
    return m.get("materials", m)


def test_berberis_band_is_narrow_and_low():
    """A wide traced bed becomes a 1.1-1.4 m clipped band 0.5-0.65 m high (r7 N-4: 'narrow strip', not a sofa)."""
    from shapely.geometry import Polygon
    from roads.meshing import MeshBuf
    from streetscape import plantings as PT
    bed = Polygon([(0, 0), (20, 0), (21, 3), (19, 6.5), (1, 6.8), (-1, 3)])
    band = PT.band_of(bed, 1.25)
    w = 2 * band.area / band.length
    assert 1.0 < w < 1.45 and band.length > 2 * 17.0          # long (full bed length), narrow
    assert bed.buffer(1e-6).contains(band)
    narrow = Polygon([(0, 0), (10, 0), (10, 1.0), (0, 1.0)])
    assert PT.band_of(narrow, 1.25).equals(narrow)              # already narrower: kept
    buf = MeshBuf()
    PT.hedge_mass(buf, band, lambda e, n: np.zeros(len(np.atleast_1d(e))), ("band",))
    shell = np.vstack([p.V for p in buf.parts if p.mat == "hedge_shell_berberis"])
    assert PT.HEDGE_H[0] - 0.05 <= shell[:, 2].max() <= PT.HEDGE_H[1] + 0.05
    assert PT.HEDGE_H == (0.5, 0.65)


def test_berberis_texture_has_lighter_tips():
    """Copper shoot tips above the cut: the sprig atlas' upper leaves are lighter than the shell's mean leaf."""
    from streetscape import hedge_textures as HT
    tx = HT.textures()
    sh = np.asarray(tx["hedge_shell_berberis"], float)
    leaf = sh[..., 3] > 127
    lum = (0.2126 * sh[..., 0] + 0.7152 * sh[..., 1] + 0.0722 * sh[..., 2])[leaf]
    assert np.percentile(lum, 95) > 1.6 * np.percentile(lum, 50)          # spread: tips vs body (sigma in the mask)
    assert np.percentile(lum, 10) < 0.75 * np.percentile(lum, 50)         # dark inner leaves


def test_sky_occlusion_material_data():
    """sky_occ on structures and glazing, never on cars, ground, decals or vegetation (ADR 0060)."""
    from streetscape.materials import M
    assert M["glass"]["sky_occ"] == [0.0, 0.6]
    assert M["canopy_steel"]["sky_occ"][0] > 0.3
    assert M["plaster_light__far_office"]["sky_occ"][1] > 0.3
    for k, v in M.items():
        if k.startswith(("car_", "hedge_", "decal_", "collision_")) or v.get("surface") in ("grass", "asphalt", "paving_stones"):
            assert "sky_occ" not in v, k
    for k in ("bridge_soffit", "bridge_concrete"):
        so = _manifest()[k]["sky_occ"]
        assert 0.3 <= so[0] <= 0.7 and so[1] == 0.0


def test_ground_grime_keyword_in_shader():
    """The engine side exists: WorldPBR _GRIME / _DripBand / _SkyOcc, Vegetation _CrownShade (ADR 0060)."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[2] / "game" / "Assets" / "_Project"
    pbr = (root / "Environment" / "Shaders" / "WorldPBR.shader").read_text(encoding="utf-8")
    assert "shader_feature_local _GRIME" in pbr and "_DripBand" in pbr and "_SkyOcc" in pbr
    veg = (root / "Rendering" / "Shaders" / "Vegetation.shader").read_text(encoding="utf-8")
    assert "_CrownShade" in veg
    imp = (root / "World" / "Import" / "WorldPbrMaterials.cs").read_text(encoding="utf-8")
    assert 'EnableKeyword("_GRIME")' in imp
