"""Blender regression witness: a decimated lathe must not bridge atlas islands.

Run under the heavy slot, e.g. blender -b --factory-startup --threads 2 --python THIS.
Uses the real production reduce_round, not a model of its implementation.
The previous round's function must exhibit the defect on the same input.
"""
import ast
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import bpy

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT/'tools/blender/truck/exterior'))
import a6_export as A

old_source = subprocess.run(
    ['git','show','e35eb7e5:tools/blender/truck/exterior/a6_export.py'],
    cwd=ROOT, capture_output=True, text=True, encoding='utf8', check=True).stdout
old_function = next(node for node in ast.parse(old_source).body
                    if isinstance(node, ast.FunctionDef) and node.name == 'reduce_round')
namespace = vars(A).copy()
exec(compile(ast.Module(body=[old_function],type_ignores=[]),'<round-r2-baseline>','exec'),namespace)
baseline = namespace['reduce_round']


def make_rim(name, profile_cut, angular_cut):
    profile = A.C.RIM_PROF + A.C.RIM_INNER[::-1]
    count = 40
    centre_x = -A.G.FRONT_TRACK/2
    vertices = [(centre_x-x, radius*math.cos(2*math.pi*c/count),
                 A.G.WHEEL_Z+radius*math.sin(2*math.pi*c/count))
                for c in range(count) for radius,x in profile]
    width = len(profile)
    faces = []
    cells = []
    for c in range(count):
        for r in range(width-1):
            faces.append((c*width+r, ((c+1)%count)*width+r,
                          ((c+1)%count)*width+r+1, c*width+r+1))
            cells.append((c,r))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    atlas = mesh.uv_layers.new(name='Atlas')
    for polygon,(c,r) in zip(mesh.polygons,cells):
        # Disjoint real chart boxes in UV, with identical continuous geometry.
        xbase = .5 if angular_cut is not None and c >= angular_cut else 0
        ybase = .5 if profile_cut is not None and r >= profile_cut else 0
        coordinates = ((c,r),(c+1,r),(c+1,r+1),(c,r+1))
        for loop,(column,ring) in zip(polygon.loop_indices,coordinates):
            atlas.data[loop].uv = (xbase+.05+.18*column/count,
                                   ybase+.05+.18*ring/(width-1))
    obj = bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def measure(obj):
    mesh = obj.data
    mesh.calc_loop_triangles()
    atlas = mesh.uv_layers['Atlas'].data
    crossed = 0
    for triangle in mesh.loop_triangles:
        charts = {(int(atlas[i].uv.x >= .5),int(atlas[i].uv.y >= .5)) for i in triangle.loops}
        if len(charts) != 1:
            crossed += 1
    return {'triangles':len(mesh.loop_triangles),'cross_chart_triangles':crossed}


results = []
profile_cuts = range(1,len(A.C.RIM_PROF+A.C.RIM_INNER[::-1])-1)
cases = (
    ('continuous',[(None,None)]),
    ('profile-seams',[(r,None) for r in profile_cuts]),
    ('angular-seams',[(None,c) for c in range(1,40)]),
    ('both-seams',[(r,9) for r in profile_cuts]),
)
for label,variants in cases:
    case = {'case':label,'variants':[],'baseline_cross_total':0,'candidate_cross_total':0}
    for profile_cut,angular_cut in variants:
        row = {'profile_cut':profile_cut,'angular_cut':angular_cut}
        for key,function in (('baseline',baseline),('candidate',A.reduce_round)):
            # The function recognizes the actual wheel role from its name.
            obj = make_rim('wheel_FL_rim',profile_cut,angular_cut)
            before = measure(obj)
            columns = function(obj,24)
            after = measure(obj)
            row[key] = {'before':before,'after':after,'columns':columns}
            mesh = obj.data
            bpy.data.objects.remove(obj,do_unlink=True)
            bpy.data.meshes.remove(mesh)
            if key == 'candidate' and after['cross_chart_triangles']:
                print('ATLAS_FAILED_VARIANT:',json.dumps(row))
                raise AssertionError(f'{label}: candidate bridged atlas charts: {after}')
            case[key+'_cross_total'] += after['cross_chart_triangles']
        if label=='continuous' and row['baseline']['after'] != row['candidate']['after']:
            raise AssertionError('Continuous atlas changed unexpectedly')
        case['variants'].append(row)
    print('ATLAS_CASE:',label,'variants=',len(variants),'baseline_cross=',case['baseline_cross_total'],
          'candidate_cross=',case['candidate_cross_total'])
    results.append(case)
if not any(case['baseline_cross_total'] for case in results):
    raise AssertionError('No fixture reproduced the previous reducer defect')

# Test the authoring path as well: the original parametric map must survive the
# material conversion and packing as one chart, so the geometry guard stays cheap.
obj = make_rim('wheel_FL_rim',None,None)
mesh = obj.data
original_uv = [tuple(value.uv) for value in mesh.uv_layers['Atlas'].data]
mesh.uv_layers['Atlas'].name = 'UVMap'
material = bpy.data.materials.get('alu_wheel') or bpy.data.materials.new('alu_wheel')
mesh.materials.append(material)
obj['group']='wheels'
obj['part']='WHEEL_FL'
gm = {slot:bpy.data.materials.get(name) or bpy.data.materials.new(name)
      for slot,name in A.SLOT_MAT.items()}
A.to_game_piece(obj,gm)
if [tuple(value.uv) for value in mesh.uv_layers['Atlas'].data] != original_uv:
    raise AssertionError('Authoring conversion discarded parametric lathe UV')
if not obj.get('cylindrical_atlas',False):
    raise AssertionError('Missing cylindrical atlas contract')
A.unwrap_atlases([obj])
def islands():
    return len(A.uv_islands(obj.data,obj.data.uv_layers['Atlas'].data,
                           [face.index for face in obj.data.polygons]))
before_islands=islands()
if before_islands != 1:
    raise AssertionError(f'Packing split cylindrical atlas into {before_islands} charts')
A.reduce_round(obj,24)
after_islands=islands()
if after_islands != 1:
    raise AssertionError(f'Reduction split cylindrical atlas into {after_islands} charts')
authoring = {'parametric_uv_preserved':True,'packed_charts':before_islands,
             'reduced_charts':after_islands,'reduced_triangles':len(obj.data.loop_triangles)}
print('ATLAS_AUTHORING:',json.dumps(authoring))

source = ROOT/'tools/blender/truck/exterior/a6_export.py'
output = ROOT/'artifacts/truck-r3/atlas-seam-regression.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps({'result':'Passed','baseline_commit':'e35eb7e5',
    'candidate_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'note':'Exhaustive seam locations in four groups on the real reducer; at least one must reproduce the old defect. Not an FBX, budget or visual acceptance.',
    'cases':results,'authoring':authoring},indent=2),encoding='utf8')
print('TRUCK_ATLAS_SEAM_TEST: OK cases=4 '+str(output))
