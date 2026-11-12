"""Topology checks and a labelled analytic diagram, not a Unity appearance test."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import importlib.util
import json
import math
import time

ROOT = Path(__file__).resolve().parents[4]
source = ROOT / 'tools/blender/truck/exterior/wheel_disc.py'
spec = importlib.util.spec_from_file_location('disc_proxy', source)
disc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(disc)


def cross(a, b, p):
    return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])


def covered(points, triangles, point):
    return any(all(cross(points[t[i]], points[t[(i+1) % 3]], point) >= -1e-12
                   for i in range(3)) for t in triangles)


def check(segments):
    mesh = disc.solid_annulus(.112, .236, .2, .028, .022, hole_segments=segments)
    vertices, triangles = mesh['vertices'], mesh['triangles']
    directed = Counter((t[i], t[(i+1) % 3]) for t in triangles for i in range(3))
    edges = Counter()
    for edge, count in directed.items():
        edges[tuple(sorted(edge))] += count
    assert set(edges.values()) == {2}, 'Open or nonmanifold solid'
    assert all(directed[(b, a)] == count for (a, b), count in directed.items()), 'Inconsistent winding'
    assert len(vertices)-len(edges)+len(triangles) == -20, 'Wrong through-hole genus'
    volume = sum(sum(vertices[a][i]*(vertices[b][(i+1) % 3]*vertices[c][(i+2) % 3]
                                   -vertices[b][(i+2) % 3]*vertices[c][(i+1) % 3])
                     for i in range(3))/6 for a, b, c in triangles)
    assert volume > 0, 'Inside-out solid'
    plane = mesh['plane']
    points, front = plane['vertices'], plane['triangles']
    assert min(cross(points[a], points[b], points[c]) for a, b, c in front) > 1e-12
    probes = [(0.0, 0.0)]
    for k in range(10):
        a = math.tau*(k+.5)/10
        cy, cz = .2*math.cos(a), .2*math.sin(a)
        probes.append((cy, cz))
        probes += [(cy+.02*math.cos(j*math.tau/8), cz+.02*math.sin(j*math.tau/8)) for j in range(8)]
    assert not any(covered(points, front, p) for p in probes), 'Hand hole or centre bore filled'
    assert len(mesh['uv']) == len(triangles) == len(mesh['face_charts'])
    assert all(math.isfinite(v) for face in mesh['uv'] for point in face for v in point)
    return mesh, {'segments': segments, 'vertices': len(vertices), 'triangles': len(triangles),
                  'euler': len(vertices)-len(edges)+len(triangles), 'closed_edges': True,
                  'consistent_winding': True, 'open_hole_probes': len(probes),
                  'volume_m3': volume, 'charts': len(mesh['chart_names'])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()
    start = time.perf_counter()
    checked = [check(n) for n in (8, 10, 12, 16)]
    target = ROOT / args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    packet = {'status': 'Topology only: unintegrated prototype, no packed atlas, FBX or appearance PASS',
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'seconds': time.perf_counter()-start, 'rows': [row for _, row in checked]}
    target.write_text(json.dumps(packet, indent=2), encoding='utf8')
    if args.preview:
        from PIL import Image, ImageDraw
        image = Image.new('RGB', (960, 510), (24, 24, 24))
        draw = ImageDraw.Draw(image)
        draw.text((12, 8), 'PROTOTYP TOPOLOGII | nie jest to render gry ani ocena materialu', fill='white')
        for x, (mesh, row) in zip((0, 480), (checked[0], checked[-1])):
            plane = mesh['plane']
            positions = [(x+240+800*y, 260-800*z) for y, z in plane['vertices']]
            for t in plane['triangles']:
                draw.polygon([positions[i] for i in t], fill=(172, 172, 172), outline=(95, 95, 95))
            draw.text((x+12, 35), f"{row['segments']} segmentow / otwor | pelna tarcza {row['triangles']} tris", fill='white')
        draw.text((12, 484), 'Dziesiec regularnych otworow, centralny otwor osi, zamkniete sciany i tyl. UV jeszcze niepakowane.', fill='white')
        image.save(target.with_suffix('.jpg'), quality=94)
    print(json.dumps(packet, indent=2))


if __name__ == '__main__':
    main()
