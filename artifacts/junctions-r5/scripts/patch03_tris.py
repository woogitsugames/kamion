"""ADR 0117 patch 03 (applied once): triangle budget of the barriers - flanges single-sided, spacer sides only, foot
plate top only, upper beam without underside, back of the W sheet as two facets, Douglas-Peucker 2 cm."""
import pathlib
p = pathlib.Path('tools/worldgen/streetscape/furniture.py')
s = p.read_text(encoding='utf-8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)


rep('''        quads.append(([P3(f, fl / 2, z0), P3(f, -fl / 2, z0), P3(f, -fl / 2, z1), P3(f, fl / 2, z1)], uv(0.0, fl, h)))
        quads.append(([P3(f, -fl / 2, z0), P3(bk, -fl / 2, z0), P3(bk, -fl / 2, z1), P3(f, -fl / 2, z1)],
                      uv(0.1, 0.1 + dep, h)))
        quads.append(([P3(bk, -fl / 2, z0), P3(bk, fl / 2, z0), P3(bk, fl / 2, z1), P3(bk, -fl / 2, z1)],
                      uv(0.3, 0.3 + fl, h)))
    _quads(lin, "furniture", POST_MAT, quads, key, both=True)
    solid = []''', '''        # web from both sides; the flanges only from outside (ADR 0117 budget: 8 triangles per post)
        quads.append(([P3(f, -fl / 2, z0), P3(bk, -fl / 2, z0), P3(bk, -fl / 2, z1), P3(f, -fl / 2, z1)],
                      uv(0.1, 0.1 + dep, h)))
        flanges.append(([P3(f, fl / 2, z0), P3(f, -fl / 2, z0), P3(f, -fl / 2, z1), P3(f, fl / 2, z1)], uv(0.0, fl, h)))
        flanges.append(([P3(bk, -fl / 2, z0), P3(bk, fl / 2, z0), P3(bk, fl / 2, z1), P3(bk, -fl / 2, z1)],
                        uv(0.3, 0.3 + fl, h)))
    _quads(lin, "furniture", POST_MAT, quads, key, both=True)
    solid = flanges''')
rep('''    quads = []
    dep, fl = POST_C_DECK if deck else POST_C''', '''    quads, flanges = [], []
    dep, fl = POST_C_DECK if deck else POST_C''')
rep('''        solid.append(([P3(POST_FRONT, a_, zs1), P3(W_BACK, a_, zs1), P3(W_BACK, -a_, zs1), P3(POST_FRONT, -a_, zs1)],
                      ((u, 0.30), (u + 0.1, 0.30), (u + 0.1, 0.39), (u, 0.39))))
''', '')
rep('''            solid.append(([P3(f0, a_, z), P3(f0, -a_, z), P3(f0, -a_, z + th), P3(f0, a_, z + th)],
                          ((u + 0.2, 0.0), (u + 0.42, 0.0), (u + 0.42, 0.02), (u + 0.2, 0.02))))
''', '')
rep('''                for (o0, z0), (o1, z1), v0 in zip(box, box[1:] + box[:1], uvv):''',
    '''                for (o0, z0), (o1, z1), v0 in list(zip(box, box[1:] + box[:1], uvv))[:2] + [(box[3], box[0], uvv[3])]:''')
rep('''                kp = dp_keep(np.column_stack([P[k:kk + 1], Z[k:kk + 1] + zt]), 0.01)''',
    '''                kp = dp_keep(np.column_stack([P[k:kk + 1], Z[k:kk + 1] + zt]), RAIL_DP_M)''')
rep('''    kp = dp_keep(np.column_stack([P, Z + top]), 0.01)''', '''    kp = dp_keep(np.column_stack([P, Z + top]), RAIL_DP_M)''')
rep('''    lin.buf.add("furniture", "barrier_steel", V, UV, T, src=key)
    lin.buf.add("furniture", "barrier_steel", V, UV, T[:, [0, 2, 1]], src=key)
    if tall.any() or key.endswith(":structure"):''', '''    lin.buf.add("furniture", "barrier_steel", V, UV, T, src=key)
    # back of the sheet: two facets (top edge - valley - bottom edge); the folds are a road-side thing (budget)
    bi = [0, 5, 6, 11]
    Vb = np.concatenate([rows[i] for i in bi])
    UVb = np.column_stack([np.tile(s, 4), np.repeat([uvr[i] for i in bi], n)])
    Tb = []
    for r in (0, 2):
        a, b = r * n, (r + 1) * n
        Tb += [(a + k, b + k + 1, a + k + 1) for k in range(n - 1)] + [(a + k, b + k, b + k + 1) for k in range(n - 1)]
    lin.buf.add("furniture", "barrier_steel", Vb, UVb, np.array(Tb), src=key)
    if tall.any() or key.endswith(":structure"):''')
rep('''POST_U0 = 1.3
''', '''POST_U0 = 1.3
RAIL_DP_M = 0.02            # Douglas-Peucker tolerance of the beams (ADR 0110: 0.01; 0117: 6 facets instead of 4 strips)
''')
p.write_text(s, encoding='utf-8', newline='\n')

p = pathlib.Path('tests/gis/test_junctions_r4.py')
s = p.read_text(encoding='utf-8')
rep('len(p.V) % 24 == 0 and len(p.T) == len(p.V) // 2', 'len(p.V) % 8 == 0 and len(p.T) == len(p.V) // 2')
rep('three thin plates per post drawn from both sides = 24 vertices / 12 triangles (ADR 0117)',
    'the web of each post drawn from both sides = 8 vertices / 4 triangles (ADR 0117; flanges: a single-sided part)')
s = s.replace("len(posts.V) // 24", "len(posts.V) // 8").replace("len(deck_posts.V) // 24", "len(deck_posts.V) // 8")
p.write_text(s, encoding='utf-8', newline='\n')
print("patched")
