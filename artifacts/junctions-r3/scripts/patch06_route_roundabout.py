"""ADR 0095 patch 6 (after patch 5): start route through roundabouts on the carriageway axis (swept-path regression
of ADR 0076)."""
import io


def rd(p):
    return io.open(p, encoding="utf-8").read()


def wr(p, s):
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def rep(s, old, new):
    assert s.count(old) == 1, (s.count(old), old[:90])
    return s.replace(old, new)


p = "tools/worldgen/roads/route.py"
s = rd(p)
s = rep(s, '''JOINT_MILD_TURN_DEG = 60.0
''', '''JOINT_MILD_TURN_DEG = 60.0
# ADR 0095: on a roundabout ring and on the one-way arms next to it the route follows the carriageway axis, not the
# centre of the rightmost lane, blending back to the lane over RING_BLEND_M. With the lane centre (ADR 0076) the
# line hugged the outer kerb of the ring and cut the inner corner of the exit: the tridem of the 16.5 m combination
# ran 2.9 m (Rondo Biezenstwa, E 559 N -689) / 1.0 m (Rondo Putry, E -535 N 52) off the carriageway in
# tests/physics/test_swept_path_gate3 (was 1.1 m / clear on the OSM axes). A truck straddles the ring lanes anyway.
RING_BLEND_M = 30.0          # WORKING_VALUE
''')
s = rep(s, '''        lat = np.array([_right_lane_lat(c, sec, float(s), trav, lane) for s in ss])''',
        '''        lat = np.array([_right_lane_lat(c, sec, float(s), trav, lane) for s in ss])
        if sec.roundabout:
            lat[:] = 0.0
        elif sec.oneway:
            lat *= _smoothstep((ring_before[i_e] + np.abs(ss - s0)) / RING_BLEND_M) * \\
                _smoothstep((ring_after[i_e] + np.abs(s1 - ss)) / RING_BLEND_M)''')
s = rep(s, '''    for i_e, (eid, u, v) in enumerate(path_edges):
        c, sa, sb = _edge_span(net, eid)''', '''    # path distance from the end of the last roundabout edge before / to the first one after every edge
    elen = [abs(_edge_span(net, e_)[2] - _edge_span(net, e_)[1]) for e_, _, _ in path_edges]
    isr = [bool(net.sections[e_].roundabout) for e_, _, _ in path_edges]
    ring_before, ring_after = [1e9] * len(elen), [1e9] * len(elen)
    acc = 1e9
    for i_ in range(len(elen)):
        ring_before[i_] = acc
        acc = 0.0 if isr[i_] else acc + elen[i_]
    acc = 1e9
    for i_ in range(len(elen) - 1, -1, -1):
        ring_after[i_] = acc
        acc = 0.0 if isr[i_] else acc + elen[i_]
    for i_e, (eid, u, v) in enumerate(path_edges):
        c, sa, sb = _edge_span(net, eid)''')
wr(p, s)
print("ok")
