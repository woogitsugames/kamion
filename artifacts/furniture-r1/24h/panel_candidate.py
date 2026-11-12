"""Candidate for ADR0120; kept outside production until baseline completes."""

def panel_fence(lin, line, col, key, flexible=False):
    """ADR0120: short stepped bays on grades, joints and a slight lateral mesh bow.

    Maximum endpoint rise 0.25 m, maximum bay 2.5 m, lateral bow 12–25 mm
    and board end clearance 8 mm are WORKING_VALUE, not surveyed dimensions.
    Road barriers and shared Lin helpers keep their existing behaviour.
    """
    P = [np.asarray(line.coords[0], float)]

    def subdivide(a, b, depth=0):
        q = np.array([a, (a + b) / 2, b])
        z = lin.z(q)
        if depth < 10 and (np.linalg.norm(b-a) > S.FENCE_PANEL_W + 1e-6
                           or (np.ptp(z) > 0.25 and np.linalg.norm(b-a) > 0.35)):
            mid = (a + b) / 2
            subdivide(a, mid, depth+1)
            subdivide(mid, b, depth+1)
        else:
            P.append(b)

    for a, b in zip(np.asarray(line.coords)[:-1], np.asarray(line.coords)[1:]):
        count = max(1, int(math.ceil(np.linalg.norm(b-a) / S.FENCE_PANEL_W)))
        for j in range(count):
            subdivide(a + (b-a)*j/count, a + (b-a)*(j+1)/count)
    P = np.asarray(P)
    Z = lin.z(P)
    bases = np.maximum(Z[:-1], Z[1:])
    post_base = np.maximum(np.r_[bases[0], bases], np.r_[bases, bases[-1]])
    for i, base in enumerate(bases):
        ends = P[i:i + 2]
        direction = ends[1] - ends[0]
        length = np.linalg.norm(direction)
        if length < 1e-6:
            continue
        direction /= length
        inset = min(0.008, length * 0.1)
        board = ends + np.array([direction * inset, -direction * inset])
        low = lin.z(board) - 0.2
        top = np.full(2, base + S.FENCE_PLINTH_H)
        lin.slab("concrete_plinth", board, low, top, 0.05, key)
        lateral = np.array([-direction[1], direction[0]])
        seed = _h(f"{key}:bay:{i}")
        bow = (0.012 + (seed % 14) * 0.001) * (1 if seed & 16 else -1)
        Q = np.array([ends[0], ends.mean(axis=0) + lateral * bow, ends[1]])
        bottom = np.full(3, base + S.FENCE_PLINTH_H)
        sag = 0.045 if flexible else 0.0
        upper = base + S.FENCE_H - np.array([0, sag, 0])
        lin.ribbon(f"{col}_mesh", Q, bottom, upper, 0, key, both=True, collision="collision_fence")
    lin.posts(col, P, None, 0.06, 0.04, S.FENCE_H + 0.05, zb=post_base, src=key, ground_feet=True)
