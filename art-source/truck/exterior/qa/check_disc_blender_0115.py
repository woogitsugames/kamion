"""Actual Blender authoring/packing/LOD smoke check; run only under heavy.

Writes a small JSON packet, no canonical FBX, textures, scene or prefab changes.
The real full exporter and visual comparison are still required afterwards.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'tools/blender/truck/exterior'))
import geom as G
import a6_export as A
import wheel_disc_blender as WD

args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
output = ROOT/parser.parse_args(args).output
bpy.ops.wm.read_factory_settings(use_empty=True)
G.STATE['coll'] = bpy.context.scene.collection
G.STATE['group'] = 'wheels'
G.STATE['mats'] = {'alu_wheel': bpy.data.materials.new('alu_wheel')}
gm = {slot: bpy.data.materials.new(name) for slot, name in A.SLOT_MAT.items()}
objects = []
for side, label in ((-1, 'L'), (1, 'R')):
    ob = WD.make_authoring('wheel_F'+label+'_disc',
                           (side*G.FRONT_TRACK/2, 0, G.WHEEL_Z), side, .12)
    ob['part'] = 'WHEEL_F'+label
    A.to_game_piece(ob, gm)
    objects.append(ob)
A.unwrap_atlases(objects)
rows = []
for ob in objects:
    high = ob.data
    high.calc_loop_triangles()
    chart_count = len(A.uv_islands(high, high.uv_layers['Atlas'].data,
                                  [p.index for p in high.polygons]))
    if chart_count != 14:
        raise AssertionError(f'{ob.name}: expected 14 packed charts, got {chart_count}')
    low = A.copy_object(ob, ob.name+'_smoke_low', bpy.context.scene.collection)
    WD.replace_lod(low, 8)
    low.data.calc_loop_triangles()
    if len(high.loop_triangles) != 1000 or len(low.data.loop_triangles) != 680:
        raise AssertionError('Unexpected actual Blender triangle count')
    mesh = low.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    if any(not e.is_manifold for e in bm.edges) or bm.calc_volume(signed=True) <= 0:
        raise AssertionError('Low plate is open, nonmanifold or inside-out')
    bm.free()
    atlas = mesh.uv_layers['Atlas'].data
    minimum_area = 1.0
    for face in mesh.polygons:
        points = [atlas[i].uv for i in face.loop_indices]
        area = abs(sum(a.x*b.y-b.x*a.y for a, b in zip(points, points[1:]+points[:1])))/2
        minimum_area = min(area, minimum_area)
        if area <= 1e-14 or any(v < -1e-6 or v > 1+1e-6 for p in points for v in p):
            raise AssertionError('Degenerate or out-of-atlas Low triangle')
    A.finalize_mesh(low)
    mesh.calc_loop_triangles()
    if len(mesh.loop_triangles) != 680:
        raise AssertionError('Finalize changed regular Low topology')
    if any(n in mesh.attributes for n in ('disc_chart', 'disc_parameter', 'prio')):
        raise AssertionError('Auxiliary authoring data would escape to FBX')
    if [layer.name for layer in mesh.uv_layers] != ['Atlas', 'Decal', 'Data']:
        raise AssertionError('Runtime UV interface changed')
    rows.append({'piece': ob.name, 'high_triangles': len(high.loop_triangles),
                 'low_triangles': len(mesh.loop_triangles), 'packed_charts': chart_count,
                 'minimum_low_uv_triangle_area': minimum_area, 'closed': True,
                 'auxiliary_attributes_removed': True})
files = [ROOT/'tools/blender/truck/exterior'/name for name in
         ('a6_export.py', 'chassis.py', 'wheel_disc.py', 'wheel_disc_blender.py')]
packet = {'result': 'Passed', 'blender': bpy.app.version_string,
          'note': 'Actual Blender authoring, production material conversion/packer, mirrored UV transfer, Low reconstruction and finalize. Not full vehicle budget, bake, FBX or appearance acceptance.',
          'sources': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
          'rows': rows}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(packet, indent=2), encoding='utf8')
print('TRUCK_DISC_NATIVE_SMOKE: OK '+str(output))
