"""Read-only local surface queries for material probes; never changes a generated mesh."""
import json
import sys
from pathlib import Path
import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
sys.path.insert(0, str(ROOT / 'artifacts/surface-wear-r1'))
from bus_world_proof import read


def barycentric(triangle, point):
    a, b, c = triangle
    ab, ac, ap = b-a, c-a, point-a
    det = ab[0]*ac[1]-ab[1]*ac[0]
    if abs(det) < 1e-10:
        return None
    b = (ap[0]*ac[1]-ap[1]*ac[0])/det
    c = (ab[0]*ap[1]-ab[1]*ap[0])/det
    return np.array([1-b-c, b, c])


def closest(triangle, point):
    weights = barycentric(triangle, point)
    if weights is None:
        return None
    if np.min(weights) >= 0:
        return point, weights
    candidates = []
    for index in range(3):
        a, b = triangle[index], triangle[(index+1) % 3]
        delta = b-a
        t = np.clip(np.dot(point-a, delta)/max(np.dot(delta, delta), 1e-12), 0, 1)
        p = a+t*delta
        w = np.zeros(3)
        w[index], w[(index+1) % 3] = 1-t, t
        candidates.append((float(np.dot(p-point, p-point)), p, w))
    _, p, w = min(candidates, key=lambda row: row[0])
    return p, w


def capture():
    fixture = json.loads((OUT/'cameras.json').read_text(encoding='utf-8-sig'))
    cams = {camera['id']: camera for camera in fixture['cameras']}
    old = cams['d_wear_lane_old']
    eye = np.array(old['pos'][:2])
    forward = np.array(old['look_at'][:2])-eye
    forward /= np.linalg.norm(forward)
    right = np.array([forward[1], -forward[0]])
    paving = cams['asphalt_paving_andersa_close']
    queries = {'paving_look_at': np.array(paving['look_at'][:2]),
               'paving_near_middle': (np.array(paving['pos'][:2])+paving['look_at'][:2])/2}
    hits, kerbs = [], []
    file = ROOT/'Data/raw/derived/bialystok-industrial-c/world/chunk_3_4.low.glb'
    _, nodes = read(file)
    for node, parts in nodes.items():
        if node not in ('road', 'paved', 'plot_ground'):
            continue
        for material, attrs in parts:
            if material != 'curb_concrete' and 'paving' not in material:
                continue
            v = attrs['POSITION'].astype(float)
            xy = np.column_stack((-v[:, 0], v[:, 2]))
            for index, tri in enumerate(attrs['indices'].reshape(-1, 3)):
                points, heights = xy[tri], v[tri, 1]
                if 'paving' in material:
                    for label, point in queries.items():
                        w = barycentric(points, point)
                        if w is None or np.min(w) < -1e-6:
                            continue
                        uv = None
                        if 'TEXCOORD_1' in attrs:
                            uv = (w @ attrs['TEXCOORD_1'][tri]).tolist()
                            uv[1] = 1-uv[1]  # same GLTF inversion as the importer
                        hits.append(dict(query=label, node=node, material=material, triangle=index,
                                         en=point.tolist(), elevation_u=float(w @ heights), uv1=uv))
                if material != 'curb_concrete':
                    continue
                if 'NORMAL' in attrs and float(attrs['NORMAL'][tri, 1].mean()) < .5:
                    continue
                result = closest(points, eye)
                if result is None:
                    continue
                point, w = result
                delta = point-eye
                distance = float(np.linalg.norm(delta))
                z = float(w @ heights)
                if np.dot(delta, right) <= .1 or distance > 20 or abs(z-(old['pos'][2]-1.7)) > 2:
                    continue
                kerbs.append(dict(node=node, material=material, triangle=index, en=point.tolist(), elevation_u=z,
                                  distance_m=distance))
    kerbs.sort(key=lambda row: (round(row['distance_m'], 4), -row['elevation_u']))
    nearest = []
    for row in kerbs:
        if all(np.linalg.norm(np.array(row['en'])-other['en']) > .5 for other in nearest):
            nearest.append(row)
        if len(nearest) >= 5:
            break
    proposed = None
    if nearest:
        point = nearest[0]
        proposed = dict(id='asphalt_kerb_andersa_close', type='persp', kind='material_probe', seat='road',
                        pos=[*eye.tolist(), point['elevation_u']+.75],
                        look_at=[*point['en'], point['elevation_u']+.02], fov_deg=42,
                        note='WORKING_VALUE pose aimed at a measured nearest right-hand kerb top; inspect render. Not a photo pose.')
    report = dict(file=str(file.relative_to(ROOT)), paving_hits=hits, nearest_right_kerb_tops=nearest,
                  proposed_kerb_camera=proposed,
                  note='Local source GLB geometry only; no general occlusion proof or changes to mesh. Camera still requires visual verification.')
    (OUT/'site-probe-baseline.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(paving_hits=hits, proposed_kerb_camera=proposed)))


if __name__ == '__main__':
    capture()
