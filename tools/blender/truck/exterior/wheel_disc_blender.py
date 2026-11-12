"""Blender adapter for regular wheel discs, behind the exporter opt-in.

The canonical source recipe reconstructs original parameter coordinates after
packing. Vertex coordinates and triangle keys must still match that recipe;
otherwise reconstruction fails. No auxiliary runtime mesh attributes are needed.
"""
import json
import math

from wheel_disc import solid_annulus


def geometry(spec, segments):
    mesh = solid_annulus(spec['inner_radius'], spec['outer_radius'],
                         spec['hole_ring_radius'], spec['hole_radius'],
                         spec['thickness'], spec['hole_count'], segments)
    xc, yc, zc = spec['center']
    side, offset = spec['side'], spec['offset']
    vertices = [(xc+side*(offset+x), yc+y, zc+z) for x, y, z in mesh['vertices']]
    faces, coordinates = [], []
    for tri, uv in zip(mesh['triangles'], mesh['uv']):
        faces.append(tuple(reversed(tri)) if side < 0 else tri)
        coordinates.append(tuple(reversed(uv)) if side < 0 else uv)

    # Non-overlapping metric chart layout before the existing atlas packer.
    offsets, cursor = {}, 0.0
    for chart in range(len(mesh['chart_names'])):
        points = [p for uv, tag in zip(coordinates, mesh['face_charts']) if tag == chart for p in uv]
        u0, v0 = min(p[0] for p in points), min(p[1] for p in points)
        height = max(p[1] for p in points)-v0
        offsets[chart] = (.02-u0, cursor-v0)
        cursor += height+.02
    parameters = [[(u+offsets[tag][0], v+offsets[tag][1]) for u, v in uv]
                  for uv, tag in zip(coordinates, mesh['face_charts'])]
    return vertices, faces, parameters, mesh['face_charts']


def make_authoring(name, center, side, offset, material='alu_wheel', segments=16):
    """Construct the authoring mesh using the current exterior material registry."""
    import bmesh
    from geom import obj_from_bm
    spec = dict(inner_radius=.112, outer_radius=.236, hole_ring_radius=.2,
                hole_radius=.028, thickness=.022, hole_count=10,
                center=list(center), side=side, offset=offset, source_segments=segments)
    vertices, faces, parameters, charts = geometry(spec, segments)
    bm = bmesh.new()
    verts = [bm.verts.new(p) for p in vertices]
    uv_layer = bm.loops.layers.uv.new('UVMap')
    for tri, uv, chart in zip(faces, parameters, charts):
        face = bm.faces.new([verts[i] for i in tri])
        for loop, point in zip(face.loops, uv):
            loop[uv_layer].uv = point
    ob = obj_from_bm(name, bm, material, sharp=40, uv=False)
    ob['disc_spec_json'] = json.dumps(spec, sort_keys=True)
    ob['parametric_disc_atlas'] = True
    return ob


def chart_transform(samples):
    """Recover a verified affine atlas transform from packed parameter samples."""
    p0, q0 = samples[0]
    p1, q1 = max(samples, key=lambda pair: sum((a-b)**2 for a, b in zip(pair[0], p0)))
    dx, dy = p1[0]-p0[0], p1[1]-p0[1]
    p2, q2 = max(samples, key=lambda pair: abs(dx*(pair[0][1]-p0[1])-dy*(pair[0][0]-p0[0])))
    ex, ey = p2[0]-p0[0], p2[1]-p0[1]
    determinant = dx*ey-dy*ex
    if abs(determinant) < 1e-12:
        raise RuntimeError('Degenerate disc chart')
    a = tuple(((q1[i]-q0[i])*ey-(q2[i]-q0[i])*dy)/determinant for i in range(2))
    b = tuple((dx*(q2[i]-q0[i])-ex*(q1[i]-q0[i]))/determinant for i in range(2))

    def transform(p):
        return tuple(q0[i]+a[i]*(p[0]-p0[0])+b[i]*(p[1]-p0[1]) for i in range(2))

    error = max(math.dist(transform(p), q) for p, q in samples)
    if error > 2e-6:
        raise RuntimeError(f'Disc chart is not affine after packing: {error}')
    return transform


def replace_lod(ob, segments=8):
    """Rebuild a copied GAME piece using its actual High atlas chart transforms."""
    import bpy
    old = ob.data
    if not ob.get('parametric_disc_atlas'):
        raise ValueError('Not a parameterized wheel disc')
    if len(old.materials) != 1:
        raise RuntimeError('Disc proxy expects one existing material slot')
    spec = json.loads(ob['disc_spec_json'])
    source_vertices, source_faces, source_uv, source_charts = geometry(spec, spec.get('source_segments', 16))
    if len(old.vertices) != len(source_vertices) or len(old.polygons) != len(source_faces):
        raise RuntimeError('Source disc topology changed before LOD reconstruction')
    if any(math.dist(tuple(v.co), expected) > 1e-6 for v, expected in zip(old.vertices, source_vertices)):
        raise RuntimeError('Source disc vertex indices or positions changed')
    by_triangle = {tuple(sorted(tri)): (dict(zip(tri, uv)), chart)
                   for tri, uv, chart in zip(source_faces, source_uv, source_charts)}
    if len(by_triangle) != len(source_faces):
        raise RuntimeError('Ambiguous source disc triangle keys')
    samples = {}
    atlas = old.uv_layers['Atlas'].data
    for face in old.polygons:
        original = by_triangle.get(tuple(sorted(face.vertices)))
        if original is None:
            raise RuntimeError('Source disc faces changed during packing')
        parameters, chart = original
        bucket = samples.setdefault(chart, [])
        for i in face.loop_indices:
            bucket.append((parameters[old.loops[i].vertex_index], tuple(atlas[i].uv)))
    transforms = {tag: chart_transform(points) for tag, points in samples.items()}
    vertices, faces, coordinates, charts = geometry(spec, segments)
    mesh = bpy.data.meshes.new(old.name+'_regular')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    mesh.materials.append(old.materials[0])
    for name in ('Atlas', 'Decal', 'Data'):
        mesh.uv_layers.new(name=name)
    mesh.color_attributes.new('Col', 'BYTE_COLOR', 'CORNER')
    mesh.attributes.new('prio', 'FLOAT', 'FACE')
    # Fetch RNA layer references after all custom-data allocations.
    uv_atlas, uv_decal, uv_data = (mesh.uv_layers[n].data for n in ('Atlas', 'Decal', 'Data'))
    color = mesh.color_attributes['Col'].data
    priority = mesh.attributes['prio'].data
    data_value = tuple(old.uv_layers['Data'].data[0].uv)
    decal_value = tuple(old.uv_layers['Decal'].data[0].uv)
    color_value = tuple(old.color_attributes['Col'].data[0].color)
    priority_value = old.attributes['prio'].data[0].value
    for face, face_uv, chart in zip(mesh.polygons, coordinates, charts):
        priority[face.index].value = priority_value
        for i, point in zip(face.loop_indices, face_uv):
            uv_atlas[i].uv = transforms[chart](point)
            uv_decal[i].uv = decal_value
            uv_data[i].uv = data_value
            color[i].color = color_value
    mesh.uv_layers.active = mesh.uv_layers['Atlas']
    mesh.color_attributes.active_color = mesh.color_attributes['Col']
    mesh.shade_smooth()
    mesh.set_sharp_from_angle(angle=math.radians(40))
    ob.data = mesh
    ob['regular_disc_lod'] = True
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return ob
