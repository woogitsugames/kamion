"""Deterministic planar wheel-disc topology, independent of Blender.

Each annular sector contains one regular hand hole. Its boundary retains the
sector corners, so neighbouring sectors weld without the gaps produced by a
generic collapse modifier. This module is not wired into the exporter yet.
Coordinates are metres in the disc plane; triangles face positive Z.
"""
import math

TAU = 2.0 * math.pi


def perforated_annulus(inner_radius, outer_radius, hole_ring_radius, hole_radius,
                       hole_count=10, hole_segments=8):
    """Return vertices, front triangles and explicit boundary loops.

    A zipper joins independently sampled outer/inner loops around each hole.
    Keeping the sector corners requires more outer vertices than hole vertices;
    forcing equal counts either distorts holes or leaves corner gaps.
    """
    if not (0 < inner_radius < hole_ring_radius < outer_radius):
        raise ValueError('Invalid annulus radii')
    if hole_count < 3 or hole_segments < 6 or hole_segments % 2:
        raise ValueError('Use at least three holes and an even segment count >=6')
    half = math.pi / hole_count
    if hole_radius >= min(hole_ring_radius-inner_radius,
                          outer_radius-hole_ring_radius,
                          hole_ring_radius*math.sin(half)):
        raise ValueError('Hand holes touch the sector boundary')
    vertices, triangles, holes = [], [], []
    welded = {}

    def vertex(point):
        # Adjacent analytic sectors may land on opposite sides of a rounded
        # decimal bucket. Search neighbours rather than using rounded equality.
        tolerance = 1e-8
        key = tuple(math.floor(v/tolerance) for v in point)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for index in welded.get((key[0]+dx, key[1]+dy), ()):
                    old = vertices[index]
                    if sum((a-b)**2 for a, b in zip(old, point)) < tolerance*tolerance:
                        return index
        index = len(vertices)
        vertices.append(tuple(point))
        welded.setdefault(key, []).append(index)
        return index

    def boundary_distance(angle):
        dx, dy = math.cos(angle), math.sin(angle)
        cx = hole_ring_radius
        candidates = []
        for radius in (inner_radius, outer_radius):
            # |(cx,0) + t*(dx,dy)|^2 = radius^2.
            discriminant = radius*radius-cx*cx*dy*dy
            if discriminant >= -1e-12:
                q = math.sqrt(max(0.0, discriminant))
                candidates.extend(t for t in (-cx*dx-q, -cx*dx+q) if t > 1e-10)
        for sign in (-1, 1):
            # Cross(ray_on_sector_boundary, point) = 0.
            denominator = math.cos(half)*dy-sign*math.sin(half)*dx
            if abs(denominator) > 1e-12:
                t = sign*math.sin(half)*cx/denominator
                if t > 1e-10:
                    candidates.append(t)
        if not candidates:
            raise ValueError('No intersection with sector')
        return min(candidates)

    samples = [TAU*j/hole_segments for j in range(hole_segments)]
    # Boundary silhouette sampling is independent of hand-hole tessellation:
    # adding rounder holes must not spend extra triangles on the outside ring.
    outer_samples = [TAU*j/8 for j in range(8)]
    corners = [(radius*math.cos(half), sign*radius*math.sin(half))
               for radius in (inner_radius, outer_radius) for sign in (-1, 1)]
    corner_angles = [math.atan2(y, x-hole_ring_radius) % TAU for x, y in corners]
    angles = sorted(set(round(a, 12) for a in outer_samples+corner_angles))
    # Retain exact zero for the cyclic zipper's common starting angle.
    angles[0] = 0.0
    sample_angles = [round(a, 12) for a in samples]

    for sector in range(hole_count):
        rotation = TAU*(sector+0.5)/hole_count
        co, si = math.cos(rotation), math.sin(rotation)

        def point(angle, distance):
            x = hole_ring_radius + distance*math.cos(angle)
            y = distance*math.sin(angle)
            return (co*x-si*y, si*x+co*y)

        outer = [vertex(point(a, boundary_distance(a))) for a in angles]
        inner = [vertex(point(a, hole_radius)) for a in sample_angles]
        holes.append(inner)
        a = b = 0
        while a < len(outer) or b < len(inner):
            next_a = angles[a+1] if a+1 < len(outer) else TAU
            next_b = sample_angles[b+1] if b+1 < len(inner) else TAU
            oa, ib = outer[a % len(outer)], inner[b % len(inner)]
            if abs(next_a-next_b) < 1e-10:
                ob, ic = outer[(a+1) % len(outer)], inner[(b+1) % len(inner)]
                triangles.extend(((oa, ob, ic), (oa, ic, ib)))
                a += 1
                b += 1
            elif next_a < next_b:
                triangles.append((oa, outer[(a+1) % len(outer)], ib))
                a += 1
            else:
                triangles.append((oa, inner[(b+1) % len(inner)], ib))
                b += 1

    # The sector weld leaves exactly two global circular boundary loops.
    def circular_loop(radius):
        indices = [i for i, (x, y) in enumerate(vertices)
                   if abs(math.hypot(x, y)-radius) < 1e-8]
        return sorted(indices, key=lambda i: math.atan2(vertices[i][1], vertices[i][0]))

    return {'vertices': vertices, 'triangles': triangles, 'hand_holes': holes,
            'outer_loop': circular_loop(outer_radius),
            'bore_loop': circular_loop(inner_radius),
            'hole_segments': hole_segments, 'hole_count': hole_count}


