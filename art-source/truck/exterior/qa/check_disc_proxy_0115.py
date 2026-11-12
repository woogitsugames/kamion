"""Topology checks and a labelled analytic diagram, not a Unity appearance test."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import importlib.util
import json
import math
import sys
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


def check_transfer():
    sys.path.insert(0, str(source.parent))
    try:
        import wheel_disc_blender as adapter
    finally:
        sys.path.pop(0)
    recipe = dict(inner_radius=.112, outer_radius=.236, hole_ring_radius=.2,
                  hole_radius=.028, thickness=.022, hole_count=10,
                  center=[-1, 0, .5], side=-1, offset=.12)
    high, low = adapter.geometry(recipe, 16), adapter.geometry(recipe, 8)
    matrices = ((.31, -.12, .12, .31), (-.27, .06, .04, .4), (.5, .05, .02, .1))
    checks = 0
    for aa, ab, ba, bb in matrices:
        def expected(p):
            return (aa*p[0]+ab*p[1]+.2, ba*p[0]+bb*p[1]+.1)
        for chart in set(high[3]):
            points = [p for uv, tag in zip(high[2], high[3]) if tag == chart for p in uv]
            pairs = [(p, expected(p)) for p in points]
            transform = adapter.chart_transform(pairs)
            for uv, tag in zip(low[2], low[3]):
                if tag == chart:
                    assert all(math.dist(transform(p), expected(p)) < 1e-10 for p in uv)
            checks += 1
    pairs = [(p, (p[0], p[1])) for uv, tag in zip(high[2], high[3]) if tag == 0 for p in uv]
    point, value = pairs[len(pairs)//2]
    pairs[len(pairs)//2] = (point, (value[0]+.001, value[1]))
    try:
        adapter.chart_transform(pairs)
    except RuntimeError:
        pass
    else:
        raise AssertionError('Non-affine chart was accepted')
    return {'chart_transforms': checks, 'matrices_include_reflection_and_anisotropic_scale': True,
            'non_affine_control_rejected': True,
            'adapter_sha256': hashlib.sha256(Path(adapter.__file__).read_bytes()).hexdigest(),
            'note': 'Synthetic affine transfer, not actual Blender packing or atlas validation'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--preview', action='store_true')
    args = parser.parse_args()
    start = time.perf_counter()
    checked = [check(n) for n in (8, 10, 12, 16)]
    target = ROOT / args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    transfer = check_transfer()
    packet = {'status': 'Topology only: unintegrated prototype, no packed atlas, FBX or appearance PASS',
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'seconds': time.perf_counter()-start, 'rows': [row for _, row in checked],
              'parameter_transfer': transfer}
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
