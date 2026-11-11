"""ADR 0110 step 2b: verge strips - tapered ends, slope kept on the inside of curves, none on jagged corners, strict
cull on carriageways (b1: terrain_walls 3 -> 884, marking_off_carriageway 2 -> 11)."""
p = 'tools/worldgen/roads/meshing.py'
s = open(p, encoding='utf-8').read()
old = '''    VW[VW < 0.05] = 0.0
    tw = S.KERB_TOP_W
'''
new = '''    VW[VW < 0.05] = 0.0
    along = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(G, axis=0).T))])
    # ends: the strip and its skirt run out over 2 m (a strip that stopped within one station next to a dense corner
    # arc left a near-vertical grass face, terrain_walls b1)
    zero = np.where(VW <= 0.0)[0]
    dist = np.full(n, 1e9) if not len(zero) else np.abs(along[:, None] - along[zero][None, :]).min(1)
    VW = np.minimum(VW, 0.5 * dist)
    depth = np.minimum(S.FLANGE_DEPTH, 0.25 * dist)
    tw = S.KERB_TOP_W
'''
assert old in s
s = s.replace(old, new)
old = '''    u2 = u1 + np.where(on, S.FLANGE_DEPTH * S.EMBANKMENT_SLOPE, 0.0) * scale
    z0 = zg + H
    z1 = z0 + S.SIDEWALK_CROSSFALL * VW
    z2 = z1 - np.where(on, S.FLANGE_DEPTH, 0.0)
'''
new = '''    depth = np.where(on, depth, 0.0) * scale          # squeezed on the inside of a curve: shallower, same 1:1.5 slope
    u2 = u1 + depth * S.EMBANKMENT_SLOPE
    z0 = zg + H
    z1 = z0 + S.SIDEWALK_CROSSFALL * VW
    z2 = z1 - depth
'''
assert old in s
s = s.replace(old, new)
old = '''    along = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(G, axis=0).T))])
    T = grid_tris(n, 2, flip=flip)
    for A, B, ua, ub, fp in ((P0, P1, u0, u1, True), (P1, P2, u1, u2, False)):'''
new = '''    T = grid_tris(n, 2, flip=flip)
    for A, B, ua, ub, fp in ((P0, P1, u0, u1, True), (P1, P2, u1, u2, False)):'''
assert old in s
s = s.replace(old, new)
old = '''            vw = np.array([v if (q[0] == URBAN and q[2] < 0.05 and q[4] == 0 and q[1] > 0.05) else 0.0
                           for v, q in zip(cv, params)])
'''
new = '''            vw = np.array([v if (q[0] == URBAN and q[2] < 0.05 and q[4] == 0 and q[1] > 0.05) else 0.0
                           for v, q in zip(cv, params)])
            # a corner whose kerb line jumps in height (plates of two levels meeting: j:n2591872092, +-1 m between
            # stations) gets no grass - the strip would repeat the jumps as 1-2 m grass faces
            dsz = np.maximum(np.hypot(*np.diff(G, axis=0).T), 0.25)
            if len(Z) > 1 and float(np.max(np.abs(np.diff(Z)) / dsz)) > 0.15:
                vw[:] = 0.0
'''
assert old in s
s = s.replace(old, new)
old = '''        tri = p.V[p.T]
        cen = tri.mean(1)
        drop = on_cw(cen)
        if kerb:'''
new = '''        tri = p.V[p.T]
        cen = tri.mean(1)
        drop = on_cw(cen)
        if p.src.endswith(":vg"):
            # ADR 0110: grass behind a kerb never lies on a carriageway, not even with one vertex (a strip reaching
            # onto the lane of a merging road stood 0.13 m above its asphalt: marking_off_carriageway 2 -> 11 in b1)
            for k in range(3):
                drop |= on_cw(tri[:, k] + (cen - tri[:, k]) * 0.05)
        elif kerb:'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
