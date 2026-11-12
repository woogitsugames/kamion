"""Measure display luma in projected road wheel/centre fields, with inspectable masks."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT / 'artifacts/surface-wear-r1'))
from bus_world_proof import read


def checked_geometry(label):
    """Reject stale world data instead of projecting today's geometry onto older captures."""
    name = 'chunk_3_4.low.glb'
    baseline = json.loads((OUT / 'geometry-baseline.json').read_text(encoding='utf-8'))
    expected = next(row for row in baseline['rows'] if row['file'] == name)
    candidate = json.loads((OUT / f'geometry-{label}.json').read_text(encoding='utf-8'))
    candidate_row = next(row for row in candidate['rows'] if row['file'] == name)
    if candidate['label'] != label or candidate_row != expected:
        raise RuntimeError('Candidate geometry evidence is absent, mislabeled or differs from baseline.')
    document, nodes = read(ROOT / 'Data/raw/derived/bialystok-industrial-c/world' / name)
    graph = [{key: node[key] for key in ('name', 'mesh', 'children', 'matrix', 'translation', 'rotation', 'scale') if key in node}
             for node in document['nodes']]
    digest = hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    if digest != expected['scene_graph_sha256']:
        raise RuntimeError('Current GLB scene graph differs from baseline evidence.')
    # This projector handles the importer handedness flip and region root, not arbitrary glTF nodes.
    for node in document['nodes']:
        if (not np.array_equal(node.get('matrix', np.eye(4).reshape(-1)), np.eye(4).reshape(-1))
                or node.get('translation', [0, 0, 0]) != [0, 0, 0]
                or node.get('rotation', [0, 0, 0, 1]) != [0, 0, 0, 1]
                or node.get('scale', [1, 1, 1]) != [1, 1, 1]):
            raise RuntimeError('Nonidentity GLB node transform is unsupported by this projector.')
    observed = []
    for node, parts in sorted(nodes.items()):
        for index, (material, attrs) in enumerate(parts):
            fields = {key: dict(shape=list(value.shape), dtype=value.dtype.str,
                                sha256=hashlib.sha256(value.tobytes()).hexdigest())
                      for key, value in sorted(attrs.items())}
            observed.append(dict(node=node, primitive=index, material=material, fields=fields))
    if observed != expected['primitives']:
        raise RuntimeError('Current GLB attributes/indices differ from baseline evidence.')
    return nodes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--after', default='candidate')
    parser.add_argument('--condition', action='append')
    args = parser.parse_args()
    camera = 'd_wear_lane_old'
    rows = []
    nodes = checked_geometry(args.after)
    for condition in args.condition or ('Low-overcast', 'Low-clear', 'High-overcast', 'High-clear'):
        directory = OUT / args.after / condition
        state = json.loads((directory / 'runtime-cameras' / ('QA_' + camera + '.json')).read_text())
        if len(state.get('rootToWorld', [])) != 16:
            raise RuntimeError('Runtime rootToWorld is required. Never infer the world anchor from an input camera: seat=road may reseat it.')
        before_state = json.loads((OUT / 'baseline' / condition / 'runtime-cameras' / ('QA_' + camera + '.json')).read_text())
        for key in ('view', 'projection', 'rootToWorld'):
            if len(before_state.get(key, [])) != 16 or before_state[key] != state[key]:
                raise RuntimeError(f'Baseline/candidate {key} is absent or differs; shared masks are invalid.')
        matrix = (np.array(state['projection']).reshape(4, 4) @ np.array(state['view']).reshape(4, 4)
                  @ np.array(state['rootToWorld']).reshape(4, 4))
        im = Image.open(directory / (camera + '.png')).convert('RGB')
        width, height = im.size
        with Image.open(OUT / 'baseline' / condition / (camera + '.png')) as before_image:
            if before_image.size != im.size:
                raise RuntimeError('Baseline/candidate image sizes differ.')
        # Clear near asphalt, away from the crossing, kerb and white boundary line.
        x0, y0, x1, y1 = [round(v * width / 960) for v in (380, 280, 630, 400)]
        depth = np.full((y1-y0, x1-x0), np.inf)
        uv = np.full((*depth.shape, 2), np.nan)
        for material, attrs in nodes['road']:
            if material != 'road_asphalt' or 'TEXCOORD_1' not in attrs:
                continue
            xyz = attrs['POSITION'].astype(float)
            xyz[:, 0] *= -1
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
    result = dict(note='Display luma, not physical albedo. Actual runtime root-to-world, view and projection matrices, perspective-correct Half UV1. Road-only projection does not resolve non-road occluders; inspect coloured masks before accepting. Baseline reuses identical camera pose and unchanged road geometry.', rows=rows)
    (OUT / f'wheel-contrast-{args.after}.json').write_text(json.dumps(result, indent=2)+'\n')
    for row in rows:
        print(row['condition'], [(m['label'], m['fields'], m['row_matched']) for m in row['measurements']])


if __name__ == '__main__':
    main()