def solid_annulus(inner_radius, outer_radius, hole_ring_radius, hole_radius,
                  thickness, hole_count=10, hole_segments=8):
    """Closed plate with both faces and all bore/hand-hole walls.

    X is the wheel axis. Independent UV charts use metres; wall U is analytic
    arc length, so High/Low hole segment counts share the same parameterization.
    Charts still need layout/atlas packing before this can become an asset.
    """
    if thickness <= 0:
        raise ValueError('Plate thickness must be positive')
    plane = perforated_annulus(inner_radius, outer_radius, hole_ring_radius,
                               hole_radius, hole_count, hole_segments)
    points = plane['vertices']
    count = len(points)
    vertices = [(x, y, z) for x in (thickness/2, -thickness/2) for y, z in points]
    triangles, uv, charts = [], [], []

    def face(indices, coordinates, chart):
        triangles.append(tuple(indices))
        uv.append(tuple(coordinates))
        charts.append(chart)

    for tri in plane['triangles']:
        face(tri, [points[i] for i in tri], 0)
        back = tuple(reversed(tri))
        face([i+count for i in back], [points[i] for i in back], 1)

    def clockwise(loop):
        return [loop[0]]+list(reversed(loop[1:]))

    loops = [plane['outer_loop'], clockwise(plane['bore_loop'])]
    loops += [clockwise(loop) for loop in plane['hand_holes']]
    names = ['front', 'back', 'outer-wall', 'bore-wall']
    names += ['hand-hole-wall-'+str(i) for i in range(hole_count)]
    for index, loop in enumerate(loops):
        cy = sum(points[i][0] for i in loop)/len(loop)
        cz = sum(points[i][1] for i in loop)/len(loop)
        radius = sum(math.hypot(points[i][0]-cy, points[i][1]-cz) for i in loop)/len(loop)
        start = math.atan2(points[loop[0]][1]-cz, points[loop[0]][0]-cy)
        sign = 1 if index == 0 else -1
        phases = []
        for i in loop:
            a = sign*(math.atan2(points[i][1]-cz, points[i][0]-cy)-start) % TAU
            if a > TAU-1e-9 or a < 1e-9:
                a = 0.0
            phases.append(a*radius)
        if any(b <= a for a, b in zip(phases, phases[1:])):
            raise ValueError('Wall loop is not consistently wound')
        for j, a in enumerate(loop):
            b = loop[(j+1) % len(loop)]
            ua, ub = phases[j], phases[j+1] if j+1 < len(loop) else TAU*radius
            q = (a+count, b+count, b, a)
            tex = ((ua, -thickness/2), (ub, -thickness/2),
                   (ub, thickness/2), (ua, thickness/2))
            face((q[0], q[1], q[2]), (tex[0], tex[1], tex[2]), index+2)
            face((q[0], q[2], q[3]), (tex[0], tex[2], tex[3]), index+2)
    return {'vertices': vertices, 'triangles': triangles, 'uv': uv,
            'face_charts': charts, 'chart_names': names, 'plane': plane}
