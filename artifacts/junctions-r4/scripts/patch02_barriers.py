"""ADR 0110 step 3 (one-off source patch, kept as a record): bridge barrier-railing, barriers beside structures,
one continuous run per edge with turned-down terminals, hero viaduct keeps its barriers / loses the picket railing."""
import re

p = 'tools/worldgen/streetscape/furniture.py'
s = open(p, encoding='utf-8').read()
a = s.index('def guardrail(lin, P, Z, key):')
b = s.index('    report["guardrails_m"] = {k: round(v) for k, v in m.items()}')
new = r'''def guardrail(lin, P, Z, key, tall=None, term=(False, False)):
    """Steel W-beam on posts (top GUARDRAIL_H), Z = ground/surface height along P (points ~1 m apart).

    ADR 0110: `tall` (bool per point) = bridge barrier-railing ("barieroporecz"): posts to BRIDGE_BARRIER_H with a
    flat mid rail and a handrail above the beam, as on the decks of the Andersa viaducts (Mapillary 454716650857984,
    2948595898752384, 500263111404933: horizontal rails, no pickets). `term` = (start, end): the beam is turned down
    to the ground over GUARDRAIL_TERMINAL_M at that end (a free end on the ground; REVIEW s10-0100 P2-7)."""
    n = len(P)
    tall = np.zeros(n, bool) if tall is None else np.asarray(tall, bool)
    top = np.full(n, S.GUARDRAIL_H)
    tl = int(S.GUARDRAIL_TERMINAL_M)
    lo, hi = 0, n
    if n > 2 * tl + 4:
        if term[0] and not tall[:tl + 1].any():
            top[:tl + 1] = np.linspace(0.33, S.GUARDRAIL_H, tl + 1)
            lo = tl
        if term[1] and not tall[-tl - 1:].any():
            top[-tl - 1:] = np.linspace(S.GUARDRAIL_H, 0.33, tl + 1)
            hi = n - tl
    # posts: one family per run of low / tall points (shared boundary point belongs to the tall run)
    k = lo
    while k < hi:
        kk = k
        while kk + 1 < hi and tall[kk + 1] == tall[k]:
            kk += 1
        if kk > k:
            if tall[k]:
                lin.posts("barrier_post", P[k:kk + 1], S.GUARDRAIL_POST_SPACING, 0.1, 0.06, S.BRIDGE_BARRIER_H,
                          zb=Z[k:kk + 1], src=key)
                zt = Z[k:kk + 1]
                lin.ribbon("barrier_steel", P[k:kk + 1], zt + S.BRIDGE_BARRIER_MID - 0.03, zt + S.BRIDGE_BARRIER_MID + 0.03,
                           0.03, key)
                lin.slab("barrier_steel", P[k:kk + 1], zt + S.BRIDGE_BARRIER_H - 0.06, zt + S.BRIDGE_BARRIER_H, 0.06, key)
            else:
                lin.posts("barrier_post", P[k:kk + 1], S.GUARDRAIL_POST_SPACING, 0.1, 0.05, S.GUARDRAIL_H - 0.05,
                          zb=Z[k:kk + 1], src=key)
        k = kk + 1
    d = np.gradient(P, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    # W profile (two bulges toward the road side, +nrm): 5 points of the 0.31 m high beam
    prof = [(0.0, -0.31), (0.05, -0.24), (0.0, -0.155), (0.05, -0.07), (0.0, 0.0)]
    rows = []
    for o, dz in prof:
        rows.append(np.column_stack([P + nrm * (0.08 + o), Z + top + dz]))
    V = np.concatenate(rows)
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    UV = np.column_stack([np.tile(s, len(rows)), np.repeat(np.arange(len(rows)) * 0.08, n)])
    T = []
    for r in range(len(rows) - 1):
        a, b = r * n, (r + 1) * n
        T += [(a + k, a + k + 1, b + k + 1) for k in range(n - 1)] + [(a + k, b + k + 1, b + k) for k in range(n - 1)]
    T = np.array(T)
    lin.buf.add("furniture", "barrier_steel", V, UV, T, src=key)
    lin.buf.add("furniture", "barrier_steel", V, UV, T[:, [0, 2, 1]], src=key)
    lin.buf.add("collision", "collision_steel", V, UV, np.concatenate([T, T[:, [0, 2, 1]]]), src=key)


GUARDRAIL_DEDUP_M = 1.0     # ADR 0100 (REVIEW s10-0095 P1-10): a run within this of an already built rail is not built twice
GUARDRAIL_DEDUP_GROUND_M = 2.5   # ADR 0110 (REVIEW s10-0100 P1-6): ground runs - one rail per separator also when the
#                                  two edges that want it are 1-2.5 m apart (decks keep 1 m: two decks, two rails)
GUARDRAIL_MIN_RUN = 8       # points (1 m apart) of a run left after the dedup; shorter leftovers are dropped


def _dedup_guardrail(lin, P, Z, key, built, m, tall=None, term=(True, True)):
    """Build the parts of run P that are not within the dedup distance of a rail built before (two chains / a chain
    and an authored rail on the same separator crossed and overlapped at E -782 and on the viaduct approaches)."""
    from shapely.geometry import LineString, Point
    keep = np.ones(len(P), bool)
    tall = np.zeros(len(P), bool) if tall is None else np.asarray(tall, bool)
    if built:
        near = shapely.union_all([b.buffer(GUARDRAIL_DEDUP_M) for b in built])
        far = shapely.union_all([b.buffer(GUARDRAIL_DEDUP_GROUND_M) for b in built])
        shapely.prepare(near)
        shapely.prepare(far)
        keep = ~np.where(tall, shapely.contains_xy(near, P[:, 0], P[:, 1]), shapely.contains_xy(far, P[:, 0], P[:, 1]))
    k = 0
    while k < len(P):
        if not keep[k]:
            k += 1
            continue
        kk = k
        while kk + 1 < len(P) and keep[kk + 1]:
            kk += 1
        if kk - k + 1 >= GUARDRAIL_MIN_RUN:
            # a cut made by the dedup is not a free end (the other rail carries on there)
            guardrail(lin, P[k:kk + 1], Z[k:kk + 1], key, tall[k:kk + 1],
                      (term[0] and k == 0, term[1] and kk == len(P) - 1))
            built.append(LineString(P[k:kk + 1]))
        else:
            m["dedup_dropped_pts"] = m.get("dedup_dropped_pts", 0) + (kk - k + 1)
        k = kk + 1
    m["dedup_skipped_pts"] = m.get("dedup_skipped_pts", 0) + int((~keep).sum())


STRUCT_GUARD_GAP_M = 8.0     # WORKING_VALUE (ADR 0110): a ground carriageway edge this close to a viaduct / walled ramp
STRUCT_GUARD_MIN_H = 1.0     # ... standing at least this high above it gets a barrier on that side


def _structures(net):
    """[(chain id, deck polygon, KD-tree of deck axis points, their heights)] of bridges and walled ramps."""
    from scipy.spatial import cKDTree
    from shapely.geometry import LineString
    out = []
    for c in net.chains:
        if c.meta.get("absorbed"):
            continue
        msk = np.asarray(c.bridge, bool).copy()
        wl = c.meta.get("walled")
        if wl is not None:
            msk |= np.asarray(wl, bool)
        idx = np.where(msk)[0]
        if len(idx) < 3:
            continue
        for run in np.split(idx, np.where(np.diff(idx) > 1)[0] + 1):
            if len(run) < 3:
                continue
            pts = c.line.p[run]
            half = float(np.max(c.hw[run])) + S.KERB_TOP_W + S.BRIDGE_CAP_W
            out.append((c.id, LineString(pts).buffer(half, cap_style="flat"), cKDTree(pts),
                        np.asarray(c.crossfall_z(c.line.s[run], 0.0), float)))
    return out


def _beside_structure(c, ss, sgn, hw, zg, structs):
    """Stations of chain c whose edge on side sgn runs beside (not under) a viaduct / walled ramp of another chain."""
    E = c.line.offset_point(ss, sgn * (hw + 0.75))
    Eo = c.line.offset_point(ss, sgn * (hw + 4.75))
    res = np.zeros(len(ss), bool)
    lo, hi = E.min(0) - 15.0, E.max(0) + 15.0
    for cid, poly, tree, z in structs:
        if cid == c.id:
            continue
        b = poly.bounds
        if b[0] > hi[0] or b[2] < lo[0] or b[1] > hi[1] or b[3] < lo[1]:
            continue
        d0 = shapely.distance(poly, shapely.points(E))
        d1 = shapely.distance(poly, shapely.points(Eo))
        cand = (d0 > 0.2) & (d0 < STRUCT_GUARD_GAP_M) & (d1 < d0 - 1.0)
        if not cand.any():
            continue
        _, k = tree.query(E[cand])
        ok = z[k] - zg[cand] > STRUCT_GUARD_MIN_H
        res[np.where(cand)[0][ok]] = True
    return res


def guardrails(lin, net, zground, report):
    from scipy import ndimage
    m = {"bridge": 0.0, "median": 0.0, "embankment": 0.0, "structure": 0.0}
    names = ["", "bridge", "median", "embankment", "structure"]
    built = []
    drops, runs = [], []
    structs = _structures(net)
    for c in net.chains:
        if c.meta.get("absorbed"):
            continue
        s0, s1 = c.t_a, c.length - c.t_b
        if s1 - s0 < 10:
            continue
        ss = np.arange(s0, s1, 1.0)
        hw = c.hw_at(ss)
        br = c.bridge[c.idx(ss)]
        for side, sgn in (("L", 1.0), ("R", -1.0)):
            prm = [side_params(c, side, s) for s in ss]
            kinds = np.array([p[0] for p in prm])
            kh = np.array([p[1] for p in prm])
            kw = np.array([p[2] for p in prm])
            kmat = np.array([p[4] for p in prm])
            ext = np.array([side_extent(*p) for p in prm])
            zg = c.crossfall_z(ss, sgn * hw)
            want = np.zeros(len(ss), int)            # 1 bridge, 2 median, 3 embankment, 4 beside a structure
            off = np.zeros(len(ss))
            zb = zg.copy()
            # bridges: barrier-railing on the cap, BRIDGE_BARRIER_EDGE_M in from its outer edge (ADR 0110: the
            # orthophoto of the Biezenstwa decks has it 0.2-0.4 m from the deck edge, 0.8-1.0 m behind the kerb)
            want[br] = 1
            off[br] = hw[br] + S.KERB_TOP_W + S.BRIDGE_CAP_W - S.BRIDGE_BARRIER_EDGE_M
            zb[br] = zg[br] + S.BRIDGE_KERB_H
            med = (kinds == MEDIAN_RURAL) & ~br
            want[med] = 2
            off[med] = hw[med] + S.PAVED_SHOULDER_MEDIAN + S.GUARDRAIL_OFFSET
            zb[med] = zg[med] - 0.02
            rur = (kinds == RURAL) & ~br
            drop = np.full(len(ss), -1e9)
            if rur.any():
                # embankment height = road edge minus the ground at the toe of the fill slope: berm 1 m +
                # slope 1:1.5 of a 2 m fill + 1 m = profile end + 5 m (the old probe at +2 m only ever saw
                # the berm, so the rule never fired); take the lowest of three probes (5, 7, 9 m)
                for extra in (5.0, 7.0, 9.0):          # zground = natural ground (NMT), not the conformed terrain
                    P_out = c.line.offset_point(ss, sgn * (hw + ext + extra))
                    drop = np.maximum(drop, zg - zground(P_out[:, 0], P_out[:, 1]))
                drops.append(float(drop[rur].max()))
                emb = rur & (drop > S.GUARDRAIL_EMBANKMENT_H)
                # extend 12 m each way (approach), close small gaps
                emb = ndimage.binary_dilation(emb, iterations=12) & rur
                want[emb] = 3
                off[emb] = hw[emb] + S.PAVED_SHOULDER + S.GUARDRAIL_OFFSET
                zb[emb] = zg[emb] - S.CROSSFALL * S.PAVED_SHOULDER
            # ADR 0110 (gate-3 side-by-side #4b): W-beam along a ground carriageway that runs beside a viaduct or a
            # walled ramp, on the side facing it (Mapillary 500263111404933, 1259231227807789, 751431972202262: the
            # links at Rondo Biezenstwa). Rural edge: behind the paved shoulder; kerbed edge without a sidewalk:
            # GUARDRAIL_OFFSET behind the kerb. WORKING rule.
            if structs:
                kerbed = (kinds == URBAN) & (kw < 0.05) & (kh > 0.05) & (kmat == 0)
                bs = _beside_structure(c, ss, sgn, hw, zg, structs) & (want == 0) & ~br & (rur | kerbed)
                bs = ndimage.binary_closing(bs, iterations=6) & (want == 0) & ~br & (rur | kerbed)
                want[bs] = 4
                off[bs] = np.where(rur[bs], hw[bs] + S.PAVED_SHOULDER + S.GUARDRAIL_OFFSET,
                                   hw[bs] + S.KERB_TOP_W + S.GUARDRAIL_OFFSET)
                zb[bs] = np.where(rur[bs], zg[bs] - S.CROSSFALL * S.PAVED_SHOULDER, zg[bs] + kh[bs])
            # runs: ONE rail per contiguous stretch that wants a barrier, whatever the rule (ADR 0110: the bridge
            # rail, the approach embankment rail and the median rail were separate runs at different offsets and
            # crossed / doubled where they met, REVIEW s10-0100 P1-6); the offset and the foot height blend over 9 m
            k = 0
            while k < len(ss):
                if want[k] == 0:
                    k += 1
                    continue
                kk = k
                while kk + 1 < len(ss) and want[kk + 1] != 0:
                    kk += 1
                if kk - k >= 8:
                    sl = slice(k, kk + 1)
                    o_, z_ = off[sl].copy(), zb[sl].copy()
                    if len(set(want[sl].tolist())) > 1:
                        o_ = ndimage.uniform_filter1d(o_, 9, mode="nearest")
                        z_ = ndimage.uniform_filter1d(z_, 9, mode="nearest")
                    P = c.line.offset_point(ss[sl], sgn * o_)
                    tall = want[sl] == 1
                    if sgn > 0:                          # beam faces the road: road is on the right of travel
                        P, z_, tall = P[::-1], z_[::-1], tall[::-1]
                    kind = names[int(np.bincount(want[sl]).argmax())]
                    _dedup_guardrail(lin, P, z_, f"{c.id}:{side}:{kind}", built, m, tall)
                    w3 = want[sl] == 3
                    if w3.any():
                        runs.append({"chain": c.id, "side": side, "s": [round(float(ss[k]), 1), round(float(ss[kk]), 1)],
                                     "max_drop_m": round(float(drop[sl][w3].max()), 2),
                                     "at": [round(float(v), 1) for v in c.line.offset_point(ss[(k + kk) // 2], 0.0)]})
                    for q in (1, 2, 3, 4):
                        m[names[q]] += float((want[sl] == q).sum())
                k = kk + 1
    # ADR 0100: authored guardrails on kerbed separators traced on the orthophoto (`kind: guardrail`, polyline_en in
    # region-local E/N, drawn with the road on the RIGHT of the drawing direction = the face of the W-beam)
    m["authored"] = 0.0
    for o in getattr(net, "authored", None) or []:
        if o.get("kind") != "guardrail":
            continue
        Q = np.asarray(o.get("polyline_en") or [], float)
        if Q.ndim != 2 or len(Q) < 2:
            net.overrides_stale.append(o["id"])
            continue
        sq = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(Q, axis=0).T))])
        u = np.linspace(0.0, sq[-1], max(2, int(np.ceil(sq[-1])) + 1))
        P = np.column_stack([np.interp(u, sq, Q[:, 0]), np.interp(u, sq, Q[:, 1])])
        Z = lin.z(P)
        if not np.isfinite(Z).all():
            net.overrides_stale.append(o["id"])
            continue
        _dedup_guardrail(lin, P, Z, f"authored:{o['id']}", built, m)
        net.overrides_applied.append({"id": o["id"], "targets": [f"guardrail@{P[0][0]:.0f},{P[0][1]:.0f}"]})
        m["authored"] += float(sq[-1])
'''
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8', newline='\n').write(s)

