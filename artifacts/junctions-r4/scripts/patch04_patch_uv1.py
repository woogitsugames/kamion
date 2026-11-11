"""ADR 0110 step 4: junction plates carry the wheel-path / gutter weathering coordinates (UV1) of their through road."""
p = 'tools/worldgen/roads/meshing.py'
s = open(p, encoding='utf-8').read()
old = 'footprint=(layer == "road" and not coarse), src=j.id)'
assert s.count(old) == 3, s.count(old)
s = s.replace(old, 'footprint=(layer == "road" and not coarse), src=j.id,\n' + ' ' * 16 + 'UV1=None if coarse else _patch_uv1(net, j, V))')
old = '''def _patch_mat(net, j):'''
new = '''def _patch_uv1(net, j, V):
    """UV1 = (lane coordinate, distance to the carriageway edge) of a junction plate, in the frame of its through
    road: the widest arm and the arm opposite to it (ADR 0110, REVIEW s10-0100 P1-2). Plates had no UV1 (the exporter
    default -1 / 5 m = no wheel paths, no gutter dirt), so every plate in a weathered carriageway read as a cleaner,
    lighter rectangle across the lanes (p0_fork_putry_eye, eye_putry_n). Vertices outside the through road keep the
    default."""
    P = np.asarray(V, float)[:, :2]
    lane = np.full(len(P), -1.0)
    edge = np.full(len(P), 5.0)
    score = np.full(len(P), np.inf)
    if not j.arms:
        return np.column_stack([lane, edge])
    hws = [float(a.chain.hw_at(float(a.s(j.trims[i])))) for i, a in enumerate(j.arms)]
    i0 = int(np.argmax(hws))
    d0 = j.arms[i0].direction(float(j.trims[i0]))
    ref = [i0]
    best = None
    for i, a in enumerate(j.arms):
        if i == i0:
            continue
        dot = float(np.dot(a.direction(float(j.trims[i])), d0))
        if dot < -0.8 and (best is None or dot < best[0]):
            best = (dot, i)
    if best is not None:
        ref.append(best[1])
    for i in ref:
        a = j.arms[i]
        c = a.chain
        d = float(j.trims[i])
        s0 = float(a.s(d))
        sec = c.section(s0, net.sec_list)
        lo, hi = (0.0, d + 5.0) if a.end == "a" else (c.length - d - 5.0, c.length)
        idx = np.where((c.line.s >= lo - 1e-6) & (c.line.s <= hi + 1e-6))[0]
        if len(idx) < 2:
            continue
        pts = c.line.p[idx]
        A, B = pts[:-1], pts[1:]
        AB = B - A
        l2 = np.maximum((AB ** 2).sum(1), 1e-12)
        t = np.clip(((P[:, None, :] - A[None]) * AB[None]).sum(2) / l2[None], 0.0, 1.0)
        C = A[None] + AB[None] * t[..., None]
        D = np.hypot(P[:, None, 0] - C[..., 0], P[:, None, 1] - C[..., 1])
        k = D.argmin(1)
        dist = D[np.arange(len(P)), k]
        cross = AB[k, 0] * (P[:, 1] - A[k, 1]) - AB[k, 1] * (P[:, 0] - A[k, 0])
        lat = np.copysign(dist, cross)
        hw = hws[i]
        if getattr(sec, "lane_edges", None):
            lc = sec.lane_coord(lat, hw, int(c.dirn[c.idx(s0)]) or 1)
        elif sec.oneway or sec.roundabout:
            lc = (lat + hw - sec.edge_strip) / max(float(sec.lane_w), 2.0)
        else:
            lc = np.abs(lat) / max(float(sec.lane_w), 2.0)
        better = (dist < score) & (dist <= hw + 0.3)
        lane[better] = np.asarray(lc, float)[better]
        edge[better] = np.maximum(hw - dist, 0.0)[better]
        score[better] = dist[better]
    return np.column_stack([lane, edge])


def _patch_mat(net, j):'''
assert old in s
s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
