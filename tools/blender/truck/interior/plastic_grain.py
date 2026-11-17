"""D84: cab plastic detail maps as a synthesised injection-moulding stipple (no scan, no photo).

The former plastic profile was an emboss derived from the Poly Haven brown_leather scan; from the driver's eye on PC
High it read as creased leather on every moulded part (dash top, A-pillar trim, door cards). Moulded cab plastics
carry an isotropic spark-eroded grain without creases or pores, so the maps are generated here:
a band-limited stipple (0.25-0.6 mm features on the 0.10 m tile) plus a very low mould-flow mottle.

    uv run --project tools/worldgen python tools/blender/truck/interior/plastic_grain.py --output art-source/truck/interior/export/textures

Writes T_Cab_Plastic_Detail.png (R albedo variation, G micro AO, B roughness deviation, A preserved from the existing
map) and T_Cab_Plastic_Normal.png for High 1024 / Medium 512 / Low 256, plus conversion-plastic.json.
Parameters come from cab_material_scans.json "plastic" (mode "procedural_stipple"); all WORKING_VALUE, judged on the
cab-grain / cab-materials / cab-dash control cameras.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
CONFIG = ROOT / 'art-source/truck/interior/cab_material_scans.json'
SEED = 20261116


def fnoise(rng, n, f_lo, f_hi):
    """Periodic band-limited noise in [0,1]; f in cycles per tile (same construction as make_textures.fnoise)."""
    spectrum = np.fft.fft2(rng.standard_normal((n, n)))
    fy = np.fft.fftfreq(n)[:, None] * n
    fx = np.fft.fftfreq(n)[None, :] * n
    r = np.sqrt(fx * fx + fy * fy) + 1e-6
    band = np.exp(-((np.log(r) - np.log(math.sqrt(f_lo * f_hi))) ** 2) / (2 * (math.log(f_hi / f_lo) / 2.5) ** 2))
    out = np.real(np.fft.ifft2(spectrum * band))
    out -= out.min()
    return out / max(out.max(), 1e-9)


def normal_from_height(height, strength):
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * .5 * strength
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * .5 * strength
    n = np.stack([-dx, dy, np.ones_like(height)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True) * .5 + .5


def renormalise(encoded):
    v = encoded * 2 - 1
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-6) * .5 + .5


def image8(array):
    from PIL import Image
    return Image.fromarray(np.rint(np.clip(array, 0, 1) * 255).astype(np.uint8))


def prepare(output, entry, alpha_source):
    from PIL import Image
    n = 1024
    rng = np.random.default_rng(SEED)
    tile_mm = entry['tile_metres'] * 1000.0
    lo, hi = entry['stipple_feature_mm']
    stipple = fnoise(rng, n, tile_mm / hi, tile_mm / lo)          # cycles per tile for the feature-size band
    mottle = fnoise(rng, n, 3, 9)                                 # mould-flow mottle, centimetres
    # D84 polish: from the driver's eye one 1080p pixel covers ~0.9 mm of dash (0.8 m, 62 deg vertical FOV), so the
    # 0.25-0.6 mm stipple alone is sub-pixel and the mip chain averages it to a flat sheet (review P1-2). The moulded
    # grain that reads from the seat is the coarser pebble (grain_feature_mm) and the cm-scale gloss patches; the fine
    # stipple stays as the close-up layer.
    g_lo, g_hi = entry.get('grain_feature_mm', [lo, hi])
    gw = entry.get('grain_weight', 0.0)
    grain = fnoise(rng, n, tile_mm / g_hi, tile_mm / g_lo)
    grain = np.clip((grain - .5) * 1.6 + .5, 0, 1) ** 1.25        # flattened pebble tops, narrower valleys
    gloss = fnoise(rng, n, 1, 4)                                  # 2.5-10 cm handling / cleaning gloss patches
    stipple = (1 - gw) * stipple + gw * grain
    pw = entry.get('gloss_patch_weight', 0.0)
    mottle = (1 - pw) * mottle + pw * gloss
    height = stipple
    # Packing as cc0_leather.prepare: shader albedo = tint * (0.7 + 0.6 * R), roughness = authored + (B - 0.5) * 0.6.
    ratio = 1 + (stipple - stipple.mean()) * entry['variation_gain'] + (mottle - .5) * entry['mottle_gain']
    variation = (np.clip(ratio, .72, 1.28) - .7) / .6
    micro_ao = np.clip(1 - (1 - stipple) * entry['ao_gain'] * .5, 0, 1)
    roughness = np.clip(.5 + ((stipple - stipple.mean()) * entry['roughness_gain'] + (mottle - .5) * entry.get('roughness_mottle_gain', entry['mottle_gain'])) / .6, 0, 1)
    detail = np.stack((variation, micro_ao, roughness), -1)
    normal = normal_from_height(height, entry['normal_strength'] * 4.0)
    old_alpha = Image.open(alpha_source).convert('RGBA').getchannel('A')
    alpha_sha = hashlib.sha256(old_alpha.tobytes()).hexdigest()
    outputs = []
    for tier, size in (('High', 1024), ('Medium', 512), ('Low', 256)):
        folder = Path(output) / tier
        folder.mkdir(parents=True, exist_ok=True)
        packed = image8(detail).resize((size, size), Image.Resampling.LANCZOS).convert('RGBA')
        packed.putalpha(old_alpha.resize((size, size), Image.Resampling.LANCZOS))
        packed.save(folder / 'T_Cab_Plastic_Detail.png')
        resized = np.asarray(image8(normal).resize((size, size), Image.Resampling.LANCZOS), dtype=np.float32) / 255
        image8(renormalise(resized)).save(folder / 'T_Cab_Plastic_Normal.png')
        outputs.append({'tier': tier, 'pixels': size})
    slope = np.degrees(np.arctan(np.hypot(*(normal[..., :2] * 2 - 1).transpose(2, 0, 1)) / np.maximum(normal[..., 2] * 2 - 1, 1e-6)))
    metadata = {
        'status': 'procedural; not a scan',
        'profile': 'plastic', 'mode': 'procedural_stipple', 'seed': SEED,
        'tile_metres': entry['tile_metres'], 'stipple_feature_mm': [lo, hi],
        'working_values': {k: entry[k] for k in ('variation_gain', 'roughness_gain', 'ao_gain', 'normal_strength', 'mottle_gain', 'grain_feature_mm', 'grain_weight',
                                                    'gloss_patch_weight', 'roughness_mottle_gain') if k in entry},
        'normal_slope_deg': {'median': float(np.median(slope)), 'p95': float(np.percentile(slope, 95))},
        'perforation_alpha_pixels_sha256': alpha_sha,
        'outputs': outputs,
    }
    (Path(output) / 'conversion-plastic.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=CONFIG)
    parser.add_argument('--alpha-source', type=Path)
    opts = parser.parse_args()
    entry = json.loads(opts.config.read_text(encoding='utf-8-sig'))['plastic']
    if entry.get('mode') != 'procedural_stipple':
        raise ValueError('plastic.mode is not procedural_stipple in ' + str(opts.config))
    alpha = opts.alpha_source or opts.output / 'High/T_Cab_Plastic_Detail.png'
    prepare(opts.output, entry, alpha)


if __name__ == '__main__':
    main()
