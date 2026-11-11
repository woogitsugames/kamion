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


def config_args(output, alpha, config=CONFIG, fetch=False):
    document = json.loads(Path(config).read_text(encoding='utf-8-sig'))
    if document['schema'] != 1:
        raise ValueError('Unsupported cab scan schema')
    entry = document['leather']
    raw = ROOT / 'art-source/truck/interior/cc0/_raw' / entry['asset']
    args = argparse.Namespace(output=Path(output), preserve_alpha=Path(alpha),
                              source_metres=entry['source_metres'], tile_metres=entry['tile_metres'],
                              rim_uv_scale=entry['wheel_authored_tile_metres'] / entry['tile_metres'])
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
    entry = json.loads(CONFIG.read_text(encoding='utf-8-sig'))['leather']
    if not entry['enabled']:
        return
    args, _ = config_args(output, Path(output) / 'High/T_Cab_Leather_Detail.png')
    prepare(args)
    print('CAB_CC0 leather=brown_leather maps=verified fallback=False')


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


def unit_normals(encoded):
    vectors = encoded * 2 - 1
    lengths = np.linalg.norm(vectors, axis=-1, keepdims=True)
    if np.any(lengths < .1):
        raise ValueError('Invalid normal vector after resampling')
    return vectors / lengths * .5 + .5


def image8(array):
    return Image.fromarray(np.rint(np.clip(array, 0, 1) * 255).astype(np.uint8))


def prepare(args):
    if not 0 < args.tile_metres <= args.source_metres:
        raise ValueError('Tile must fit the physical source field')
    files = {role: getattr(args, role) for role in ('diffuse', 'normal', 'roughness', 'ao')}
    images = {role: Image.open(path).convert('RGB' if role in ('diffuse', 'normal') else 'L') for role, path in files.items()}
    shape = images['diffuse'].size
    if shape[0] != shape[1] or any(image.size != shape for image in images.values()):
        raise ValueError('Registered, square source maps of identical size required')
    pixels = round(shape[0] * args.tile_metres / args.source_metres)
    if pixels < 32:
        raise ValueError('Physical crop too small for reliable detail')
    start = (shape[0] - pixels) // 2
    box = (start, start, start + pixels, start + pixels)
    crops = {role: np.asarray(image.crop(box).resize((1024, 1024), Image.Resampling.LANCZOS), dtype=np.float32) / 255 for role, image in images.items()}
    rgb = crops['diffuse']
    linear = np.where(rgb <= .04045, rgb / 12.92, ((rgb + .055) / 1.055) ** 2.4)
    luminance = linear @ np.array([.2126, .7152, .0722], dtype=np.float32)
    # Preserve the existing trim colour. Source diffuse contributes neutral variation, not brown tint.
    ratio = np.clip(luminance / max(float(np.median(luminance)), 1e-6), .8, 1.2)
    variation = (ratio - .7) / .6  # inverse of the current shader's 0.7 + 0.6 * detail.r
    rough_median = float(np.median(crops['roughness']))
    roughness = np.clip(.5 + (crops['roughness'] - rough_median) / .6, 0, 1)
    # Keep authored vertex roughness; convert only variation to the shader's gain of 0.6.
    detail = periodic_edges(np.stack((variation, crops['ao'], roughness), -1))
    normal = unit_normals(periodic_edges(crops['normal']))
    old_alpha = Image.open(args.preserve_alpha).convert('RGBA').getchannel('A')
    args.output.mkdir(parents=True, exist_ok=True)
    outputs = []
    for tier, size in (('High', 1024), ('Medium', 512), ('Low', 256)):
        folder = args.output / tier
        folder.mkdir(exist_ok=True)
        packed = image8(detail).resize((size, size), Image.Resampling.LANCZOS).convert('RGBA')
        packed.putalpha(old_alpha.resize((size, size), Image.Resampling.LANCZOS))
        packed.save(folder / 'T_Cab_Leather_Detail.png')
        resized = np.asarray(image8(normal).resize((size, size), Image.Resampling.LANCZOS), dtype=np.float32) / 255
        image8(unit_normals(resized)).save(folder / 'T_Cab_Leather_Normal.png')
        outputs.append({'tier': tier, 'pixels': size, 'detail': str(folder / 'T_Cab_Leather_Detail.png'), 'normal': str(folder / 'T_Cab_Leather_Normal.png')})
    metadata = {
        'status': 'candidate; inspect before integration',
        'source_metres': args.source_metres, 'requested_tile_metres': args.tile_metres,
        'actual_crop_metres': pixels / shape[0] * args.source_metres,
        'crop_pixels': pixels, 'source_pixels': shape, 'crop_box': box,
        'edge_crossfade_fraction': .06, 'scan_roughness_median': rough_median,
        'mapping_limits': '12 cm upholstery crop. Authored wheel UV uses 5 cm; requires the flagged Unity rim UV correction, verified separately in builder logs. Source-only previews retain the authored wheel scale. No claim of a scanned dashboard plastic.',
        'required_unity_rim_uv_scale': args.rim_uv_scale,
        'perforation_alpha_source': str(args.preserve_alpha),
        'perforation_alpha_source_sha256': hashlib.sha256(args.preserve_alpha.read_bytes()).hexdigest(),
        'sources': {role: {'file': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for role, path in files.items()},
        'outputs': outputs,
    }
    (args.output / 'conversion.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=CONFIG)
    parser.add_argument('--alpha-source', type=Path, default=ROOT / 'art-source/truck/interior/export/textures/High/T_Cab_Leather_Detail.png')
    parser.add_argument('--fetch', action='store_true')
    opts = parser.parse_args()
    args, _ = config_args(opts.output, opts.alpha_source, opts.config, opts.fetch)
    prepare(args)


if __name__ == '__main__':
    main()
