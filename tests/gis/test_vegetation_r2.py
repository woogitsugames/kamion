"""ADR0088: shape / stable card LOD / licensed bark fallback contracts."""
import math
from pathlib import Path
import numpy as np

from streetscape.foliage_policy import crown_opening, leaf_lod_indices, metric_patch_field, osm_tree_species
from streetscape.leaf_textures import pine_scan
from streetscape.vegetation_metrics import foliage_mask
from streetscape.pine_needles import needle_card


def test_canopy_has_coherent_openings_and_retains_stem_foliage():
    angles = np.linspace(0, 2 * math.pi, 360, endpoint=False)
    gaps = np.array([crown_opening((4*math.cos(a), 4*math.sin(a), 0), (0, 0, 0), 15, 0) for a in angles])
    assert .10 < gaps.mean() < .40
    # Neighbouring leaves form actual windows rather than a salt-and-pepper mask.
    assert np.count_nonzero(gaps != np.roll(gaps, 1)) == 4
    assert not crown_opening((.1, .1, 0), (0, 0, 0), 15, 0)


def test_lod_leaf_subset_is_deterministic_and_budgeted():
    a, b = leaf_lod_indices(1000, 48), leaf_lod_indices(1000, 48)
    np.testing.assert_array_equal(a, b)
    assert 330 < len(a) < 470
    assert np.all(np.diff(a) > 0) and 0 <= a.min() < a.max() < 1000
    assert len(leaf_lod_indices(1000, 48, maximum=140)) == 140
    assert len(leaf_lod_indices(1000, 48, maximum=0)) == 0


def test_cc0_bark_clean_clone_fallback_stays_useful(tmp_path, caplog):
    image = pine_scan(root=tmp_path, n=64)
    assert image.size == (64, 64)
    assert np.asarray(image)[..., :3].std() > 2
    assert 'procedural bark retained' in caplog.text


def test_cc0_needles_missing_or_unapproved_source_falls_back(tmp_path, caplog):
    assert needle_card(root=tmp_path) is None
    assert 'procedural needles retained' in caplog.text


def test_cc0_needles_red_alpha_and_atlas_padding_are_not_opaque_cards(tmp_path):
    import hashlib
    import json
    from PIL import Image, ImageDraw
    raw = tmp_path / 'art-source/world/cc0/_raw/pine_tree_01'
    raw.mkdir(parents=True)
    color = Image.new('RGB', (1024, 1024), (72, 94, 52))
    alpha = Image.new('RGB', (1024, 1024));draw = ImageDraw.Draw(alpha)
    # Connected twig + needles, and separate unwanted white atlas padding.
    draw.line((130, 440, 130, 45), fill=(255, 0, 0), width=9)
    for y in range(65, 350, 25):
        draw.line((45, y-20, 130, y+35, 200, y-20), fill=(255, 0, 0), width=5)
    draw.rectangle((205, 26, 220, 75), fill=(255, 0, 0))
    files=[]
    for channel,image in [('diffuse',color),('alpha',alpha)]:
        path=raw/(channel+'.png');image.save(path)
        files.append({'map':channel,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest={'raw_dir':str(raw.relative_to(tmp_path)),'files':files,'crop_xyxy':[5,26,220,450],
              'covered_mean_linear_luminance_WORKING_VALUE':.064}
    (raw.parents[1]/'pine_needles_manifest.json').write_text(json.dumps(manifest))
    image=needle_card(n=128,root=tmp_path);assert image is not None
    a=np.array(image);assert .03 < (a[...,3]>127).mean() < .45
    # Alpha must use R, not RGB luminance (red-only source still reaches255).
    assert a[...,3].max()==255
    (raw/'alpha.png').write_bytes(b'tampered')
    assert needle_card(n=128,root=tmp_path) is None


def test_metric_patches_are_world_anchored_without_chunk_seams():
    east, north = np.arange(-30., 31), np.arange(45., -16., -1)
    full = metric_patch_field(east, north)
    piece = metric_patch_field(east[13:43], north[7:27])
    np.testing.assert_array_equal(piece, full[7:27, 13:43])
    assert .05 < full.std() < .35 and 0 <= full.min() <= full.max() <= 1
    # No leaf-size salt noise: adjacent one-metre samples vary smoothly.
    assert np.abs(np.diff(full, axis=1)).mean() < .12


def test_explicit_osm_botany_is_not_replaced_by_generic_linden():
    assert osm_tree_species({'genus': 'Betula'}) == 'birch'
    assert osm_tree_species({'species': 'Pinus sylvestris'}) == 'pine'
    assert osm_tree_species({'species:pl': 'lipa drobnolistna'}) == 'linden'
    assert osm_tree_species({'natural': 'tree'}) == 'linden'


def test_crown_mask_retains_crushed_foliage_and_excludes_sky_bark():
    pixels = np.array([[[45, 65, 35], [8, 8, 8], [205, 215, 230], [90, 75, 61]]], dtype=np.uint8)
    assert foliage_mask(pixels).tolist() == [[True, True, False, False]]
