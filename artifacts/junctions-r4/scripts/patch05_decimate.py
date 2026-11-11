"""ADR 0110 step 3b / 2c: Douglas-Peucker on guardrail beams and verge strips (Low tris budget: b2 +5...+15 % per frame)."""
p = 'tools/worldgen/roads/geom.py'
s = open(p, encoding='utf-8').read()
s = s.rstrip('\n') + '''


def dp_keep(P, tol):
    """Douglas-Peucker: boolean mask of the points of polyline P (n, 2 or 3) kept so that no dropped point lies
    further than `tol` from the simplified line (ADR 0110: guardrail beams and verge strips were meshed at every
    1 m station also on straights)."""
    P = np.asarray(P, float)
    n = len(P)
    keep = np.zeros(n, bool)
    if n == 0:
        return keep
    keep[[0, n - 1]] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        ab = P[b] - P[a]
        l2 = float(ab @ ab)
        q = P[a + 1:b] - P[a]
        if l2 < 1e-18:
            d2 = (q * q).sum(1)
        else:
            t = np.clip((q @ ab) / l2, 0.0, 1.0)
            r = q - t[:, None] * ab[None, :]
            d2 = (r * r).sum(1)
        k = int(d2.argmax())
        if d2[k] > tol * tol:
            m = a + 1 + k
            keep[m] = True
            stack.append((a, m))
            stack.append((m, b))
    return keep
'''
open(p, 'w', encoding='utf-8', newline='\n').write(s)

p = 'tools/worldgen/roads/meshing.py'
s = open(p, encoding='utf-8').read()
old = '''    T = grid_tris(n, 2, flip=flip)
    for A, B, ua, ub, fp in ((P0, P1, u0, u1, True), (P1, P2, u1, u2, False)):'''
new = '''    # straights: one quad per run (Douglas-Peucker on the three edge lines, 1-2 cm; the kerb beside it keeps every
    # station, the hairline between them is under the tolerance)
    from .geom import dp_keep
    kp = dp_keep(P0, 0.01) | dp_keep(P1, 0.015) | dp_keep(P2, 0.02)
    P0, P1, P2, u0, u1, u2, along = P0[kp], P1[kp], P2[kp], u0[kp], u1[kp], u2[kp], along[kp]
    n = len(P0)
    T = grid_tris(n, 2, flip=flip)
    for A, B, ua, ub, fp in ((P0, P1, u0, u1, True), (P1, P2, u1, u2, False)):'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)

p = 'tools/worldgen/streetscape/furniture.py'
s = open(p, encoding='utf-8').read()
old = '''                zt = Z[k:kk + 1]
                lin.ribbon("barrier_steel", P[k:kk + 1], zt + S.BRIDGE_BARRIER_MID - 0.03, zt + S.BRIDGE_BARRIER_MID + 0.03,
                           0.03, key)
                lin.slab("barrier_steel", P[k:kk + 1], zt + S.BRIDGE_BARRIER_H - 0.06, zt + S.BRIDGE_BARRIER_H, 0.06, key)'''
new = '''                kp = dp_keep(np.column_stack([P[k:kk + 1], Z[k:kk + 1]]), 0.01)
                Pt, zt = P[k:kk + 1][kp], Z[k:kk + 1][kp]
                lin.ribbon("barrier_steel", Pt, zt + S.BRIDGE_BARRIER_MID - 0.03, zt + S.BRIDGE_BARRIER_MID + 0.03,
                           0.03, key)
                lin.slab("barrier_steel", Pt, zt + S.BRIDGE_BARRIER_H - 0.06, zt + S.BRIDGE_BARRIER_H, 0.06, key)'''
assert old in s
s = s.replace(old, new)
old = '''    d = np.gradient(P, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    # W profile (two bulges toward the road side, +nrm): 5 points of the 0.31 m high beam
    prof = [(0.0, -0.31), (0.05, -0.24), (0.0, -0.155), (0.05, -0.07), (0.0, 0.0)]
    rows = []
    for o, dz in prof:
        rows.append(np.column_stack([P + nrm * (0.08 + o), Z + top + dz]))
    V = np.concatenate(rows)'''
new = '''    d = np.gradient(P, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    # ADR 0110: the beam keeps only the points a 1 cm Douglas-Peucker needs (it was meshed every metre: 16 triangles
    # per metre also on straights; the posts above keep their spacing)
    kp = dp_keep(np.column_stack([P, Z + top]), 0.01)
    P, Z, top, nrm = P[kp], Z[kp], top[kp], nrm[kp]
    n = len(P)
    # W profile (two bulges toward the road side, +nrm): 5 points of the 0.31 m high beam
    prof = [(0.0, -0.31), (0.05, -0.24), (0.0, -0.155), (0.05, -0.07), (0.0, 0.0)]
    rows = []
    for o, dz in prof:
        rows.append(np.column_stack([P + nrm * (0.08 + o), Z + top + dz]))
    V = np.concatenate(rows)'''
assert old in s
s = s.replace(old, new)
old = '''from roads.network import MEDIAN_RURAL, RURAL, URBAN, side_params, side_extent
'''
new = old + '''from roads.geom import dp_keep
'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
