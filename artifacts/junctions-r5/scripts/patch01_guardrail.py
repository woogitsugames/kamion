"""ADR 0117 patch 01: W-beam with the real folded profile (hard arrises), C posts + spacer + foot plate, deck barrier
with an upper box beam (applied once; kept as the record of the change)."""
import pathlib
p = pathlib.Path("tools/worldgen/streetscape/furniture.py")
s = p.read_text(encoding="utf-8")
a = s.index("def guardrail(lin, P, Z, key, tall=None, term=(False, False)):")
b = s.index("# ADR 0110: posts share the material of the beam")
new = r'''# ADR 0117 (REVIEW s10-0110 P1-1): the W-beam as the folded sheet it is - 310 mm high, 83 mm deep, two flat crests and
# a valley (the "A" guide rail of the SP-05 family; depth/height from the review table, fold positions WORKING_VALUE).
# (offset towards the road from the back plane of the beam, height below its top edge). Every facet has its own
# vertices: the exporter smooths normals inside a part, so shared rows shaded the beam as one tube.
W_PROFILE = ((0.020, 0.0), (0.083, -0.040), (0.083, -0.105), (0.0, -0.155), (0.083, -0.205), (0.083, -0.270),
             (0.020, -0.310))
W_BACK = 0.05               # m: back plane (valley) of the beam in front of the post line P -> crest face at 0.133
#                             (0.13 before: the collision face and the swept-path clearance stay where they were)
POST_FRONT = -0.05          # m: road-side flange of the post behind P; the spacer fills POST_FRONT .. W_BACK (0.10 m)
POST_C = (0.10, 0.055)      # ground post: C / sigma 100 x 55 (web across the road, flanges along it), WORKING_VALUE
POST_C_DECK = (0.12, 0.064)  # deck post (heavier section on a foot plate, Mapillary 454716650857984), WORKING_VALUE
# UV0 of the `barrier_galv` set (4.0 x 0.5 m tile, u along the beam, v = unrolled metres across the profile from the
# bottom edge): posts / spacers / plates sample the plain sheet between the splices
POST_U0 = 1.3


def _w_unrolled():
    v = [0.0]
    pr = W_PROFILE[::-1]
    for (o0, z0), (o1, z1) in zip(pr[:-1], pr[1:]):
        v.append(v[-1] + math.hypot(o1 - o0, z1 - z0))
    return v[::-1]            # per W_PROFILE point, top edge first


def _quads(lin, layer, mat, quads, src, both=True):
    """Flat-shaded quad soup: quads = [(4 points CCW seen from the front, 4 uv)]."""
    V, UV, T = [], [], []
    for pts, uv in quads:
        b = len(V)
        V += [np.asarray(q, float) for q in pts]
        UV += list(uv)
        T += [(b, b + 1, b + 2), (b, b + 2, b + 3)]
        if both:
            b = len(V)
            V += [np.asarray(q, float) for q in pts]
            UV += list(uv)
            T += [(b, b + 2, b + 1), (b, b + 3, b + 2)]
    if V:
        lin.buf.add(layer, mat, np.array(V), np.array(UV, float), np.array(T), src=src)


def _rail_posts(lin, Q, Zq, Tq, top, deck, key):
    """C posts at Q (n, 2) with the open side downstream, a spacer block between post and beam, and on a deck a foot
    plate. `top` = top of the W-beam above Zq per post; deck posts carry on to BRIDGE_BARRIER_H (upper beam)."""
    quads = []
    dep, fl = POST_C_DECK if deck else POST_C
    f, bk = POST_FRONT, POST_FRONT - dep

    def uv(u0, u1, h):
        h = min(h, 0.44)
        return ((POST_U0 + u0, 0.02), (POST_U0 + u1, 0.02), (POST_U0 + u1, 0.02 + h), (POST_U0 + u0, 0.02 + h))

    def frame(q, t):
        nn = np.array([-t[1], t[0]])                  # towards the road (beam side)
        return lambda o, a, zz: np.append(q + nn * o + t * a, zz)

    for q, z, t, tp in zip(Q, Zq, Tq, top):
        P3 = frame(q, t)
        z0 = z if deck else z - 0.3                    # ground posts are driven in
        z1 = z + (S.BRIDGE_BARRIER_H if deck else tp - 0.03)
        h = z1 - z0
        # road-side flange, web, back flange (thin sheet, drawn from both sides)
        quads.append(([P3(f, fl / 2, z0), P3(f, -fl / 2, z0), P3(f, -fl / 2, z1), P3(f, fl / 2, z1)], uv(0.0, fl, h)))
        quads.append(([P3(f, -fl / 2, z0), P3(bk, -fl / 2, z0), P3(bk, -fl / 2, z1), P3(f, -fl / 2, z1)],
                      uv(0.1, 0.1 + dep, h)))
        quads.append(([P3(bk, -fl / 2, z0), P3(bk, fl / 2, z0), P3(bk, fl / 2, z1), P3(bk, -fl / 2, z1)],
                      uv(0.3, 0.3 + fl, h)))
    _quads(lin, "furniture", POST_MAT, quads, key, both=True)
    solid = []
    u = POST_U0 + 0.5
    for q, z, t, tp in zip(Q, Zq, Tq, top):
        P3 = frame(q, t)
        # spacer ("przekladka"): block between the post flange and the valley of the beam; top + the two sides
        a_, zs0, zs1 = 0.045, z + tp - 0.235, z + tp - 0.075
        solid.append(([P3(POST_FRONT, a_, zs1), P3(W_BACK, a_, zs1), P3(W_BACK, -a_, zs1), P3(POST_FRONT, -a_, zs1)],
                      ((u, 0.30), (u + 0.1, 0.30), (u + 0.1, 0.39), (u, 0.39))))
        for sg in (1.0, -1.0):
            pts = [P3(POST_FRONT, sg * a_, zs0), P3(W_BACK, sg * a_, zs0), P3(W_BACK, sg * a_, zs1),
                   P3(POST_FRONT, sg * a_, zs1)]
            solid.append((pts if sg > 0 else pts[::-1], ((u, 0.20), (u + 0.1, 0.20), (u + 0.1, 0.36), (u, 0.36))))
        if deck:
            # foot plate bolted to the cap: top and the road-side edge
            f0, f1, a_, th = POST_FRONT + 0.05, POST_FRONT - dep - 0.05, 0.11, 0.02
            solid.append(([P3(f1, a_, z + th), P3(f0, a_, z + th), P3(f0, -a_, z + th), P3(f1, -a_, z + th)],
                          ((u + 0.2, 0.05), (u + 0.42, 0.05), (u + 0.42, 0.27), (u + 0.2, 0.27))))
            solid.append(([P3(f0, a_, z), P3(f0, -a_, z), P3(f0, -a_, z + th), P3(f0, a_, z + th)],
                          ((u + 0.2, 0.0), (u + 0.42, 0.0), (u + 0.42, 0.02), (u + 0.2, 0.02))))
    _quads(lin, "furniture", POST_MAT, solid, key, both=False)


def _stations(P, Z, top, spacing, lo, hi):
    """Post stations every ~`spacing` along P[lo:hi + 1] (both ends included): points, foot z, tangents, beam top."""
    Pp = P[lo:hi + 1]
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(Pp, axis=0).T))])
    L = float(s[-1])
    n = max(1, int(round(L / spacing)))
    u = np.linspace(0.0, L, n + 1)
    Q = np.column_stack([np.interp(u, s, Pp[:, 0]), np.interp(u, s, Pp[:, 1])])
    d = np.gradient(Pp, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    Tq = np.column_stack([np.interp(u, s, d[:, 0]), np.interp(u, s, d[:, 1])])
    Tq /= np.maximum(np.hypot(Tq[:, 0], Tq[:, 1]), 1e-9)[:, None]
    return Q, np.interp(u, s, Z[lo:hi + 1]), Tq, np.interp(u, s, top[lo:hi + 1])


def guardrail(lin, P, Z, key, tall=None, term=(False, False)):
    """Steel W-beam on posts (top GUARDRAIL_H), Z = ground/surface height along P (points ~1 m apart). P is the post
    line; the road is on its LEFT normal side (beam face W_BACK + 0.083 in front of it).

    ADR 0110: `tall` (bool per point) = deck barrier of the Andersa viaducts. `term` = (start, end): the beam is
    turned down to the ground over GUARDRAIL_TERMINAL_M at that end (a free end on the ground).
    ADR 0117: folded W profile with hard arrises (W_PROFILE), C posts with a spacer behind the beam (the beam hangs on
    the face of the post, not on its top), ground posts every GUARDRAIL_POST_SPACING_GROUND; deck runs: heavier posts
    on foot plates every GUARDRAIL_POST_SPACING with a box beam above the W-beam (Mapillary 454716650857984: low
    W-beam + upper beam on short posts; the handrail with horizontal bars at the deck edge is a separate railing -
    hero asset / roads.meshing.build_bridge_extras)."""
    n = len(P)
    tall = np.zeros(n, bool) if tall is None else np.asarray(tall, bool)
    first = len(lin.buf.parts)
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
    d = np.gradient(P, axis=0)
    d /= np.maximum(np.hypot(d[:, 0], d[:, 1]), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    s_all = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    # posts: one family per run of low / tall points (shared boundary point belongs to the tall run)
    k = lo
    while k < hi:
        kk = k
        while kk + 1 < hi and tall[kk + 1] == tall[k]:
            kk += 1
        if kk > k:
            deck = bool(tall[k])
            Q, Zq, Tq, tq = _stations(P, Z, top, S.GUARDRAIL_POST_SPACING if deck else S.GUARDRAIL_POST_SPACING_GROUND,
                                      k, kk)
            if not deck and k > lo and tall[k - 1]:
                Q, Zq, Tq, tq = Q[1:], Zq[1:], Tq[1:], tq[1:]          # the boundary post is the deck post
            if len(Q):
                _rail_posts(lin, Q, Zq, Tq, tq, deck, key)
            if deck:
                # upper box beam (100 x 80) on the road face of the posts; at an end where the W-beam carries on
                # along the ground it slopes down behind the W-beam over 2 m instead of stopping in the air
                zt = np.full(kk - k + 1, S.BRIDGE_BARRIER_H)
                if k > lo and kk - k >= 4:
                    zt[:3] = np.linspace(S.GUARDRAIL_H - 0.02, S.BRIDGE_BARRIER_H, 3)
                if kk + 1 < hi and kk - k >= 4:
                    zt[-3:] = np.linspace(S.BRIDGE_BARRIER_H, S.GUARDRAIL_H - 0.02, 3)
                kp = dp_keep(np.column_stack([P[k:kk + 1], Z[k:kk + 1] + zt]), 0.01)
                Pt, zz, nt, st = P[k:kk + 1][kp], (Z[k:kk + 1] + zt)[kp], nrm[k:kk + 1][kp], s_all[k:kk + 1][kp]
                box = ((POST_FRONT, 0.0), (POST_FRONT + 0.08, 0.0), (POST_FRONT + 0.08, -0.10), (POST_FRONT, -0.10))
                uvv = (0.40, 0.46, 0.34, 0.42)
                for (o0, z0), (o1, z1), v0 in zip(box, box[1:] + box[:1], uvv):
                    A = np.column_stack([Pt + nt * o0, zz + z0])
                    B = np.column_stack([Pt + nt * o1, zz + z1])
                    m_ = len(Pt)
                    V = np.concatenate([A, B])
                    UV = np.column_stack([np.tile(st, 2), np.repeat([v0, v0 + 0.06], m_)])
                    T = [(i, i + 1, m_ + i + 1) for i in range(m_ - 1)] + [(i, m_ + i + 1, m_ + i) for i in range(m_ - 1)]
                    lin.buf.add("furniture", "barrier_steel", V, UV, np.array(T), src=key)
        k = kk + 1
    # ADR 0110: the beam keeps only the points a 1 cm Douglas-Peucker needs (it was meshed every metre: 16 triangles
    # per metre also on straights; the posts above keep their spacing)
    kp = dp_keep(np.column_stack([P, Z + top]), 0.01)
    P, Z, top, nrm, s = P[kp], Z[kp], top[kp], nrm[kp], s_all[kp]
    n = len(P)
    vv = _w_unrolled()
    rows, uvr = [], []
    for (o0, z0), (o1, z1), v0, v1 in zip(W_PROFILE[:-1], W_PROFILE[1:], vv[:-1], vv[1:]):
        rows.append(np.column_stack([P + nrm * (W_BACK + o0), Z + top + z0]))
        rows.append(np.column_stack([P + nrm * (W_BACK + o1), Z + top + z1]))
        uvr += [v0, v1]
    V = np.concatenate(rows)
    UV = np.column_stack([np.tile(s, len(rows)), np.repeat(uvr, n)])
    T = []
    for r in range(0, len(rows), 2):
        a, b = r * n, (r + 1) * n
        T += [(a + k, a + k + 1, b + k + 1) for k in range(n - 1)] + [(a + k, b + k + 1, b + k) for k in range(n - 1)]
    T = np.array(T)
    lin.buf.add("furniture", "barrier_steel", V, UV, T, src=key)
    lin.buf.add("furniture", "barrier_steel", V, UV, T[:, [0, 2, 1]], src=key)
    if tall.any() or key.endswith(":structure"):
        # ADR 0110: a run on a deck, and a run beside a viaduct, belong to the bridge mesh of their chunk (drawn with
        # the deck; one barrier_steel primitive for both), not to the furniture mesh (fences, hedges: its bounds grew
        # by the viaduct and 8 more draws entered frames beside it)
        for prt in lin.buf.parts[first:]:
            if prt.layer == "furniture":
                prt.layer = "bridge"
    # collision: the road face of the beam only (top edge - crests - bottom edge), where it was before ADR 0117
    cr = [0, 1, 3, 7, 9, 11]
    Vc = np.concatenate([rows[i] for i in cr])
    Tc = []
    for r in range(len(cr) - 1):
        a, b = r * n, (r + 1) * n
        Tc += [(a + k, a + k + 1, b + k + 1) for k in range(n - 1)] + [(a + k, b + k + 1, b + k) for k in range(n - 1)]
    Tc = np.array(Tc)
    lin.buf.add("collision", "collision_steel", Vc, Vc[:, :2], np.concatenate([Tc, Tc[:, [0, 2, 1]]]), src=key)


'''
s = s[:a] + new + s[b:]
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
