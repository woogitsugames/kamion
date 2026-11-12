# r4 code changes (applied once; kept for the record): High kit inside the 2.0 M High frame estimate (leader decision B)
p = 'tools/worldgen/streetscape/plots.py'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a)
    s = s.replace(a, b)


# thuja_lite: number of silhouette cards
rep('''def thuja_lite(kit, p, z, h, r, key, dead=False, core=True):''', '''def thuja_lite(kit, p, z, h, r, key, dead=False, core=True, cards=1):''')
rep('''    kit.tris(V, UV, T, C)
    card(kit, pc, z - 0.05, sp, 2.5 * r, h * 1.02, a0 + 0.3)
''', '''    kit.tris(V, UV, T, C)
    for i in range(cards):                                   # cards=2 (High, near the street): 16 triangles
        card(kit, pc, z - 0.05, sp, 2.5 * r, h * 1.02, a0 + 0.3 + i * math.pi / 2)
''')
# _core: 2-ring variant
rep('''def _core(kit, c, z0, rx, h, key, sides=5, occ=0.26):''', '''def _core(kit, c, z0, rx, h, key, sides=5, occ=0.26, rings=3):''')
rep('''    fr = ((0.0, 0.60), (0.40, 1.0), (0.78, 0.66))
    a0 = hfloat(key, "ca") * 6.2832''', '''    fr = ((0.0, 0.60), (0.40, 1.0), (0.78, 0.66)) if rings >= 3 else ((0.0, 0.66), (0.52, 0.98))
    a0 = hfloat(key, "ca") * 6.2832''')
# bush: lighter core, bush_lite
rep('''    20 + 2 * (cards + 2) triangles."""
    p = np.asarray(p, float)
    sp = "shrub_b" if red else "shrub_a"
    occ = 0.86 + 0.14 * hfloat(key, "bo")
    _core(kit, p, z - 0.05, r * 0.52, h * 0.66, key, sides=4, occ=0.26 * occ)''', '''    12 + 2 * (cards + 2) triangles (r4: the core is one band + a cap - the High frame estimate was over 2.0 M)."""
    p = np.asarray(p, float)
    sp = "shrub_b" if red else "shrub_a"
    occ = 0.86 + 0.14 * hfloat(key, "bo")
    _core(kit, p, z - 0.05, r * 0.52, h * 0.66, key, sides=4, occ=0.26 * occ, rings=2)''')
rep('''def fruit_tree(kit, p, z, h, key, r=None):
    """Small orchard''', '''def bush_lite(kit, p, z, r, h, key, red=False):
    """A shrub away from the street (ADR 0132 r4: further than NEAR_FRONT_M from the plot's front edge): two crossed
    cards, 4 triangles - same sprite, size and seed as bush()."""
    sp = "shrub_b" if red else "shrub_a"
    a0 = hfloat(key, "ba") * 6.2832
    for i in range(2):
        card(kit, np.asarray(p, float), z - 0.04, sp, max(2.3 * r, 0.9), h * 1.05, a0 + i * math.pi / 2)


def fruit_tree(kit, p, z, h, key, r=None):
    """Small orchard''')
rep('''    for k in range(3):                                       # limbs into the crown
        az = a0 + 2.0944 * k + 0.5 * (hfloat(key, "fl", k) - 0.5)''', '''    for k in range(2):                                       # limbs into the crown (r4: 2, were 3)
        az = a0 + 3.1416 * k + 0.5 * (hfloat(key, "fl", k) - 0.5)''')
rep('''    _core(kit, cc, zc0 + hc * 0.14, R * 0.50, hc * 0.60, key, sides=5, occ=0.26 * occ)''',
    '''    _core(kit, cc, zc0 + hc * 0.14, R * 0.50, hc * 0.60, key, sides=4, occ=0.26 * occ, rings=2)''')
rep('''    for i in range(6):                                       # lower tier: sprays hanging out and down
        az = a0 + 2 * math.pi * (i + 0.4 * (hfloat(key, "tj", i) - 0.5)) / 6''', '''    for i in range(5):                                       # lower tier: sprays hanging out and down
        az = a0 + 2 * math.pi * (i + 0.4 * (hfloat(key, "tj", i) - 0.5)) / 5''')
rep('''    for i in range(5):                                       # upper tier
        az = a0 + 0.8 + 2 * math.pi * i / 5''', '''    for i in range(4):                                       # upper tier
        az = a0 + 0.8 + 2 * math.pi * i / 4''')
rep('''    bush(kit, p, z, 0.5 * wm * h / hm, h, key, red=red, cards=5)''', '''    bush(kit, p, z, 0.5 * wm * h / hm, h, key, red=red, cards=4)''')
rep('''HEDGE_STEP_M = 1.28           # station pitch of a hedge (SEG_M / 4)''',
    '''HEDGE_STEP_M = 1.92           # station pitch of a hedge (r4: 1.28 -> 1.92, -1/3 of the triangles on every tier)''')