p = 'tools/worldgen/roads/standards.py'
s = open(p, encoding='utf-8').read()
old = '''GUARDRAIL_OFFSET = 0.60     # behind the kerb face / edge WORKING_VALUE
'''
new = old + '''GUARDRAIL_TERMINAL_M = 4    # WORKING_VALUE (ADR 0110): free ground end of a W-beam turned down to the ground over this length
BRIDGE_BARRIER_H = 1.10     # WORKING_VALUE (ADR 0110): handrail of the bridge barrier-railing (posts), Mapillary 454716650857984
BRIDGE_BARRIER_MID = 0.92   # WORKING_VALUE: flat rail between the W-beam and the handrail (same frame)
BRIDGE_BARRIER_EDGE_M = 0.40  # WORKING_VALUE: barrier-railing axis in from the outer edge of the cap (orthophoto 0.2-0.4 m)
'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)

p = 'tools/worldgen/roads/meshing.py'
s = open(p, encoding='utf-8').read()
old = '''        for side, sgn in (() if hero else (("L", 1.0), ("R", -1.0))):
            top = outer[side][1].copy()
            top[:, :2] -= nn * sgn * 0.15'''
new = '''        # ADR 0110: no balustrade where a noise screen stands on the same edge (the screen is the edge protection; with
        # the barrier-railing that made three rail systems side by side, REVIEW s10-0100 P1-6 p0_lamp_w1101181473_eye)
        for side, sgn in (() if (hero or style["noise_screen"]) else (("L", 1.0), ("R", -1.0))):
            top = outer[side][1].copy()
            top[:, :2] -= nn * sgn * 0.15'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)

