"""Measure display luma in projected road wheel/centre fields, with inspectable masks."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT / 'artifacts/surface-wear-r1'))
from bus_world_proof import read


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--after', default='candidate2')
    parser.add_argument('--condition', action='append')
    args = parser.parse_args()
    camera = 'd_wear_lane_old'
    spec = next(c for c in json.loads((OUT / 'cameras.json').read_text(encoding='utf-8-sig'))['cameras'] if c['id'] == camera)
    rows = []
    for condition in args.condition or ('Low-overcast', 'Low-clear', 'High-overcast', 'High-clear'):
        directory = OUT / args.after / condition
        state = json.loads((directory / 'runtime-cameras' / ('QA_' + camera + '.json')).read_text())
        matrix = np.array(state['projection']).reshape(4, 4) @ np.array(state['view']).reshape(4, 4)
        im = Image.open(directory / (camera + '.png')).convert('RGB')
        width, height = im.size
        # Clear near asphalt, away from the crossing, kerb and white boundary line.
        x0, y0, x1, y1 = [round(v * width / 960) for v in (380, 280, 630, 400)]
        depth = np.full((y1-y0, x1-x0), np.inf)
        uv = np.full((*depth.shape, 2), np.nan)
        runtime_pos = state['position']
        offset = np.array(spec['pos'])[[0, 2, 1]] - [runtime_pos['x'], runtime_pos['y'], runtime_pos['z']]
        _, nodes = read(ROOT / 'Data/raw/derived/bialystok-industrial-c/world/chunk_3_4.low.glb')
        for material, attrs in nodes['road']:
            if material != 'road_asphalt' or 'TEXCOORD_1' not in attrs:
                continue
            xyz = attrs['POSITION'].astype(float)
            xyz[:, 0] *= -1
            xyz -= offset
            clip = matrix @ np.column_stack((xyz, np.ones(len(xyz)))).T
            ndc = (clip[:3] / clip[3]).T
            points = np.column_stack(((ndc[:, 0]+1)*width/2, (1-ndc[:, 1])*height/2))
            field = attrs['TEXCOORD_1'].copy()
            field[:, 1] = 1-field[:, 1]  # GLTF UV inversion undone by importer.
            field = field.astype(np.float16).astype(float)
            for tri in attrs['indices'].reshape(-1, 3):
                if np.any(clip[3, tri] <= 0):
                    continue
                p = points[tri]
                lo = np.maximum(np.floor(p.min(0)).astype(int), [x0, y0])
                hi = np.minimum(np.ceil(p.max(0)).astype(int), [x1, y1])
                if np.any(lo >= hi):
                    continue
                xs, ys = np.meshgrid(np.arange(lo[0], hi[0])+.5, np.arange(lo[1], hi[1])+.5)
                a, b, c = p
                den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(den) < 1e-10:
                    continue
                wa = ((b[1]-c[1])*(xs-c[0])+(c[0]-b[0])*(ys-c[1]))/den
                wb = ((c[1]-a[1])*(xs-c[0])+(a[0]-c[0])*(ys-c[1]))/den
                weights = np.stack((wa, wb, 1-wa-wb), axis=-1)
                z = weights @ ndc[tri, 2]
                sl = np.s_[lo[1]-y0:hi[1]-y0, lo[0]-x0:hi[0]-x0]
                mask = np.all(weights >= -1e-6, axis=-1) & (z < depth[sl])
                perspective = weights / clip[3, tri]
                sample = (perspective @ field[tri]) / perspective.sum(-1)[..., None]
                depth[sl][mask] = z[mask]
                uv[sl][mask] = sample[mask]
        lc = np.mod(uv[..., 0], 1)
        wp = np.clip(1-abs(abs(lc-.5)-.24)/.11, 0, 1)
        valid = np.isfinite(lc) & (uv[..., 0] >= -.5) & (uv[..., 1] >= .65)
        masks = dict(left=valid & (wp > .65) & (lc < .5),
                     centre=valid & (lc > .45) & (lc < .55),
                     right=valid & (wp > .65) & (lc > .5))
        overlay = np.asarray(im).copy()
        crop = overlay[y0:y1, x0:x1]
        for name, colour in (('left', [255, 60, 30]), ('centre', [30, 255, 60]), ('right', [30, 100, 255])):
            crop[masks[name]] = np.asarray(colour)
        preview = Image.fromarray(overlay)
        preview.thumbnail((960, 960))
        preview.save(OUT / f'wheel-mask-{args.after}-{condition}.jpg')
        measurements = []
        for label in ('baseline', args.after):
            rgb = np.asarray(Image.open(OUT / label / condition / (camera+'.png')).convert('RGB'), float)[y0:y1, x0:x1]
            luma = rgb @ np.array([.2126, .7152, .0722])
            values = {name: dict(pixels=int(mask.sum()), median=float(np.median(luma[mask])) if mask.any() else None) for name, mask in masks.items()}
            # Match image rows to reduce the effect of depth/lighting gradients.
            ratios = {}
            for side in ('left', 'right'):
                pairs = [(float(np.median(luma[y][masks[side][y]])), float(np.median(luma[y][masks['centre'][y]])))
                         for y in range(luma.shape[0]) if masks[side][y].sum() >= 3 and masks['centre'][y].sum() >= 3]
                ratios[side] = dict(rows=len(pairs), median_ratio=float(np.median([a/b for a, b in pairs if b > 0])) if pairs else None)
            measurements.append(dict(label=label, fields=values, row_matched=ratios))
        rows.append(dict(condition=condition, camera=camera, roi960=[380, 280, 630, 400], runtime=state, measurements=measurements))
    result = dict(note='Display luma, not physical albedo. Actual runtime matrices, perspective-correct Half UV1. Road-only projection does not resolve non-road occluders; inspect coloured masks before accepting. Baseline reuses identical camera pose and unchanged road geometry.', rows=rows)
    (OUT / f'wheel-contrast-{args.after}.json').write_text(json.dumps(result, indent=2)+'\n')
    for row in rows:
        print(row['condition'], [(m['label'], m['fields'], m['row_matched']) for m in row['measurements']])


if __name__ == '__main__':
    main()



