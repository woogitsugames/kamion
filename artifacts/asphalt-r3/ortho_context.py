"""Small optional geographic context; execute only inside the SurfaceAudit heavy slot.

Reads a bounded, downsampled GeoTIFF window. This is not camera fitting or a material classifier.
"""
import hashlib
import json
import os
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]


def generate():
    target = OUT / 'reference/ortho-context.json'
    image_path = OUT / 'reference/ortho-context-preview.png'
    source = ROOT / 'Data/raw/derived/bialystok-industrial-c/ortho_0p25m.tif'
    report = dict(status='unavailable', source=str(source.relative_to(ROOT)),
                  requested_local_en=[230, -590, 500, -260],
                  note='Optional geographic context only. Acquisition date and photo3 pose remain unverified. '
                       'Downsampled imagery is not a measurement of albedo/roughness or proof of paving block type.')
    try:
        os.environ['GDAL_NUM_THREADS'] = '1'
        import numpy as np
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.windows import from_bounds, bounds
        from PIL import Image

        manifest_path = ROOT / 'Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
        manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
        receipt = json.loads((OUT / 'baseline-producer-progress.json').read_text(encoding='utf-8-sig'))
        manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        if not receipt['complete'] or receipt['manifest_sha256'].lower() != manifest_sha:
            raise ValueError('Fresh baseline source receipt required')
        origin = manifest['origin_epsg2180']
        with rasterio.Env(GDAL_CACHEMAX=64 * 1024 * 1024, GDAL_NUM_THREADS='1'):
            with rasterio.open(source) as dataset:
                if dataset.crs.to_epsg() != 2180 or dataset.count < 3 or any(t != 'uint8' for t in dataset.dtypes[:3]):
                    raise ValueError('Expected EPSG2180 RGB uint8 source; no silent color/CRS conversion')
                window = from_bounds(origin['x'] + 230, origin['y'] - 590,
                                     origin['x'] + 500, origin['y'] - 260, dataset.transform)
                if (window.col_off < 0 or window.row_off < 0 or window.col_off + window.width > dataset.width
                        or window.row_off + window.height > dataset.height):
                    raise ValueError('Requested context is outside the source raster')
                scale = min(960 / window.width, 960 / window.height, 1)
                width, height = max(1, round(window.width * scale)), max(1, round(window.height * scale))
                rgb = dataset.read((1, 2, 3), window=window, out_shape=(3, height, width), resampling=Resampling.bilinear)
                valid = dataset.read_masks(1, window=window, out_shape=(height, width), resampling=Resampling.nearest)
                Image.fromarray(np.moveaxis(rgb, 0, -1)).save(image_path)
                report.update(status='available', source_crs=str(dataset.crs), source_resolution=list(dataset.res),
                              source_dimensions=[dataset.width, dataset.height], native_window=list(window.flatten()),
                              bounds_epsg2180=list(bounds(window, dataset.transform)), preview_dimensions=[width, height],
                              valid_fraction=float(np.count_nonzero(valid) / valid.size),
                              resampling='bilinear, max960px, no photometric adjustment', manifest_sha256=manifest_sha)
        report.update(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                      preview=str(image_path.relative_to(ROOT)), preview_sha256=hashlib.sha256(image_path.read_bytes()).hexdigest())
    except Exception as error:
        report.update(status='unavailable', error_type=type(error).__name__, error=str(error)[:500])
    target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return dict(ortho_context=report['status'], sidecar=str(target.relative_to(ROOT)))


if __name__ == '__main__':
    print(json.dumps(generate()))
