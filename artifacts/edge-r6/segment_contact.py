"""Exact piecewise-linear bottom-edge clearance on a triangulated apron.

Run only as part of the heavy contact audit. Evaluating base vertices alone
misses an apron valley between two deliberately buried curtain endpoints.
No alpha/texture coverage or photographic visibility is inferred here.
"""
import numpy as np
import shapely


def profile(points, vertices, ground, projected, tree, tolerance=0.05):
    start, end = np.asarray(vertices, dtype=float)
    en0, en1 = start[[0, 2]], end[[0, 2]]
    delta = en1 - en0
    length = float(np.linalg.norm(delta))
    if length <= 1e-8:
        return None
    line = shapely.LineString([en0, en1])
    length2 = length * length
    faces = []
    knots = [0.0, 1.0]
    for index in tree.query(line):
        a, b, c = projected[index]
        ab, ac = b-a, c-a
        det = ab[0]*ac[1] - ab[1]*ac[0]
        if abs(det) < 1e-8:
            continue
        intersection = shapely.intersection(line, shapely.Polygon(projected[index]))
        coordinates = shapely.get_coordinates(intersection)
        if not len(coordinates):
            continue
        ts = np.clip((coordinates-en0) @ delta / length2, 0.0, 1.0)
        lo, hi = float(ts.min()), float(ts.max())
        ap = np.stack([en0-a, en1-a])
        u = (ap[:, 0]*ac[1] - ap[:, 1]*ac[0])/det
        v = (ab[0]*ap[:, 1] - ab[1]*ap[:, 0])/det
        ys = ground[index, :, 1]
        heights = ys[0]+u*(ys[1]-ys[0])+v*(ys[2]-ys[0])
        faces.append((lo, hi, float(heights[0]), float(heights[1]-heights[0])))
        knots.extend((lo, hi))
    if not faces:
        raise RuntimeError(f'Bottom edge has no apron coverage: {points}')
    covered = 0.0
    for lo, hi, _, _ in sorted(faces):
        if lo > covered+1e-6:
            raise RuntimeError(f'Bottom edge apron coverage gap: {points}: {covered}..{lo}')
        covered = max(covered, hi)
    if covered < 1.0-1e-6:
        raise RuntimeError(f'Bottom edge incomplete apron coverage: {points}: {covered}')
    # Overlapping apron faces need their upper envelope, including any interior
    # crossings. Ordinary shared edges have equal heights and add no crossing.
    for i, first in enumerate(faces):
        for second in faces[i+1:]:
            lo, hi = max(first[0], second[0]), min(first[1], second[1])
            slope = first[3]-second[3]
            if lo <= hi and abs(slope) > 1e-9:
                t = (second[2]-first[2])/slope
                if lo < t < hi:
                    knots.append(t)
    knots = sorted(set(knots))
    ys = []
    for t in knots:
        heights = [origin+slope*t for lo, hi, origin, slope in faces if lo-1e-6 <= t <= hi+1e-6]
        if not heights:
            raise RuntimeError(f'Bottom edge breakpoint not covered: {points}: {t}')
        ys.append(float(start[1]+t*(end[1]-start[1])-max(heights)))
    # Every interval is linear after splitting at triangle edges and envelope
    # crossings, so integrate the fraction above the declared working tolerance.
    exposed = 0.0
    for a, b, ga, gb in zip(knots, knots[1:], ys, ys[1:]):
        ga, gb = ga-tolerance, gb-tolerance
        if max(ga, gb) <= 0:
            continue
        if min(ga, gb) >= 0:
            exposed += b-a
        elif max(ga, gb) > 0:
            exposed += (b-a)*max(ga, gb)/abs(gb-ga)
    worst = int(np.argmax(ys))
    position = start+(end-start)*knots[worst]
    return dict(vertices=list(map(int, points)), length_m=length,
                max_clearance_m=max(ys), min_clearance_m=min(ys),
                length_above_tolerance_m=length*exposed,
                worst_en=[float(position[0]), float(position[2])],
                breakpoint_count=len(knots))


def validate_reference_cases():
    """Independent 2 m tent/valley: endpoints buried, middle exposed 1.5 m."""
    ground = np.array([
        [[0, 2, -1], [0, 2, 1], [1, 0, -1]],
        [[0, 2, 1], [1, 0, 1], [1, 0, -1]],
        [[1, 0, -1], [1, 0, 1], [2, 2, -1]],
        [[1, 0, 1], [2, 2, 1], [2, 2, -1]],
    ], dtype=float)
    en = ground[:, :, [0, 2]]
    tree = shapely.STRtree(shapely.polygons(en))
    result = profile((0, 1), [[0, 1.5, 0], [2, 1.5, 0]], ground, en, tree)
    if abs(result['max_clearance_m']-1.5) > 1e-8 or abs(result['length_above_tolerance_m']-1.45) > 1e-8:
        raise RuntimeError('Independent valley reference failed')
    buried = profile((0, 1), [[0, -1, 0], [2, -1, 0]], ground, en, tree)
    if buried['length_above_tolerance_m'] != 0 or abs(buried['max_clearance_m']+1) > 1e-8:
        raise RuntimeError('Independent buried reference failed')
    try:
        profile((0, 1), [[-1, 1, 0], [2, 1, 0]], ground, en, tree)
    except RuntimeError as error:
        if 'coverage gap' not in str(error):
            raise
    else:
        raise RuntimeError('Uncovered reference edge was silently accepted')
