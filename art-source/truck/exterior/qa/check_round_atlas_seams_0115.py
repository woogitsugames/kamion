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


def make_rim(name, split_profile, split_angular):
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
        xbase = .5 if split_angular and c >= 9 else 0
        ybase = .5 if split_profile and r%2 else 0
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
for label,profile,angular in (('continuous',False,False),('profile-seams',True,False),
                             ('angular-seam',False,True),('both-seams',True,True)):
    row = {'case':label}
    for key,function in (('baseline',baseline),('candidate',A.reduce_round)):
        # The function recognizes the actual wheel role from its name.
        obj = make_rim('wheel_FL_rim',profile,angular)
        before = measure(obj)
        columns = function(obj,24)
        after = measure(obj)
        row[key] = {'before':before,'after':after,'columns':columns}
        bpy.data.objects.remove(obj,do_unlink=True)
        if key == 'candidate' and after['cross_chart_triangles']:
            raise AssertionError(f'{label}: candidate bridged atlas charts: {after}')
    if (profile or angular) and row['baseline']['after']['cross_chart_triangles'] == 0:
        raise AssertionError(f'{label}: test did not reproduce the previous reducer defect')
    if not (profile or angular) and row['baseline']['after'] != row['candidate']['after']:
        raise AssertionError('Continuous atlas changed unexpectedly')
    results.append(row)

source = ROOT/'tools/blender/truck/exterior/a6_export.py'
output = ROOT/'artifacts/truck-r3/atlas-seam-regression.json'
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps({'result':'Passed','baseline_commit':'e35eb7e5',
    'candidate_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'note':'Synthetic regression of real BMesh reducer only; not an FBX, budget or visual acceptance.',
    'cases':results},indent=2),encoding='utf8')
print('TRUCK_ATLAS_SEAM_TEST: OK cases=4 '+str(output))