rep('''INST_R_M = 2.3  ''', '''NEAR_FRONT_M = 12.0           # ADR 0132 r4: plants up to this far from the plot's front edge are full volumes on High;
                              # further in they are the lite variants of Low (the truck never gets closer than the street)
INST_R_M = 2.3  ''')
# near()
rep('''        placed = []

        def spot(tag, k, region, clear):''', '''        placed = []
        fr_ls = [LineString([e[0], e[1]]) for e in _edges(poly) if float(e[4] @ plot["front"]) > 0.7]

        def near(q):
            return bool(fr_ls) and min(l.distance(Point(*q)) for l in fr_ls) <= NEAR_FRONT_M

        def spot(tag, k, region, clear):''')
# rows
rep('''                    kit.low = False
                    thuja(kit, p, zf(p), hh, rr, (key, ri, k), dead)
                    kit.low = "only"
                    thuja_lite(kit, p, zf(p), hh, rr, (key, ri, k), dead)
                    kit.low = True
                    placed.append(p)''', '''                    if near(p):
                        kit.low = False
                        thuja_lite(kit, p, zf(p), hh, rr, (key, ri, k), dead, cards=2)
                        kit.low = "only"
                    thuja_lite(kit, p, zf(p), hh, rr, (key, ri, k), dead)
                    kit.low = True
                    placed.append(p)''')
rep('''                        kit.tag, kit.low = "thuja_single", False
                        thuja(kit, p, zf(p), hh, (0.26 + 0.07 * hh) * (0.9 + 0.3 * hfloat(kk, "w")), kk)
                        kit.low = "only"
                        thuja_lite(''', '''                        kit.tag = "thuja_single"
                        if near(p):
                            kit.low = False
                            thuja(kit, p, zf(p), hh, (0.26 + 0.07 * hh) * (0.9 + 0.3 * hfloat(kk, "w")), kk)
                            kit.low = "only"
                        thuja_lite(''')
rep('''                        kit.tag, kit.low = "small_tree", False
                        fruit_tree(kit, p, zf(p), min(max(1.7 + 1.5 * cr_, 3.2), 5.6), kk, r=cr_)
                        kit.low = "only"
                        fruit_tree_lite(''', '''                        kit.tag = "small_tree"
                        if near(p):
                            kit.low = False
                            fruit_tree(kit, p, zf(p), min(max(1.7 + 1.5 * cr_, 3.2), 5.6), kk, r=cr_)
                            kit.low = "only"
                        fruit_tree_lite(''')
rep('''                        bush(kit, p, zf(p), cr_ * 1.05, min(max(1.0 + 1.2 * cr_ + 0.5 * hfloat(kk, "h"), 1.2), 2.6), kk,
                             red=hfloat(kk, "red") < 0.12)''', '''                        (bush if near(p) else bush_lite)(kit, p, zf(p), cr_ * 1.05,
                                                         min(max(1.0 + 1.2 * cr_ + 0.5 * hfloat(kk, "h"), 1.2), 2.6), kk,
                                                         red=hfloat(kk, "red") < 0.12)''')
rep('''                            kit.tag, kit.low = "small_tree", False
                            fruit_tree(kit, p, zf(p), 3.0 + 1.4 * hfloat(key, "tree_h", k), (key, "ft", k))
                            kit.low = "only"
                            fruit_tree_lite(''', '''                            kit.tag = "small_tree"
                            if near(p):
                                kit.low = False
                                fruit_tree(kit, p, zf(p), 3.0 + 1.4 * hfloat(key, "tree_h", k), (key, "ft", k))
                                kit.low = "only"
                            fruit_tree_lite(''')
rep('''                bush(kit, p, zf(p), rr, r["h"] + 0.25 + 0.9 * hfloat(key, "ovh", k), (key, "ov", k), red=hfloat(key, "ovc", k) < 0.1)''',
    '''                (bush if near(p) else bush_lite)(kit, p, zf(p), rr, r["h"] + 0.25 + 0.9 * hfloat(key, "ovh", k), (key, "ov", k),
                                                 red=hfloat(key, "ovc", k) < 0.1)''')
rep('''                    shrub(kit, p, zf(p), 0.8 + 1.1 * hfloat(key, "shrub_h", k), (key, "shr", k))''', '''                    if near(p):
                        shrub(kit, p, zf(p), 0.8 + 1.1 * hfloat(key, "shrub_h", k), (key, "shr", k))
                    else:
                        _h = 0.8 + 1.1 * hfloat(key, "shrub_h", k)
                        _red = hfloat((key, "shr", k), "sh") >= 0.7
                        _wm, _hm = PK.SPRITE_M["shrub_b" if _red else "shrub_a"]
                        bush_lite(kit, p, zf(p), 0.5 * _wm * _h / _hm, _h, (key, "shr", k), red=_red)''')
# tier field for the garden trees (data only; the importer ignores unknown fields)
rep('''"src": f"{src_id}:canopy"})''', '''"src": f"{src_id}:canopy", "tier": "high"})''')
rep('''"lean": 0.02, "src": f"{src_id}:rule"})''', '''"lean": 0.02, "src": f"{src_id}:rule", "tier": "high"})''')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print("ok")
