"""ADR 0110 step 2d: the kerb's buried flange is not meshed where a verge strip covers it (Low tris budget)."""
p = 'tools/worldgen/roads/meshing.py'
s = open(p, encoding='utf-8').read()
old = '''def _emit_strip(buf, G, OUT, zg, params, kap_toward, hw, flip, br, coarse, src):'''
new = '''def _emit_strip(buf, G, OUT, zg, params, kap_toward, hw, flip, br, coarse, src, noflange=None):'''
assert old in s
s = s.replace(old, new)
old = '''        T = grid_tris(n, 2, flip=flip)
        vertical = rw < 1e-6
        is_flange = vertical and k == nseg - 1 and not coarse
'''
new = '''        T = grid_tris(n, 2, flip=flip)
        vertical = rw < 1e-6
        is_flange = vertical and k == nseg - 1 and not coarse
        if is_flange and noflange is not None and len(T):
            # ADR 0110: behind a verge strip (meshing._emit_verge) the buried flange is never seen - not meshed
            # (about half of all kerb triangles of the region were flanges of kerbs without a sidewalk)
            ts = np.minimum(T.min(1) // 2, n - 2)
            T = T[~(noflange[ts] & noflange[ts + 1])]
'''
assert old in s
s = s.replace(old, new)
# build_side_strip: compute the mask, pass it on
old = '''        _emit_verge(buf, G, N * sgn, zg, np.array([p[1] for p in params]), vw, kap, hw, side == "R",
                    f"{c.id}:{side}:vg")
    kl = [(p[0], p[4] == MAT_FLUSH_ROAD) for p in params]
'''
new = '''        _emit_verge(buf, G, N * sgn, zg, np.array([p[1] for p in params]), vw, kap, hw, side == "R",
                    f"{c.id}:{side}:vg")
        nofl = vw > 0.05
    else:
        nofl = None
    kl = [(p[0], p[4] == MAT_FLUSH_ROAD) for p in params]
'''
assert old in s
s = s.replace(old, new)
old = '''            _emit_strip(buf, G[sl], (N * sgn)[sl], zg[sl], prm, kap[sl], hw[sl], side == "R",
                        br[sl] if br is not None else None, coarse, f"{c.id}:{side}:{r}")
        return
    _emit_strip(buf, G, N * sgn, zg, params, kap, hw, side == "R",
                br, coarse, c.id + ":" + side)
'''
new = '''            _emit_strip(buf, G[sl], (N * sgn)[sl], zg[sl], prm, kap[sl], hw[sl], side == "R",
                        br[sl] if br is not None else None, coarse, f"{c.id}:{side}:{r}",
                        noflange=None if nofl is None else nofl[sl])
        return
    _emit_strip(buf, G, N * sgn, zg, params, kap, hw, side == "R",
                br, coarse, c.id + ":" + side, noflange=nofl)
'''
assert old in s
s = s.replace(old, new)
s = s.replace('kp = dp_keep(P0, 0.01) | dp_keep(P1, 0.015) | dp_keep(P2, 0.02)', 'kp = dp_keep(P0, 0.025) | dp_keep(P1, 0.025) | dp_keep(P2, 0.03)')
s = s.replace('station, the hairline between them is under the tolerance)', 'station, the hairline between them is under the tolerance, 2.5 cm)')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
