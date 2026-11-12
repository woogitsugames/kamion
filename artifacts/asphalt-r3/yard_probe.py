"""Read-only surface inventory near the PCRT reference context, outside the protected site.

Run through run-heavy.ps1 -Stage YardProbe after the matching canonical world build.
This locates surfaces, not the untagged photograph's camera or the whole PCRT site.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT / 'artifacts/surface-wear-r1'))
from bus_world_proof import read

# Deliberately stays west of the conservative Kwadrat E=400 boundary.
BBOX = (280.0, -560.0, 395.0, -300.0)


def overlaps(bounds):
    return (bounds['e_max'] >= BBOX[0] and bounds['e_min'] <= BBOX[2]
            and bounds['n_max'] >= BBOX[1] and bounds['n_min'] <= BBOX[3])


def identity_nodes(document):
    for node in document['nodes']:
        if (not np.array_equal(node.get('matrix', np.eye(4).reshape(-1)), np.eye(4).reshape(-1))
                or node.get('translation', [0, 0, 0]) != [0, 0, 0]
                or node.get('rotation', [0, 0, 0, 1]) != [0, 0, 0, 1]
                or node.get('scale', [1, 1, 1]) != [1, 1, 1]):
            raise RuntimeError('Unsupported nonidentity glTF transform; do not guess query coordinates.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    if not args.label.replace('-', '').isalnum():
        raise RuntimeError('Invalid label')
    status = (OUT / 'STATUS.md').read_text(encoding='utf-8-sig')
    expected_status = f'heavy World owner=gpt-asphalt-r3 exit=0; log artifacts/asphalt-r3/{args.label}-World.log'
    if expected_status not in status:
        raise RuntimeError('Complete the matching canonical world producer before this probe.')
    manifest_path = ROOT / 'Data/Regions/bialystok-industrial-c/generated/world_manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    points = [{'en': [float(e), float(n)], 'hits': []}
              for n in range(-550, -309, 20) for e in range(285, 386, 20)]
    files, inventory, definitions = [], [], {}
    for chunk in manifest['chunks']:
        if not overlaps(chunk['bounds_local_m']):
            continue
        source = chunk['low']
        path = ROOT / source['file']
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != source['sha256']:
            raise RuntimeError(f'Manifest/raw SHA mismatch: {path.name}')
        document, nodes = read(path)
        identity_nodes(document)
        files.append(dict(file=source['file'], sha256=digest, bounds=chunk['bounds_local_m']))
        material_defs = {material['name']: material for material in document['materials']}
        for node, parts in nodes.items():
            if node not in ('paved', 'road', 'plot_ground'):
                continue
            for primitive, (material, attrs) in enumerate(parts):
                positions = attrs['POSITION'].astype(float)
                en = np.column_stack((-positions[:, 0], positions[:, 2]))
                triangles = attrs['indices'].reshape(-1, 3)
                xy, heights = en[triangles], positions[triangles, 1]
                lo, hi = xy.min(axis=1), xy.max(axis=1)
                selected = ((hi[:, 0] >= BBOX[0]) & (lo[:, 0] <= BBOX[2])
                            & (hi[:, 1] >= BBOX[1]) & (lo[:, 1] <= BBOX[3]))
                if not selected.any():
                    continue
                tri_ids = np.flatnonzero(selected)
                xy, heights = xy[selected], heights[selected]
                if 'NORMAL' in attrs:
                    top = attrs['NORMAL'][triangles[selected], 1].mean(axis=1) > .5
                    xy, heights, tri_ids = xy[top], heights[top], tri_ids[top]
                if not len(xy):
                    continue
                definitions[material] = material_defs[material]
                inventory.append(dict(file=path.name, node=node, material=material, primitive=primitive,
                                      top_triangles_with_bbox_overlap=len(xy),
                                      elevation_range_u=[float(heights.min()), float(heights.max())]))
                a, b, c = xy[:, 0], xy[:, 1], xy[:, 2]
                den = (b[:, 1]-c[:, 1])*(a[:, 0]-c[:, 0]) + (c[:, 0]-b[:, 0])*(a[:, 1]-c[:, 1])
                usable = np.abs(den) > 1e-10
                for point in points:
                    e, n = point['en']
                    wa = np.divide((b[:, 1]-c[:, 1])*(e-c[:, 0])+(c[:, 0]-b[:, 0])*(n-c[:, 1]), den,
                                   out=np.zeros_like(den), where=usable)
                    wb = np.divide((c[:, 1]-a[:, 1])*(e-c[:, 0])+(a[:, 0]-c[:, 0])*(n-c[:, 1]), den,
                                   out=np.zeros_like(den), where=usable)
                    weights = np.column_stack((wa, wb, 1-wa-wb))
                    for hit in np.flatnonzero(usable & (weights.min(axis=1) >= -1e-7)):
                        point['hits'].append(dict(file=path.name, node=node, material=material,
                                                  triangle=int(tri_ids[hit]),
                                                  elevation_u=float(weights[hit] @ heights[hit])))
    if not files:
        raise RuntimeError('No matching chunks')
    for point in points:
        point['hits'].sort(key=lambda hit: hit['elevation_u'], reverse=True)
    result = dict(label=args.label, bbox_local_en=BBOX, files=files, inventory=inventory,
                  material_definitions=definitions, points=points,
                  manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                  note='Source E/N and absolute elevation U before runtime region-root transform. '
                       'Grid points/top faces only; roof/other occlusion is not resolved. BBox overlap is not clipped area. '
                       'Does not identify the photo camera, whole site, or authorize geometry/override changes.')
    target = OUT / f'yard-probe-{args.label}.json'
    target.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(files=len(files), groups=len(inventory), points=len(points),
                          points_with_hits=sum(bool(point['hits']) for point in points), output=str(target))))


if __name__ == '__main__':
    main()
