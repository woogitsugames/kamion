"""Audit frozen raw and imported geometry, independently of appearance metadata.

Run under heavy after After.ready. No source/asset mutations. Pixel quality and
device GPU time are separate evidence and are not established by this audit.
"""
import hashlib
import json
import struct
from pathlib import Path

import numpy as np

from unity_mesh_audit import read_meshes

HERE = Path(__file__).resolve().parent
if not (HERE/'After.ready').exists():
    raise RuntimeError('Complete and freeze both After matrices and imported meshes first')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_glb(path):
    data = path.read_bytes()
    length = struct.unpack_from('<I',data,12)[0]
    doc = json.loads(data[20:20+length])
    start = 28+length
    dtypes = {5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
    dimensions = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
    def acc(index):
        item = doc['accessors'][index]
        view = doc['bufferViews'][item['bufferView']]
        dtype = np.dtype(dtypes[item['componentType']])
        dim = dimensions[item['type']]
        array = np.ndarray((item['count'],dim),dtype=dtype,buffer=data,
                           offset=start+view.get('byteOffset',0)+item.get('byteOffset',0),
                           strides=(view.get('byteStride',dtype.itemsize*dim),dtype.itemsize)).copy()
        return array, {k:item.get(k,False) for k in ('componentType','type','normalized')}
    result = {}
    for node in doc['nodes']:
        if 'mesh' not in node:
            continue
        if any(k in node for k in ('matrix','translation','rotation','scale')):
            raise RuntimeError('Unexpected far-field node transform')
        for p in doc['meshes'][node['mesh']]['primitives']:
            material = doc['materials'][p['material']]['name']
            key = (node['name'],material)
            if key in result:
                raise RuntimeError('Duplicate material primitive in one sector')
            attrs = {name:acc(index) for name,index in p['attributes'].items()}
            indices,_ = acc(p['indices'])
            result[key] = dict(attributes=attrs,indices=indices.reshape(-1))
    if len(result) != 8:
        raise RuntimeError('Expected four sectors with two populated primitives each')
    return result


def normalized_color(attribute):
    array,meta = attribute
    if meta['normalized']:
        return array.astype(float)/np.iinfo(array.dtype).max
    return array.astype(float)


def flags(alpha):
    return dict(panel=int((abs(alpha-0.25)<0.005).sum()),
                panel_ribbon=int((abs(alpha-0.65)<0.005).sum()))


cache_before = HERE/'before-source/far_field_gis_cache.json'
cache_after = HERE/'after-source/far_field_gis_cache.json'
if sha(cache_before) != sha(cache_after):
    raise RuntimeError('GIS feature inputs changed; cannot attribute this round solely to facade appearance')
result = dict(gis_cache_unchanged=True,gis_cache_sha256=sha(cache_before),tiers={},
              note='Counts/buffers and source provenance only; not photographic similarity or device GPU timing.')
before_qa = json.loads((HERE/'before-far-field-qa.json').read_text())
after_qa = json.loads((HERE/'after-far-field-qa.json').read_text())
if before_qa['building_height_sources'] != after_qa['building_height_sources']:
    raise RuntimeError('Height provenance inventory changed')
result['height_provenance_unchanged'] = True
result['appearance_policy'] = after_qa['appearance_policy']
for tier,name in (('Low','far_field.low.glb'),('High','far_field.glb')):
    before_path = HERE/'before-source'/name
    after_path = HERE/'after-source'/name
    if sha(before_path) != before_qa['tiers'][tier]['sha256'] or sha(after_path) != after_qa['tiers'][tier]['sha256']:
        raise RuntimeError('Frozen GLB does not match its QA')
    before = read_glb(before_path)
    after = read_glb(after_path)
    if before.keys() != after.keys():
        raise RuntimeError('Sector/material primitive set changed')
    rows = []
    for key,old in before.items():
        new = after[key]
        if not np.array_equal(old['indices'],new['indices']):
            raise RuntimeError(f'{tier}/{key}: topology changed')
        if old['attributes'].keys() != new['attributes'].keys():
            raise RuntimeError(f'{tier}/{key}: vertex attributes changed')
        for attribute,(array,meta) in old['attributes'].items():
            other,other_meta = new['attributes'][attribute]
            if array.shape != other.shape or meta != other_meta:
                raise RuntimeError(f'{tier}/{key}: attribute layout changed')
            if key[1] == 'forest_edge_mixed' and array.tobytes() != other.tobytes():
                raise RuntimeError(f'{tier}/{key}: forest attribute data changed')
        p = old['attributes']['POSITION'][0]
        q = new['attributes']['POSITION'][0]
        if not np.array_equal(p[:,[0,2]],q[:,[0,2]]):
            raise RuntimeError(f'{tier}/{key}: horizontal coordinates changed')
        if not np.array_equal(p.min(axis=0),q.min(axis=0)) or not np.array_equal(p.max(axis=0),q.max(axis=0)):
            raise RuntimeError(f'{tier}/{key}: sector envelope changed')
        row = dict(sector=key[0],material=key[1],vertices=len(p),triangles=len(new['indices'])//3,
                   topology_unchanged=True,horizontal_coordinates_unchanged=True,bounds_unchanged=True,
                   changed_y_vertices=int(np.any(p != q,axis=1).sum()))
        if key[1] == 'far_field_buildings':
            old_color = normalized_color(old['attributes']['COLOR_0'])
            color = normalized_color(new['attributes']['COLOR_0'])
            row.update(before_flags=flags(old_color[:,3]),after_flags=flags(color[:,3]),
                       changed_color_vertices=int(np.any(old_color != color,axis=1).sum()))
        else:
            row['all_forest_attributes_byte_identical'] = True
        rows.append(row)
    triangles = sum(row['triangles'] for row in rows)
    if triangles != before_qa['tiers'][tier]['total_triangles'] or triangles != after_qa['tiers'][tier]['total_triangles']:
        raise RuntimeError(f'{tier}: raw triangle budget changed')
    if not sum(sum(row.get('after_flags',{}).values()) for row in rows):
        raise RuntimeError('New appearance data missing from generated geometry')

    old_meshes = read_meshes(HERE/f'before-source/world_edge_far-{tier}.asset')
    new_meshes = read_meshes(HERE/f'after-source/world_edge_far-{tier}.asset')
    if old_meshes.keys() != new_meshes.keys() or len(old_meshes) != 4:
        raise RuntimeError('Imported sector mesh set changed')
    imported = []
    for name,old in old_meshes.items():
        new = new_meshes[name]
        if old['count'] != new['count'] or old['stride'] != new['stride'] or not np.array_equal(old['indices'],new['indices']):
            raise RuntimeError(f'{name}: imported buffers/layout/topology changed')
        if not np.array_equal(old['positions'][:,[0,2]],new['positions'][:,[0,2]]):
            raise RuntimeError(f'{name}: imported horizontal coordinates changed')
        if not np.array_equal(old['positions'].min(axis=0),new['positions'].min(axis=0)) or not np.array_equal(old['positions'].max(axis=0),new['positions'].max(axis=0)):
            raise RuntimeError(f'{name}: imported bounds changed')
        byte_count = new['count']*new['stride']+new['indices'].nbytes
        imported.append(dict(mesh=name,vertices=new['count'],stride=new['stride'],vertex_index_buffer_bytes=byte_count,
                             buffer_sizes_unchanged=True,topology_unchanged=True,
                             after_flags=flags(new['colors'][:,3])))
    if not sum(sum(row['after_flags'].values()) for row in imported):
        raise RuntimeError('Appearance flags lost in the Unity import')
    result['tiers'][tier] = dict(total_triangles=triangles,raw_primitives=rows,imported_meshes=imported,
                                imported_vertex_index_bytes=sum(row['vertex_index_buffer_bytes'] for row in imported))

old_apron = read_meshes(HERE/'before-source/world_edge.asset')['world_edge']
new_apron = read_meshes(HERE/'after-source/world_edge.asset')['world_edge']
if not np.array_equal(old_apron['positions'],new_apron['positions']) or not np.array_equal(old_apron['indices'],new_apron['indices']):
    raise RuntimeError('Apron geometry changed during the facade round')
result['apron_geometry_unchanged'] = True
(HERE/'appearance-geometry-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({tier:{k:v for k,v in row.items() if k not in ('raw_primitives','imported_meshes')}
                  for tier,row in result['tiers'].items()}))