p = 'tools/worldgen/streetscape/hero_bridge.py'
s = open(p, encoding='utf-8').read()
old = '''    "rail_h_m": S.BRIDGE_PARAPET_H,'''
new = '''    # ADR 0110: 0 = no picket railing in the asset. The decks carry the generated steel barrier-railing
    # (streetscape.furniture.guardrails, horizontal rails as on Mapillary 454716650857984 / 500263111404933).
    "rail_h_m": 0.0,'''
assert old in s
s = s.replace(old, new)
old = '''            w.buf.parts = [p for p in w.buf.parts if not (p.src == c.id or p.src.startswith(c.id + ":"))]'''
new = '''            # ADR 0110: the barriers of the chain (streetscape.furniture.guardrails, src "<chain>:<side>:<rule>") stay:
            # they were dropped with the ribbons, so the hero decks had no road barrier at all (gate-3 sbs #4a)
            rails = ("bridge", "median", "embankment", "structure")
            w.buf.parts = [p for p in w.buf.parts if not (p.src == c.id or p.src.startswith(c.id + ":"))
                           or (p.layer in ("furniture", "collision") and p.src.rsplit(":", 1)[-1] in rails)]'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)

p = 'tools/blender/world/landmarks/make_viaduct.py'
s = open(p, encoding='utf-8').read()
old = '''            # ---- railing on the cap edge
            xr = sgn * (a.hb - PRM["rail_inset_m"])
            H = PRM["rail_h_m"]
'''
new = '''            # ---- railing on the cap edge (ADR 0110: rail_h_m 0 = none, the world generator builds the barrier-railing)
            if PRM["rail_h_m"] < 0.05:
                continue
            xr = sgn * (a.hb - PRM["rail_inset_m"])
            H = PRM["rail_h_m"]
'''
assert old in s
s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print("ok")
