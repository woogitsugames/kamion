"""ADR 0110 step 2 (one-off source patch, kept as a record): grass verge behind kerbs without a sidewalk."""
p = 'tools/worldgen/roads/network.py'
s = open(p, encoding='utf-8').read()
old = '''            c.side[side] = {"kind": kind, "walk": walk_d, "median": med_d, "raw": {"h": h, "w": w, "depth": depth},
                            "mat": mat}
'''
new = '''            # ADR 0110 (REVIEW s10-0100 P1-1): grass behind a kerb that has no sidewalk, at the kerb crown. The kerb
            # used to end in its 0.5 m buried flange and the 1 m terrain grid lay 0.03-0.4 m lower behind it: from the
            # other carriageway the flange read as a concrete wall and every median as a trough. Width: VERGE_W, in a
            # median up to MEDIAN_VERGE_MAX, never past the middle of the gap to a parallel carriageway.
            gapm = _side_gap(c, sgn, idx, all_tree, all_chains, trims)
            verge = np.where(med_d, S.MEDIAN_VERGE_MAX, S.VERGE_W)
            verge = np.minimum(verge, np.maximum((gapm - 2 * S.KERB_TOP_W) / 2, 0.0))
            verge[(kind != URBAN) | (w > 0.05) | (mat != 0) | (h < 0.05) | c.bridge] = 0.0
            c.side[side] = {"kind": kind, "walk": walk_d, "median": med_d, "raw": {"h": h, "w": w, "depth": depth},
                            "mat": mat, "verge": verge}
'''
assert old in s
s = s.replace(old, new)
old = '''def structure_sides(c: Chain, mask: np.ndarray):'''
new = '''def _side_gap(c, sgn, idx, tree, chains, trims=False, reach=2 * 3.0 + 1.0):
    """Clear distance [m] per dense station from this edge (gutter) to the gutter of the nearest roughly parallel
    carriageway lying on this side within `reach` (inf where there is none); checked at `idx`, the minimum of the
    neighbouring checks is held in between (ADR 0110, as _tight_side without the profile-extent test)."""
    n = len(c.line.s)
    gapv = np.full(len(idx), np.inf)
    nodes = {c.node_a: 0.0, c.node_b: c.length}
    skip = {c.node_a: (c.t_a + 1.0) if trims else S.ADJ_NODE_SKIP_M, c.node_b: (c.t_b + 1.0) if trims else S.ADJ_NODE_SKIP_M}
    for j, i in enumerate(idx):
        p, nrm, t = c.line.p[i], c.line.n[i] * sgn, c.line.t[i]
        e = p + nrm * c.hw[i]
        for k in tree.query(Point(*(e + nrm * reach * 0.5)).buffer(reach * 0.5 + 6.0)):
            oc = chains[int(k)]
            if oc is c or oc.meta.get("absorbed"):
                continue
            if any(abs(c.line.s[i] - nodes[nd]) < skip[nd] for nd in {oc.node_a, oc.node_b} & set(nodes)):
                continue
            s_o, lat_o = oc.line.project(e)
            if s_o <= 0.0 or s_o >= oc.length:
                continue
            io = oc.idx(s_o)
            if abs(float(np.dot(oc.line.t[io], t))) < 0.7:
                continue
            if float(np.dot(oc.line.point(s_o) - p, nrm)) <= 0.0:       # other road on the far side
                continue
            gapv[j] = min(gapv[j], max(float(abs(lat_o) - oc.hw_at(s_o)), 0.0))
    g = np.array([gapv[max(0, j - 1):j + 2].min() for j in range(len(idx))])
    out = np.full(n, np.inf)
    ia = np.asarray(idx)
    for a, b, ga, gb in zip(ia[:-1], ia[1:], g[:-1], g[1:]):
        out[a:b + 1] = np.minimum(out[a:b + 1], min(ga, gb))
    return out


def structure_sides(c: Chain, mask: np.ndarray):'''
assert old in s
s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='\n').write(s)

p = 'tools/worldgen/roads/standards.py'
s = open(p, encoding='utf-8').read()
old = '''VERGE_W = 1.00                      # WORKING_VALUE: grass strip behind the kerb when no sidewalk
'''
new = old + '''MEDIAN_VERGE_MAX = 3.00             # WORKING_VALUE (ADR 0110): grass strip behind a median kerb (two meet in the middle)
'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)

p = 'tools/worldgen/roads/meshing.py'
s = open(p, encoding='utf-8').read()
old = '''    kl = [(p[0], p[4] == MAT_FLUSH_ROAD) for p in params]
'''
new = '''    if not coarse and c.side[side].get("verge") is not None:
        vg = c.side[side]["verge"]
        wl = c.meta.get("walled")
        vw = np.array([float(c.interp(vg, s)) if (p[0] == URBAN and p[2] < 0.05 and p[4] == 0 and p[1] > 0.05) else 0.0
                       for s, p in zip(st, params)])
        if br is not None:
            vw[br] = 0.0
        if wl is not None:
            vw[c.interp(wl.astype(float), st) > 0.01] = 0.0
        _emit_verge(buf, G, N * sgn, zg, np.array([p[1] for p in params]), vw, kap, hw, side == "R",
                    f"{c.id}:{side}:vg")
    kl = [(p[0], p[4] == MAT_FLUSH_ROAD) for p in params]
