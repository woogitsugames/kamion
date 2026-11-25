"""fields2-s24: one-off patch of tools/worldgen/streetscape/verge_flora.py (ADR 0334 r2 / 0324 r4), kept as evidence."""
from pathlib import Path

p = Path("tools/worldgen/streetscape/verge_flora.py")
s = p.read_text(encoding="utf-8")


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:70])
    s = s.replace(a, b)


rep('''TEX_W, TEX_H = 1024, 512
TEX_M = 2.0                      # metres of sward one texture width stands for
NT = 4                           # tufts per atlas row (r2); a card maps 1 or 2 whole tufts
TUFT_H = (1.0, 0.72, 0.9, 0.6)   # relative height of the tufts of a row
''', '''# r4 (fields2-s24, critic build #8 P1#7 "ta sama kępa co kilka metrów"): 8 tufts per row instead of 4 (16 shapes with
# the two rows), each with its own character - density, share of dry blades, lean, spread, tone - so two neighbouring
# cards are rarely the same plant. The atlas is twice as wide at the same texel density (an old card of a tile not yet
# rebuilt maps two narrower tufts of the new atlas - still whole tufts).
TEX_W, TEX_H = 2048, 512
TEX_M = 4.0                      # metres of sward one texture width stands for
NT = 8                           # tufts per atlas row; a card maps 1 or 2 whole tufts
TUFT_H = (1.0, 0.72, 0.9, 0.6, 0.82, 1.0, 0.66, 0.94)        # relative height of the tufts of a row
TUFT_DENS = (1.0, 0.8, 1.2, 0.6, 0.45, 1.3, 0.9, 0.7)        # relative number of blades (lush clump .. thin wisp)
TUFT_DRY = (0.08, 0.05, 0.12, 0.10, 0.55, 0.04, 0.25, 0.10)  # share of bleached blades (a dead tuft of last year)
TUFT_LEAN = (0.0, 0.0, 0.0, 0.0, 0.25, -0.20, 0.0, 0.35)     # the whole tuft leans (wind, a wheel)
TUFT_SPREAD = (1.0, 1.0, 1.0, 1.0, 1.3, 0.7, 1.1, 0.8)       # foot spread in the cell
TUFT_TONE = (1.0, 0.94, 1.06, 0.90, 1.10, 0.88, 1.0, 1.05)
''')
rep('''STEP_SLOPE_M = (1.1, 2.6)
''', '''STEP_SLOPE_M = (1.1, 2.6)
# r4: slope tufts stand in groups (a patch the mower left, a damp spot), not one every couple of metres
CLUSTER_M = 9.0                  # correlation length of the groups along the road
CLUSTER_T = 0.60                 # density noise above this = inside a group
STEP_CLUSTER_M = (0.45, 1.20)    # spacing inside a group
LONE_KEEP = 0.10                 # share of the regular candidates kept outside the groups
CROSS_SHARE = 0.20               # group tufts with a second card along the road (volume from the side)
TONE = (0.78, 1.04)              # per-card brightness (foliage occlusion scale)
''')
rep('''        cw = W / NT
        for _ in range(n):
            k = int(rng.integers(0, NT))
            off = float(np.clip(rng.normal(0, 0.14), -0.30, 0.30))          # foot offset in the cell (x cell width)
''', '''        cw = W / NT
        pk = np.asarray(TUFT_DENS, float) / sum(TUFT_DENS)
        for _ in range(n * NT // 4):
            k = int(rng.choice(NT, p=pk))
            off = float(np.clip(rng.normal(0, 0.14 * TUFT_SPREAD[k]), -0.30, 0.30))   # foot offset in the cell (x cell width)
''')
rep('''            lean = off * 1.6 + rng.normal(0, 0.10)                           # blades fan out of the tuft
''', '''            lean = off * 1.6 + rng.normal(0, 0.10) + TUFT_LEAN[k]            # blades fan out of the tuft
''')
rep('''            c = dry if rng.random() < 0.10 else greens[int(rng.integers(0, len(greens)))]
            if rng.random() < base_share:
                c = dark * rng.uniform(0.9, 1.6)
''', '''            c = dry if rng.random() < TUFT_DRY[k] else greens[int(rng.integers(0, len(greens)))]
            if rng.random() < base_share:
                c = dark * rng.uniform(0.9, 1.6)
            c = c * TUFT_TONE[k]
''')
rep('''    C += [_fol(nrm, OCC[0])] * 2 + [_fol(nrm, OCC[1])] * 2
''', '''    tone = TONE[0] + (TONE[1] - TONE[0]) * _h(*key, "tn")
    C += [_fol(nrm, OCC[0] * tone)] * 2 + [_fol(nrm, OCC[1] * tone)] * 2
''')
rep('''            # ---- slopes: medium tufts, sparse
            x = _h(src, k, "s0") * STEP_SLOPE_M[0]
            q = 0
            while x < L:
                key = (src, k, "s", q)
                front = _h(*key, "f") < 0.5
                lo, hi = (ug + 0.15, ub0) if front else (ub1, uc - 0.1)
                if hi - lo > 0.25:
                    lat = lo + (hi - lo) * _h(*key, "l")
                    ang = (_h(*key, "a") - 0.5) * 1.6
                    h = H_SLOPE[0] + (H_SLOPE[1] - H_SLOPE[0]) * _h(*key, "h")
                    _card(sec, k, x / L, lat, ang, min(W_CARD[1], 0.9), h, V_TALL, key, V, UV, C, T)
                    ncard["slope"] += 1
                x += STEP_SLOPE_M[0] + (STEP_SLOPE_M[1] - STEP_SLOPE_M[0]) * _h(*key, "s")
                q += 1
''', '''            # ---- slopes: medium tufts in groups (r4), a lone one now and then
            x = _h(src, k, "s0") * STEP_SLOPE_M[0]
            q = 0
            while x < L:
                key = (src, k, "s", q)
                grp = _vnoise(src + ":s", sec.ch[k] + x, CLUSTER_M)
                inside = grp > CLUSTER_T
                front = _h(*key, "f") < 0.5
                lo, hi = (ug + 0.15, ub0) if front else (ub1, uc - 0.1)
                if hi - lo > 0.25 and (inside or _h(*key, "k") < LONE_KEEP):
                    lat = lo + (hi - lo) * _h(*key, "l")
                    ang = (_h(*key, "a") - 0.5) * 1.6
                    h = (H_SLOPE[0] + (H_SLOPE[1] - H_SLOPE[0]) * _h(*key, "h")) * (0.70 + 0.70 * _h(*key, "hv") ** 2)
                    if inside:
                        h *= 0.85 + 0.5 * (grp - CLUSTER_T) / (1.0 - CLUSTER_T)        # taller in the heart of a group
                    w = W_CARD[0] + (min(W_CARD[1], 0.95) - W_CARD[0]) * _h(*key, "w")
                    _card(sec, k, x / L, lat, ang, w, h, V_TALL, key, V, UV, C, T)
                    ncard["slope"] += 1
                    if inside and _h(*key, "x") < CROSS_SHARE:
                        _card(sec, k, x / L, lat, math.pi / 2 + (_h(*key, "b") - 0.5) * 0.8, w, h * 0.9, V_TALL,
                              key + ("x",), V, UV, C, T)
                        ncard["slope"] += 1
                st = STEP_CLUSTER_M if inside else STEP_SLOPE_M
                x += st[0] + (st[1] - st[0]) * _h(*key, "s")
                q += 1
''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
