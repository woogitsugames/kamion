"""ADR 0095 patch 5: lane_edges + explicit width (carriageway beyond the last lane), route keeps out of turn-only lanes."""
import io


def rd(p):
    return io.open(p, encoding="utf-8").read()


def wr(p, s):
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def rep(s, old, new):
    assert s.count(old) == 1, (s.count(old), old[:90])
    return s.replace(old, new)


p = "tools/worldgen/roads/network.py"
s = rd(p)
s = rep(s, '''                total = le[-1] if le else 0.0
                if len(le) >= 3 and 0 < le[-1] - le[-2] < 2.0:
                    le = le[:-1]                    # right edge strip''', '''                total = le[-1] if le else 0.0
                if len(le) >= 3 and 0 < le[-1] - le[-2] < 2.0:
                    le = le[:-1]                    # right edge strip
                if "width" in st and not isinstance(st["width"], (list, tuple)):
                    total = max(total, float(st["width"]))   # carriageway beyond the last lane (hatching, island)''')
s = rep(s, '''            elif "width" in st:
                # measured carriageway width (orthophoto): lanes keep their count, lane width follows
                sec.width = float(st["width"])''', '''            elif "width" in st and "lane_edges" not in st:
                # measured carriageway width (orthophoto): lanes keep their count, lane width follows
                sec.width = float(st["width"])''')
wr(p, s)

p = "tools/worldgen/roads/route.py"
s = rd(p)
s = rep(s, '''def _right_lane_lat(c, sec, s, trav):
    """Chain lateral (left +) of the rightmost lane centre for travel sign `trav` along the chain."""
    hw = float(c.hw_at(s))
    dirn = int(c.dirn[c.idx(s)])
    _, _, cen = lane_layout(sec, hw, dirn or 1)
    if sec.oneway:
        lat = cen["fwd"][-1] if cen["fwd"] else 0.0''', '''def _through_lane(sec):
    """Index (from the left) of the rightmost lane a vehicle going straight on may use, by turn:lanes; None = the
    rightmost lane. ADR 0095: the right lane of Andersa before the side street at n10015785253 is a right-turn lane
    that ends at a kerbed island - the route keeps to the lane beside it."""
    tl = sec.turn_fwd if sec.oneway else None
    if not tl or len(tl) != sec.lanes:
        return None
    ok = [i for i, t in enumerate(tl) if not t or t == "none" or "through" in t.split(";")]
    return ok[-1] if ok and ok[-1] != len(tl) - 1 else None


def _right_lane_lat(c, sec, s, trav, lane=None):
    """Chain lateral (left +) of the rightmost lane centre for travel sign `trav` along the chain (`lane`: index
    from the left on a one-way carriageway instead of the rightmost one)."""
    hw = float(c.hw_at(s))
    dirn = int(c.dirn[c.idx(s)])
    _, _, cen = lane_layout(sec, hw, dirn or 1)
    if sec.oneway:
        lat = cen["fwd"][-1 if lane is None else lane] if cen["fwd"] else 0.0''')
s = rep(s, '''    secs = net.sec_list
    pieces = []
    for eid, u, v in path_edges:
        c, sa, sb = _edge_span(net, eid)''', '''    secs = net.sec_list
    pieces = []
    spans = []
    for eid, u, v in path_edges:
        c, sa, sb = _edge_span(net, eid)
        fw = float(np.hypot(*(c.line.point(sa) - np.asarray(node_xy[u], float)))) <= \\
            float(np.hypot(*(c.line.point(sb) - np.asarray(node_xy[u], float))))
        s_in, s_out = (sa, sb) if fw else (sb, sa)
        sg = 1.0 if fw else -1.0
        spans.append((c.line.frame(s_in)[0] * sg, c.line.frame(s_out)[0] * sg))
    for i_e, (eid, u, v) in enumerate(path_edges):
        c, sa, sb = _edge_span(net, eid)''')
s = rep(s, '''        sec = net.sections[eid]
        lat = np.array([_right_lane_lat(c, sec, float(s), trav) for s in ss])''', '''        sec = net.sections[eid]
        lane = None
        if i_e + 1 < len(path_edges):       # going straight on at the end of this edge: not in a turn-only lane
            if float(np.dot(spans[i_e][1], spans[i_e + 1][0])) > math.cos(math.radians(20.0)):
                lane = _through_lane(sec)
        lat = np.array([_right_lane_lat(c, sec, float(s), trav, lane) for s in ss])''')
wr(p, s)
print("ok")
