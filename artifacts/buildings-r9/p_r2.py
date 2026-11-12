# r2 code changes (applied once; kept for the record)
p='tools/worldgen/streetscape/plots.py'
s=open(p,encoding='utf-8').read()
def rep(a,b):
    global s
    assert a in s, a
    s=s.replace(a,b)
rep('''            g0 = min(max(g0, 0.3), L - grp - 0.3)
''','''            g0 = _snap_corner(min(max(g0, 0.3), L - grp - 0.3), grp, L)
''')
rep('''            g0 = min(max(sg - gslot / 2, 0.3), L - gslot - 0.3)
''','''            g0 = _snap_corner(min(max(sg - gslot / 2, 0.3), L - gslot - 0.3), gslot, L)
''')
rep('''def layout(plot, cut=None''','''CORNER_SNAP_M = 0.9           # a gate group closer than this to the end of the front edge moves onto the corner


def _snap_corner(g0, w, L):
    """ADR 0132 (review 0124 P1-d, r16_drive_3): a gate 0.3 m short of the plot corner left a gap no fence panel fits
    (stretches under 0.6 m are not built) - the side fence then started in the air beside the gate post. The outer
    gate post IS the corner post now."""
    if g0 < CORNER_SNAP_M:
        return 0.0
    if L - (g0 + w) < CORNER_SNAP_M:
        return L - w
    return g0


def layout(plot, cut=None''')
rep('''INST_SPECIES = [("birch", 0.32), ("linden", 0.22), ("maple", 0.22), ("pine", 0.14), ("alder", 0.10)]   # WORKING_VALUE mix''',
    '''INST_SPECIES = [("birch", 0.34), ("linden", 0.26), ("maple", 0.26), ("pine", 0.14)]   # WORKING_VALUE mix
# one model variant per species (r1 used all 3 x 5 species: every prototype x LOD in view is 1-3 instanced draws, the
# worst house-street camera on Low gained +17); yaw, height and lean still differ from tree to tree
INST_VARIANT = {"birch": 1, "linden": 0, "maple": 2, "pine": 1}''')
rep('''                        trees.append({"p": f"tree_{sp}", "v": int(hfloat(kk, "v") * 3) % 3, "e": round(float(p[0]), 2),''',
    '''                        trees.append({"p": f"tree_{sp}", "v": INST_VARIANT[sp], "e": round(float(p[0]), 2),''')
rep('''                            trees.append({"p": f"tree_{sp}", "v": int(hfloat(key, "bv", k) * 3) % 3, "e": round(float(p[0]), 2),''',
    '''                            trees.append({"p": f"tree_{sp}", "v": INST_VARIANT[sp], "e": round(float(p[0]), 2),''')
rep('''INST_H_M = {"birch": (8.0, 19.0), "linden": (8.0, 18.0), "maple": (7.5, 16.0), "pine": (11.0, 22.0), "alder": (8.0, 17.0)}''',
    '''INST_H_M = {"birch": (8.0, 19.0), "linden": (8.0, 18.0), "maple": (7.5, 16.0), "pine": (11.0, 22.0)}''')
open(p,'w',encoding='utf-8').write(s)
p='tools/worldgen/streetscape/buildings_mesh.py'
s=open(p,encoding='utf-8').read()
rep('''LOD1_HOUSE_FRAME_M = 0.07 ''','''LOD1_HOUSE_FRAME_M = 0.12 ''')
open(p,'w',encoding='utf-8').write(s)
p='artifacts/buildings-r9/plan_dry.py'
s=open(p,encoding='utf-8').read()
rep('''TREES = out["trees"]''','''TREES = out["trees"]
for p_ in P:                       # ends of the fence runs that join nothing (diagnosis of free-standing panels)
    g_ = p_["lay"]["gate"]
    if g_ is None:
        continue
    ends = [(r_["a"], r_) for r_ in p_["lay"]["runs"]] + [(r_["b"], r_) for r_ in p_["lay"]["runs"]]
    d_ = sorted((float(np.hypot(*(e_ - (g_["m"] + g_["t"] * sx * (g_["w"] / 2 + 2 * g_["ph"]))))), sx) for e_, r_ in ends for sx in (-1, 1))
    gaps = [round(min(float(np.hypot(*(e_ - (g_["m"] + g_["t"] * sx * (g_["w"] / 2 + 2 * g_["ph"])))) for e_, r_ in ends), 2) for sx in (-1, 1)]
    if max(gaps) > 0.25:
        print("gate post gap", p_["id"][-12:], p_["front_style"], gaps)''')
open(p,'w',encoding='utf-8').write(s)