'''
assert old in s
s = s.replace(old, new)
old = '''# ADR 0100 (REVIEW s10-0095 P1-8): a concrete strip wider than a kerb top'''
new = '''def _emit_verge(buf, G, OUT, zg, H, VW, kap_toward, hw, flip, src):
    """ADR 0110: grass strip behind a kerb without a sidewalk, from the back of the kerb top at the kerb crown
    (rising SIDEWALK_CROSSFALL outward), VW m wide per station, ending in a battered grass skirt
    (1 : EMBANKMENT_SLOPE, FLANGE_DEPTH deep) instead of the kerb's vertical concrete flange. Visual only (the
    collision ground behind a kerb stays the terrain); the top is footprint (terrain conforms under it, "soft")."""
    n = len(G)
    VW = np.asarray(VW, float).copy()
    if n < 2 or VW.max() < 0.05:
        return
    VW[VW < 0.05] = 0.0
    tw = S.KERB_TOP_W
    scale = np.ones(n)
    inside = kap_toward > 1e-6
    if inside.any():
        R = 1.0 / np.maximum(kap_toward[inside], 1e-6)
        allow = np.maximum(0.3, 0.9 * R - (hw[inside] if np.ndim(hw) else hw))
        scale[inside] = np.minimum(1.0, allow / np.maximum(tw + VW[inside] + S.FLANGE_DEPTH * S.EMBANKMENT_SLOPE, 1e-6))
    on = VW > 0.0
    u0 = tw * scale
    u1 = (tw + VW) * scale
    u2 = u1 + np.where(on, S.FLANGE_DEPTH * S.EMBANKMENT_SLOPE, 0.0) * scale
    z0 = zg + H
    z1 = z0 + S.SIDEWALK_CROSSFALL * VW
    z2 = z1 - np.where(on, S.FLANGE_DEPTH, 0.0)
    P0 = np.column_stack([G + OUT * u0[:, None], z0])
    P1 = np.column_stack([G + OUT * u1[:, None], z1])
    P2 = np.column_stack([G + OUT * u2[:, None], z2])
    along = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(G, axis=0).T))])
    T = grid_tris(n, 2, flip=flip)
    for A, B, ua, ub, fp in ((P0, P1, u0, u1, True), (P1, P2, u1, u2, False)):
        V = np.concatenate([A[:, None, :], B[:, None, :]], axis=1).reshape(-1, 3)
        UV1 = np.column_stack([np.repeat(along, 2), np.column_stack([ua, ub]).ravel()])
        buf.add("road", "verge_grass", V, V[:, :2].copy(), T, footprint=fp, src=src, UV1=UV1)


# ADR 0100 (REVIEW s10-0095 P1-8): a concrete strip wider than a kerb top'''
assert old in s
s = s.replace(old, new, 1)
old = '''        params = [(URBAN, p[1], (p[2] if p[0] == URBAN else 0.0), p[3], p[4] if p[0] == URBAN else 0) for p in params]'''
new = '''        # ADR 0110: `h` of a rural station is its DITCH depth (0.2-0.6 m), not a kerb height: a corner between a kerbed
        # and a rural arm rose to a 0.6 m concrete wall (j:n1847317049:corner0, kerb_rise.py)
        params = [(URBAN, p[1] if p[0] == URBAN else S.KERB_HEIGHT, (p[2] if p[0] == URBAN else 0.0), p[3],
                   p[4] if p[0] == URBAN else 0) for p in params]'''
assert old in s
s = s.replace(old, new)
old = '''        # another carriageway (not an arm of this junction) right beside the corner: the strip is flush asphalt up
        # to it.'''
new = '''        va = A.chain.side[sideA].get("verge")
        vb = B.chain.side[sideB].get("verge")
        cv = None
        if va is not None and vb is not None and not coarse:
            va_ = float(A.chain.interp(va, float(A.s(j.trims[i]))))
            vb_ = float(B.chain.interp(vb, float(B.s(j.trims[i1]))))
            cv = va_ + (vb_ - va_) * f
        # another carriageway (not an arm of this junction) right beside the corner: the strip is flush asphalt up
        # to it.'''
assert old in s
s = s.replace(old, new)
old = '''        else:
            _emit_strip(buf, G, OUT, Z, params, kap, hwz, True, None, coarse, j.id + f":corner{i}")
'''
new = '''        else:
            _emit_strip(buf, G, OUT, Z, params, kap, hwz, True, None, coarse, j.id + f":corner{i}")
        if cv is not None and not _patch_on_bridge(j):
            # ADR 0110: the grass behind the kerb runs round the corner / median nose too
            vw = np.array([v if (q[0] == URBAN and q[2] < 0.05 and q[4] == 0 and q[1] > 0.05) else 0.0
                           for v, q in zip(cv, params)])
            _emit_verge(buf, G, OUT, Z, np.array([q[1] for q in params]), vw, kap, hwz, True, j.id + f":corner{i}:vg")
'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print("ok")
