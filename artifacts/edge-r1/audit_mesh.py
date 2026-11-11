"""Measure asphalt/terrain clearance directly in the serialized Unity apron mesh."""
import json
import re
import sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
phase = sys.argv[1] if len(sys.argv) > 1 else 'before'
path = ROOT/'game/Assets/_Generated/World/bialystok-industrial-c/Meshes/world_edge.asset'
source = path.read_text()
vertex_count = int(re.search(r'm_VertexCount: (\d+)', source)[1])
data = bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)', source)[1])
channels = re.findall(r'- stream: (\d+)\s+offset: (\d+)\s+format: (\d+)\s+dimension: (\d+)', source)
sizes = {0:4, 1:2, 2:1, 3:1, 4:1, 5:1, 6:2, 7:2, 8:4, 9:4, 10:4, 11:4}
stride = max(int(offset)+sizes[int(fmt)]*int(dim) for stream,offset,fmt,dim in channels if stream == '0')
vertices = np.ndarray((vertex_count,3), dtype='<f4', buffer=data, strides=(stride,4)).astype(float)
index_format = int(re.search(r'm_IndexFormat: (\d+)', source)[1])
indices = np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)', source)[1]), dtype='<u2' if index_format == 0 else '<u4')
submeshes = re.findall(r'firstByte: (\d+)\s+indexCount: (\d+)', source)
def triangles(submesh):
    byte, count = map(int, submeshes[submesh])
    size = 2 if index_format == 0 else 4
    return indices[byte//size:byte//size+count].reshape(-1,3)
road = triangles(1)
# Each road station is toe/left/right/toe; the first asphalt index is left at station zero.
base_vertices = int(road.min())-1
ground = triangles(0)
ground = vertices[ground[np.all(ground < base_vertices, axis=1)]]
a = ground[:,0]
b = ground[:,1]-a
c = ground[:,2]-a
det = b[:,0]*c[:,2]-b[:,2]*c[:,0]
valid = np.abs(det) > 1e-7
a,b,c,det = a[valid],b[valid],c[valid],det[valid]
def ground_at(p):
    delta = p-a
    u = (delta[:,0]*c[:,2]-delta[:,2]*c[:,0])/det
    v = (b[:,0]*delta[:,2]-b[:,2]*delta[:,0])/det
    inside = (u >= -1e-5)&(v >= -1e-5)&(u+v <= 1.00001)
    return float(np.max((a[:,1]+u*b[:,1]+v*c[:,1])[inside])) if np.any(inside) else None

if phase == 'prototype':
    # Exercise the proposed grade against the actual baseline triangles without starting Unity.
    for stub_index in range(len(road)//24):
        first = base_vertices+stub_index*52
        start_y = vertices[first+1,1]-.03
        for station in range(13):
            offset = first+station*4
            left, right = vertices[offset+1], vertices[offset+2]
            fallback = vertices[offset,1]+.35
            heights = [ground_at(left),ground_at(right)]
            height = max(fallback if value is None else value for value in heights)
            t = np.clip((station*420/12)/120,0,1)
            crown = max(start_y+.03+(height+.14-start_y-.03)*t*t*(3-2*t),height+.04)
            vertices[offset+1:offset+3,1] = crown
        for station in range(12):
            first_station = first+station*4
            next_station = first_station+4
            lift = 0.0
            for t in np.linspace(0,1,9):
                for across in np.linspace(0,1,3):
                    p0 = vertices[first_station+1]*(1-across)+vertices[first_station+2]*across
                    p1 = vertices[next_station+1]*(1-across)+vertices[next_station+2]*across
                    p = p0*(1-t)+p1*t
                    g = ground_at(p)
                    if g is not None:
                        lift = max(lift,g+.04-p[1])
            vertices[[first_station+1,first_station+2,next_station+1,next_station+2],1] += lift

rows = []
for stub_index in range(len(road)//24):
    samples = []
    for triangle in road[stub_index*24:(stub_index+1)*24]:
        p = vertices[triangle].mean(axis=0)
        ground_y = ground_at(p)
        if ground_y is not None:
            samples.append(round(float(p[1]-ground_y),4))
    start = vertices[base_vertices+stub_index*52:base_vertices+stub_index*52+4].mean(axis=0)
    rows.append(dict(stub=stub_index, start_en=[round(float(start[0]),2),round(float(start[2]),2)],
                     min_clearance_m=min(samples) if samples else None,
                     samples_m=samples))
result = dict(phase=phase, vertex_count=vertex_count, stride=stride,
              grass_triangles=len(triangles(0)), asphalt_triangles=len(road),
              ground_vertices=base_vertices, stubs=rows,
              sampling='centroid of every asphalt triangle against original apron triangles; excludes shoulders')
(HERE/f'mesh-clearance-{phase}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
for row in rows:
    if row['min_clearance_m'] is not None and row['min_clearance_m'] < -.02:
        print(row['stub'],row['start_en'],row['min_clearance_m'])
print(f'{vertex_count} vertices, {len(road)} asphalt triangles, {len(rows)} stubs measured')
