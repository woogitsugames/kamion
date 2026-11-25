"""fields2-s24: one-off patch of tools/worldgen/streetscape/vegetation.py (ADR 0334 r2), kept as evidence."""
from pathlib import Path

p = Path("tools/worldgen/streetscape/vegetation.py")
s = p.read_text(encoding="utf-8")


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (s.count(a), a[:60])
    s = s.replace(a, b)


# --- layout mirror: wobble
rep('''FIELD_DISTRICT_M = 1600.0       # KF_DISTRICT_M''', '''# ADR 0334 r2 (fields2-s24): KF_WOB_* - the strip coordinate meanders (cell m, amplitude m peak-to-peak, shader salt)
FIELD_WOBBLE = ((47.0, 2.4, 983), (17.0, 1.4, 953), (5.0, 0.5, 951))


def _kf_noise(x, y, s, salt):
    """KFNoise of the shader: value noise on an EPSG:2180 lattice of s metres, 0..1."""
    gx, gy = np.floor(x / s), np.floor(y / s)
    fx, fy = x / s - gx, y / s - gy
    fx, fy = fx * fx * (3.0 - 2.0 * fx), fy * fy * (3.0 - 2.0 * fy)
    a, b = _u01(_h32(gx, gy, salt)), _u01(_h32(gx + 1, gy, salt))
    c, d = _u01(_h32(gx, gy + 1, salt)), _u01(_h32(gx + 1, gy + 1, salt))
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def field_wobble(x, y):
    """Metres added to the across-strip coordinate at EPSG:2180 x, y (the shader's `wob`): the strip edges meander."""
    x, y = np.asarray(x, np.float64), np.asarray(y, np.float64)
    return sum((_kf_noise(x, y, s, salt) - 0.5) * a for s, a, salt in FIELD_WOBBLE)


FIELD_DISTRICT_M = 1600.0       # KF_DISTRICT_M''')
rep('''    t = (rx * np.cos(th) + ry * np.sin(th)) / w
    k = np.floor(t)''', '''    wob = field_wobble(x, y)
    t = (rx * np.cos(th) + ry * np.sin(th) + wob) / w
    k = np.floor(t)''')
rep('''            "w": w, "th": th, "block_edge": block_edge, "sx": sx, "sy": sy}''',
    '''            "w": w, "th": th, "block_edge": block_edge, "sx": sx, "sy": sy, "wob": wob}''')
rep('''per block), width w; across = projection of (P - block seed) on the normal, modulo w.''',
    '''per block), width w; across = projection of (P - block seed) on the normal plus field_wobble (r2), modulo w.''')

