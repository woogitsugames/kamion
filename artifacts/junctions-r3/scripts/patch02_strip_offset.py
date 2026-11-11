"""ADR 0095 patch 2: lane_edges with a right edge strip (last interval < 2 m), center_offset as [start, end]."""
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
s = rep(s, '''    # direction of travel to [start of lane 1, lane boundary 1|2, ..., end of the last lane]. lane_edges[0] is the
    # left edge strip / gutter, lane_edges[-1] the carriageway width; lanes need not be equal.
    lane_edges: list | None = None''', '''    # direction of travel to [start of lane 1, lane boundary 1|2, ..., end of the last lane]. lane_edges[0] is the
    # left edge strip / gutter; lanes need not be equal. In the override a last interval narrower than 2 m is the
    # right edge strip (shoulder beyond the right edge line): it sets `width`, not a lane.
    lane_edges: list | None = None
    center_offset_end: float | None = None   # authored: offset at the END of the edge (linear from center_offset)''')
s = rep(s, '''                le = [float(v) for v in st["lane_edges"]]
                if not sec.oneway or len(le) < 2 or any(b - a < 2.0 for a, b in zip(le, le[1:])) or le[0] < 0:''',
        '''                le = [float(v) for v in st["lane_edges"]]
                total = le[-1] if le else 0.0
                if len(le) >= 3 and 0 < le[-1] - le[-2] < 2.0:
                    le = le[:-1]                    # right edge strip
                if not sec.oneway or len(le) < 2 or any(b - a < 2.0 for a, b in zip(le, le[1:])) or le[0] < 0:''')
s = rep(s, '''                    sec.width = le[-1]
                    sec.lane_w = round((le[-1] - le[0]) / sec.lanes, 3)''', '''                    sec.width = total
                    sec.lane_w = round((le[-1] - le[0]) / sec.lanes, 3)''')
s = rep(s, '''                sec.center_offset = float(st["center_offset"])
                sec.provenance["center_offset_m"] = sec.center_offset''', '''                co = st["center_offset"]
                if isinstance(co, (list, tuple)):       # ADR 0095: [at the start, at the end] of the edge, linear
                    sec.center_offset, sec.center_offset_end = float(co[0]), float(co[1])
                else:
                    sec.center_offset = float(co)
                sec.provenance["center_offset_m"] = co''')
s = rep(s, '''    if any(s.center_offset for s in secs):
        # authored lateral placement (ADR 0077): shift the carriageway centre off the OSM way, blended over 20 m
        L0 = c.raw_spans[-1][1]
        s0 = c.line.s * (L0 / max(c.line.length, 1e-9))
        k0 = np.clip(np.searchsorted([sp[1] for sp in c.raw_spans], s0, side="left"), 0, len(c.raw_spans) - 1)
        off = np.array([net.sections[c.raw_spans[i][2]].center_offset * (-1.0 if c.raw_spans[i][3] else 1.0)
                        for i in k0])''', '''    if any(s.center_offset or s.center_offset_end for s in secs):
        # authored lateral placement (ADR 0077): shift the carriageway centre off the OSM way, blended over 20 m
        L0 = c.raw_spans[-1][1]
        s0 = c.line.s * (L0 / max(c.line.length, 1e-9))
        k0 = np.clip(np.searchsorted([sp[1] for sp in c.raw_spans], s0, side="left"), 0, len(c.raw_spans) - 1)

        def _off(i, sr):
            a0, a1, eid, rv = c.raw_spans[i]
            sc = net.sections[eid]
            v0 = sc.center_offset
            v1 = v0 if sc.center_offset_end is None else sc.center_offset_end
            t = float(np.clip((sr - a0) / max(a1 - a0, 1e-6), 0.0, 1.0))
            if rv:
                t = 1.0 - t
            return (v0 + (v1 - v0) * t) * (-1.0 if rv else 1.0)
        off = np.array([_off(i, sr) for i, sr in zip(k0, s0)])''')
wr(p, s)

p = "tools/worldgen/roads/markings.py"
s = rd(p)
s = rep(s, '''        if el in ("right", "both"):
            out.append((d * (hw - (le[-1] - half)), "P-7b"))
        return out''', '''        if el in ("right", "both"):       # on the right edge strip where there is one, else just inside the edge
            strip_r = float(sec.width) - le[-1] >= S.LINE_W_WIDE
            out.append((d * (hw - (le[-1] + half if strip_r else le[-1] - half)), "P-7b"))
        return out''')
wr(p, s)
print("ok")
