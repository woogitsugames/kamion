"""Physical-scale CC0 leather conversion for the existing cab packed-map contract.

Run under the heavy pool. Physical centre crop of a CC0 scan; no invented scan data.
Keeps existing packed-map sizes, vertex tint/base roughness and perforation contract.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlretrieve

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
CONFIG = ROOT / 'art-source/truck/interior/cab_material_scans.json'


def config_args(output, alpha, config=CONFIG, fetch=False, profile='leather'):
    document = json.loads(Path(config).read_text(encoding='utf-8-sig'))
    if document['schema'] != 1:
        raise ValueError('Unsupported cab scan schema')
    entry = document[profile]
    raw = ROOT / 'art-source/truck/interior/cc0/_raw' / entry['asset']
    args = argparse.Namespace(output=Path(output), preserve_alpha=Path(alpha), profile=profile,
                              source_metres=entry['source_metres'], tile_metres=entry['tile_metres'],
                              source_crop_metres=entry.get('source_crop_metres', entry['tile_metres']),
                              rim_uv_scale=entry.get('wheel_authored_tile_metres', entry['tile_metres']) / entry['tile_metres'],
                              variation_gain=entry.get('variation_gain', 1.0), roughness_gain=entry.get('roughness_gain', 1.0),
                              ao_gain=entry.get('ao_gain', 1.0), normal_strength=entry.get('normal_strength', 1.0))
    for role, item in entry['maps'].items():
        path = raw / item['file']
        if not path.exists() and fetch:
            raw.mkdir(parents=True, exist_ok=True)
            part = path.with_suffix(path.suffix + '.part')
            urlretrieve(item['url'], part)
            if part.stat().st_size != item['bytes'] or hashlib.md5(part.read_bytes()).hexdigest() != item['md5']:
                raise ValueError('Downloaded source checksum mismatch: ' + role)
            part.replace(path)
        if not path.exists():
            raise FileNotFoundError(str(path) + '; prepare with --fetch, no procedural fallback')
        if path.stat().st_size != item['bytes'] or hashlib.md5(path.read_bytes()).hexdigest() != item['md5']:
            raise ValueError('Source checksum mismatch: ' + str(path))
        setattr(args, role, path)
    return args, entry


def apply_runtime_maps(output):
    """Called by the cab exporter; an enabled scan must be available and verified."""
    document = json.loads(CONFIG.read_text(encoding='utf-8-sig'))
    for profile in ('leather', 'plastic'):
        entry = document.get(profile)
        if not entry or not entry['enabled']:
            continue
        args, _ = config_args(output, Path(output) / f'High/T_Cab_{profile.title()}_Detail.png', profile=profile)
        prepare(args)
        print(f'CAB_CC0 profile={profile} source=brown_leather maps=verified fallback=False')


def periodic_edges(array, fraction=.06):
    """Crossfade opposite edge strips; this changes the scan only near tile boundaries."""
    out = array.copy()
    for axis in (0, 1):
        view = np.moveaxis(out, axis, 0)
        width = max(2, round(view.shape[0] * fraction))
        for i in range(width):
            weight = .5 * (1 + np.cos(np.pi * i / (width - 1)))
            lo, hi = view[i].copy(), view[-1-i].copy()
            midpoint = (lo + hi) * .5
            view[i] = lo * (1 - weight) + midpoint * weight
            view[-1-i] = hi * (1 - weight) + midpoint * weight
    return out


def unit_normals(encoded, strength=1.0):
    vectors = encoded * 2 - 1
    vectors[..., :2] *= strength
    lengths = np.linalg.norm(vectors, axis=-1, keepdims=True)
    if np.any(lengths < .1):
        raise ValueError('Invalid normal vector after resampling')
    return vectors / lengths * .5 + .5


def image8(array):
    return Image.fromarray(np.rint(np.clip(array, 0, 1) * 255).astype(np.uint8))


def prepare(args):
    if not 0 < args.source_crop_metres <= args.source_metres or not args.tile_metres > 0:
        raise ValueError('Tile must fit the physical source field')
    files = {role: getattr(args, role) for role in ('diffuse', 'normal', 'roughness', 'ao')}
    images = {role: Image.open(path).convert('RGB' if role in ('diffuse', 'normal') else 'L') for role, path in files.items()}
    shape = images['diffuse'].size
    if shape[0] != shape[1] or any(image.size != shape for image in images.values()):
        raise ValueError('Registered, square source maps of identical size required')
    pixels = round(shape[0] * args.source_crop_metres / args.source_metres)
    if pixels < 32:
        raise ValueError('Physical crop too small for reliable detail')
    start = (shape[0] - pixels) // 2
    box = (start, start, start + pixels, start + pixels)
    crops = {role: np.asarray(image.crop(box).resize((1024, 1024), Image.Resampling.LANCZOS), dtype=np.float32) / 255 for role, image in images.items()}
    rgb = crops['diffuse']
    linear = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    luminance = linear @ np.array([.2126, .7152, .0722], dtype=np.float32)
    # Preserve the existing trim colour. Source diffuse contributes neutral variation, not brown tint.
    ratio = np.clip(1 + (luminance / max(float(np.median(luminance)), 1e-6) - 1) * args.variation_gain, .8, 1.2)
    variation = (ratio - .7) / .6  # inverse of the current shader's 0.7 + 0.6 * detail.r
    rough_median = float(np.median(crops['roughness']))
    roughness = np.clip(.5 + (crops['roughness'] - rough_median) * args.roughness_gain / .6, 0, 1)
    # Keep authored vertex roughness; convert only variation to the shader's gain of 0.6.
    micro_ao = 1 + (crops['ao'] - 1) * args.ao_gain
    detail = periodic_edges(np.stack((variation, micro_ao, roughness), -1))
    normal = unit_normals(periodic_edges(crops['normal']), args.normal_strength)
    old_alpha = Image.open(args.preserve_alpha).convert('RGBA').getchannel('A')
    args.output.mkdir(parents=True, exist_ok=True)
    outputs = []
    for tier, size in (('High', 1024), ('Medium', 512), ('Low', 256)):
        folder = args.output / tier
        folder.mkdir(exist_ok=True)
        packed = image8(detail).resize((size, size), Image.Resampling.LANCZOS).convert('RGBA')
        packed.putalpha(old_alpha.resize((size, size), Image.Resampling.LANCZOS))
        prefix = 'T_Cab_' + args.profile.title()
        packed.save(folder / (prefix + '_Detail.png'))
        resized = np.asarray(image8(normal).resize((size, size), Image.Resampling.LANCZOS), dtype=np.float32) / 255
        image8(unit_normals(resized)).save(folder / (prefix + '_Normal.png'))
        outputs.append({'tier': tier, 'pixels': size, 'detail': str(folder / (prefix + '_Detail.png')), 'normal': str(folder / (prefix + '_Normal.png'))})
    metadata = {
        'status': 'candidate; inspect before integration',
        'profile': args.profile,
        'source_metres': args.source_metres, 'requested_tile_metres': args.tile_metres,
        'requested_source_crop_metres': args.source_crop_metres, 'grain_xy_scale': args.tile_metres / args.source_crop_metres,
        'actual_crop_metres': pixels / shape[0] * args.source_metres,
        'crop_pixels': pixels, 'source_pixels': shape, 'crop_box': box,
        'edge_crossfade_fraction': .06, 'scan_roughness_median': rough_median,
        'mapping_limits': ('12 cm upholstery crop. Authored wheel UV uses 5 cm; requires the flagged Unity rim UV correction, verified separately in builder logs. Source-only previews retain the authored wheel scale.' if args.profile == 'leather' else
                           'Derivative emboss pattern based on a leather scan, not a scanned plastic part. Source crop and game tile intentionally differ; this is an authored working value for moulded grain.'),
        'required_unity_rim_uv_scale': args.rim_uv_scale,
        'working_values': {key: getattr(args, key) for key in ('variation_gain', 'roughness_gain', 'ao_gain', 'normal_strength')},
        'perforation_alpha_source': str(args.preserve_alpha),
        'perforation_alpha_source_sha256': hashlib.sha256(args.preserve_alpha.read_bytes()).hexdigest(),
        'sources': {role: {'file': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for role, path in files.items()},
        'outputs': outputs,
    }
    meta_name = 'conversion.json' if args.profile == 'leather' else 'conversion-plastic.json'
    (args.output / meta_name).write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=CONFIG)
    parser.add_argument('--profile', choices=('leather', 'plastic'), default='leather')
    parser.add_argument('--alpha-source', type=Path)
    parser.add_argument('--fetch', action='store_true')
    opts = parser.parse_args()
    alpha = opts.alpha_source or ROOT / f'art-source/truck/interior/export/textures/High/T_Cab_{opts.profile.title()}_Detail.png'
    args, _ = config_args(opts.output, alpha, opts.config, opts.fetch, opts.profile)
    prepare(args)


if __name__ == '__main__':
    main()