# --- plants
rep('''BAULK_SPECIES = (("shrub", 0.76), ("birchyoung", 0.12), ("pineyoung", 0.05), ("birch", 0.04), ("alder", 0.03))
''', '''BAULK_SPECIES = (("shrub", 0.76), ("birchyoung", 0.12), ("pineyoung", 0.05), ("birch", 0.04), ("alder", 0.03))
# ADR 0334 r2 (fields2-s24, critic build #8 P1#7 "samotne drzewka równo rozsiane na polach"). WORKING_VALUE.
# A run of scrub is not a row of evenly spaced bushes: thickets of ~3 cells with thin stretches between them, and a
# second bush beside some of the thicket's plants. Trees in the open field stand in clumps on a baulk (kępy
# śródpolne: a few birches / alders / a pine with scrub under them), not one sapling per hectare.
BAULK_THICKET_CELLS = 3
BAULK_THICKET_SHARE = 0.6       # share of the 3-cell groups of a run that are a thicket
BAULK_THIN_KEEP = 0.35          # candidates kept in the thin stretches of a run
BAULK_PAIR_SHARE = 0.40         # thicket plants with a companion shrub 1.2-2.6 m along the baulk
CLUMP_CELL_M = 220.0            # EPSG:2180 lattice of the clump candidates
CLUMP_SHARE = 0.30              # cells with a clump
CLUMP_SIZE = (3, 8)             # plants per clump
CLUMP_SIGMA_M = (5.0, 1.2)      # scatter along / across the baulk
CLUMP_SPECIES = (("birch", 0.30), ("shrub", 0.30), ("birchyoung", 0.15), ("alder", 0.15), ("pine", 0.10))
''')
rep('''        jit = (_u01(_h32(bid, kE * 4099 + cell, 959)) - 0.5) * 0.7 * BAULK_CELL_M
        lat = (_u01(_h32(bid, kE * 4099 + cell, 960)) - 0.5) * 0.6
        s_c = (cell + 0.5) * BAULK_CELL_M + jit
        n = kE * w + lat
        qx = sx + n * np.cos(th) - s_c * np.sin(th)
        qy = sy + n * np.sin(th) + s_c * np.cos(th)
        Lq = field_layout(qx, qy)
        same = (Lq["bid"] == bid.astype(np.uint32)) & (Lq["block_edge"] > 3.0)
        seg = np.floor(s_c / BAULK_SEG_M)
        run = _u01(_h32(bid, kE * 4099 + seg, 961)) < BAULK_SEG_SHARE
        u = _u01(_h32(bid, kE * 4099 + cell, 963))
        sel = same & (u < np.where(run, BAULK_RUN_KEEP, BAULK_LONE_KEEP))
        Q = np.column_stack([qx - ox, qy - oy])[sel]
        ok = keep_ok(Q)
        hs = _h32(bid[sel], kE[sel] * 4099 + cell[sel], 965)
        sp = _pick_species(BAULK_SPECIES, _u01(hs))
        for q, s_, h, g in zip(Q, sp, hs, ok):
            if g:
                out.append((q, s_, int(h), "baulk"))
''', '''        jit = (_u01(_h32(bid, kE * 4099 + cell, 959)) - 0.5) * 0.7 * BAULK_CELL_M
        lat = (_u01(_h32(bid, kE * 4099 + cell, 960)) - 0.5) * 0.6
        s_c = (cell + 0.5) * BAULK_CELL_M + jit
        n = kE * w + lat

        def on_edge(n_, s_, m=slice(None)):
            # the point n_ metres across (wobbled strip coordinate, r2) and s_ along: fixed point of the wobble
            # (its Lipschitz constant is ~0.35, six rounds leave < 1 cm)
            c_, sn_, bx, by = np.cos(th[m]), np.sin(th[m]), sx[m], sy[m]
            x_, y_ = bx + n_ * c_ - s_ * sn_, by + n_ * sn_ + s_ * c_
            for _ in range(6):
                d_ = n_ - field_wobble(x_, y_)
                x_, y_ = bx + d_ * c_ - s_ * sn_, by + d_ * sn_ + s_ * c_
            return x_, y_

        qx, qy = on_edge(n, s_c)
        Lq = field_layout(qx, qy)
        same = (Lq["bid"] == bid.astype(np.uint32)) & (Lq["block_edge"] > 3.0)
        # r2: a baulk exists only between two holdings (the shader's hasBaulk): one of the two strips has its own use
        zero = np.zeros(len(bid))
        own_lo = _u01(_h32(_h32(bid, kE - 1, 929).astype(np.float64), zero, 931)) < FIELD_OWN_SHARE_SHADER
        own_hi = _u01(_h32(_h32(bid, kE, 929).astype(np.float64), zero, 931)) < FIELD_OWN_SHARE_SHADER
        same &= own_lo | own_hi
        seg = np.floor(s_c / BAULK_SEG_M)
        run = _u01(_h32(bid, kE * 4099 + seg, 961)) < BAULK_SEG_SHARE
        thick = _u01(_h32(bid, kE * 4099 + np.floor(cell / BAULK_THICKET_CELLS), 981)) < BAULK_THICKET_SHARE
        u = _u01(_h32(bid, kE * 4099 + cell, 963))
        sel = same & (u < np.where(run, np.where(thick, BAULK_RUN_KEEP, BAULK_THIN_KEEP), BAULK_LONE_KEEP))
        Q = np.column_stack([qx - ox, qy - oy])[sel]
        ok = keep_ok(Q)
        hs = _h32(bid[sel], kE[sel] * 4099 + cell[sel], 965)
        sp = _pick_species(BAULK_SPECIES, _u01(hs))
        for q, s_, h, g in zip(Q, sp, hs, ok):
            if g:
                out.append((q, s_, int(h), "baulk"))
        # companion shrubs of the thicket plants
        pair = sel & run & thick & (_u01(_h32(bid, kE * 4099 + cell, 982)) < BAULK_PAIR_SHARE)
        if pair.any():
            ds = (1.2 + 1.4 * _u01(_h32(bid, kE * 4099 + cell, 984))) * np.where(_u01(_h32(bid, kE * 4099 + cell, 986)) < 0.5, -1.0, 1.0)
            px, py = on_edge((kE * w - lat)[pair], (s_c + ds)[pair], pair)
            Lp = field_layout(px, py)
            Q2 = np.column_stack([px - ox, py - oy])
            ok2 = keep_ok(Q2) & (Lp["bid"] == bid[pair].astype(np.uint32)) & (Lp["block_edge"] > 3.0)
            hs2 = _h32(bid[pair], kE[pair] * 4099 + cell[pair], 988)
            for q, h, g in zip(Q2, hs2, ok2):
                if g:
                    out.append((q, "shrub", int(h), "baulk"))
    # --- r2 clumps (kępy śródpolne): a lattice of candidates in EPSG:2180, each snapped to the nearest strip edge
    cm = CLUMP_CELL_M
    ci, cj = np.meshgrid(np.arange(np.floor((x0 + ox - 40.0) / cm), np.floor((x0 + W + ox + 40.0) / cm) + 1),
                         np.arange(np.floor((y1 - H + oy - 40.0) / cm), np.floor((y1 + oy + 40.0) / cm) + 1))
    ci, cj = ci.ravel(), cj.ravel()
    on = _u01(_h32(ci, cj, 990)) < CLUMP_SHARE
    ci, cj = ci[on], cj[on]
    if len(ci):
        cx = (ci + 0.1 + 0.8 * _u01(_h32(ci, cj, 992))) * cm
        cy = (cj + 0.1 + 0.8 * _u01(_h32(ci, cj, 994))) * cm
        Lc = field_layout(cx, cy)
        dn = np.where(Lc["across"] < 0.5 * Lc["w"], -Lc["across"], Lc["w"] - Lc["across"])
        cx, cy = cx + dn * np.cos(Lc["th"]), cy + dn * np.sin(Lc["th"])
        cnt = CLUMP_SIZE[0] + np.floor(_u01(_h32(ci, cj, 996)) * (CLUMP_SIZE[1] - CLUMP_SIZE[0] + 1)).astype(int)
        for i in range(len(ci)):
            if not (shapely.contains_xy(inner, cx[i] - ox, cy[i] - oy) and Lc["block_edge"][i] > 6.0):
                continue
            m = np.arange(cnt[i], dtype=np.float64)
            a_, b_ = np.full(len(m), ci[i] * 8191.0 + cj[i]), m
            # two uniforms -> a roughly normal offset (sum of two), along and across the baulk
            ga = (_u01(_h32(a_, b_, 998)) + _u01(_h32(a_, b_, 1000)) - 1.0) * 2.45
            gb = (_u01(_h32(a_, b_, 1002)) + _u01(_h32(a_, b_, 1004)) - 1.0) * 2.45
            c_, s_ = np.cos(Lc["th"][i]), np.sin(Lc["th"][i])
            mx = cx[i] + gb * CLUMP_SIGMA_M[1] * c_ - ga * CLUMP_SIGMA_M[0] * s_
            my = cy[i] + gb * CLUMP_SIGMA_M[1] * s_ + ga * CLUMP_SIGMA_M[0] * c_
            Q = np.column_stack([mx - ox, my - oy])
            hs = _h32(a_, b_, 1006)
            sp = _pick_species(CLUMP_SPECIES, _u01(hs))
            for q, sn, h, g in zip(Q, sp, hs, keep_ok(Q)):
                if g:
                    out.append((q, sn, int(h), "clump"))
''')
rep('''    report["field_plants"] = {"baulk": sum(1 for t in out[n0:] if t["src"] == "field:baulk"),
''', '''    report["field_plants"] = {"baulk": sum(1 for t in out[n0:] if t["src"] == "field:baulk"),
                              "clump": sum(1 for t in out[n0:] if t["src"] == "field:clump"),
''')
rep('''                d_edge = shapely.distance(shapely.points(P), poly.boundary)
                P = P[u < np.where(d_edge <= SELF_SEED_EDGE_M, SELF_SEED_EDGE_KEEP, SELF_SEED_FIELD_KEEP)]''',
    '''                # ADR 0334 r2 (critic build #8 P1#7): on the strip farms of a rural tile the open field keeps no
                # scattered lone sapling at all - its trees are the clumps and baulk runs of field_plants
                d_edge = shapely.distance(shapely.points(P), poly.boundary)
                inside = 0.0 if field_plants_on and poly.area >= FIELD_PLANT_MIN_M2 else SELF_SEED_FIELD_KEEP
                P = P[u < np.where(d_edge <= SELF_SEED_EDGE_M, SELF_SEED_EDGE_KEEP, inside)]''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
