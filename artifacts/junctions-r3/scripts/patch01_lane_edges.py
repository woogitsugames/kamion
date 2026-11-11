"""ADR 0095 step 1 patch (applied once; kept as a record of the edit): measured lane edges + edge-line overrides."""
import io


def rd(p):
    return io.open(p, encoding="utf-8").read()


def wr(p, s):
    io.open(p, "w", encoding="utf-8", newline="\n").write(s)


def rep(s, old, new, n=1):
    assert s.count(old) >= 1, old[:80]
    return s.replace(old, new, n)


p = "tools/worldgen/roads/network.py"
s = rd(p)
s = rep(s, '''    center_offset: float = 0.0  # authored: carriageway centre this far LEFT of the OSM way (edge direction), m (ADR 0077)
    provenance: dict = field(default_factory=dict)
''', '''    center_offset: float = 0.0  # authored: carriageway centre this far LEFT of the OSM way (edge direction), m (ADR 0077)
    # ADR 0095 (measured on the orthophoto, one-way carriageways only): distances from the LEFT carriageway edge in the
    # direction of travel to [start of lane 1, lane boundary 1|2, ..., end of the last lane]. lane_edges[0] is the
    # left edge strip / gutter, lane_edges[-1] the carriageway width; lanes need not be equal.
    lane_edges: list | None = None
    edge_lines: str | None = None   # painted edge lines in the direction of travel: none | left | right | both
    provenance: dict = field(default_factory=dict)

    def lane_coord(self, lat, hw, dirn=1):
        """Lane coordinate across the carriageway (0 = first lane boundary, +1 per lane) for wheel-path weathering
        and paint UVs; follows the measured lane edges where they exist."""
        lat = np.asarray(lat, float)
        if self.lane_edges and self.oneway:
            x = np.asarray(hw, float) - (float(dirn) or 1.0) * lat
            le = np.asarray(self.lane_edges, float)
            return np.interp(x, le, np.arange(len(le), dtype=float))
        return (lat + np.asarray(hw, float) - self.edge_strip) / max(float(self.lane_w), 2.0)
''')
s = rep(s, '''            if "center_offset" in st:
                # the OSM way is not''', '''            if "lane_edges" in st:
                # ADR 0095: lanes as measured on the orthophoto (count, widths and edge strip in one list)
                le = [float(v) for v in st["lane_edges"]]
                if not sec.oneway or len(le) < 2 or any(b - a < 2.0 for a, b in zip(le, le[1:])) or le[0] < 0:
                    if ov["id"] not in net.overrides_stale:
                        net.overrides_stale.append(ov["id"])
                    sec.provenance["lane_edges_rejected"] = le
                else:
                    sec.lane_edges = le
                    sec.lanes = sec.lanes_fwd = len(le) - 1
                    sec.edge_strip = le[0]
                    sec.width = le[-1]
                    sec.lane_w = round((le[-1] - le[0]) / sec.lanes, 3)
                    sec.width_src = f"authored_override:{ov['id']} (lane_edges, orthophoto)"
                    if "turn_lanes" not in st and sec.turn_fwd and len(sec.turn_fwd) != sec.lanes:
                        sec.turn_fwd = None
            if "edge_lines" in st:
                sec.edge_lines = str(st["edge_lines"])
            if "turn_lanes" in st:
                sec.turn_fwd = [t for t in str(st["turn_lanes"]).split("|")] if st["turn_lanes"] else None
            if "center_offset" in st:
                # the OSM way is not''')
wr(p, s)

p = "tools/worldgen/roads/markings.py"
s = rd(p)
s = rep(s, '''    hw = np.asarray(c.hw_at(s), float)
    lanec = (lat + hw - edge) / lw if ring else np.abs(lat) / lw
''', '''    hw = np.asarray(c.hw_at(s), float)
    lanec = (lat + hw - edge) / lw if ring else np.abs(lat) / lw
    if _SECS and getattr(sec, "lane_edges", None):
        lanec = sec.lane_coord(lat, hw, int(c.dirn[c.idx(sm)]) or 1)
''')
s = rep(s, '''    lw, e = sec.lane_w, sec.edge_strip
    if sec.oneway:
''', '''    lw, e = sec.lane_w, sec.edge_strip
    le = getattr(sec, "lane_edges", None)
    if le and sec.oneway:
        # ADR 0095: measured lane edges, distances from the left edge in the direction of travel
        d = int(dirn) or 1
        bounds = [d * (hw - x) for x in le[1:-1]]
        centres = [d * (hw - 0.5 * (a + b)) for a, b in zip(le, le[1:])]
        return None, bounds, {"fwd": centres, "bwd": []}
    if sec.oneway:
''')
s = rep(s, '''def build_markings(buf: MeshBuf, net, juncs, ctx_points, report: dict):
    first''', '''def follow_edge(sec, lat, hw_mid, hw_s, dirn):
    """A lane line of a one-way carriageway keeps its distance from the gutter it was laid out from where the
    half-width changes (hw_mid at the layout station, hw_s where it is painted)."""
    sg = (int(dirn) or 1) if getattr(sec, "lane_edges", None) else 1
    return sg * (hw_s - (hw_mid - sg * lat))


def edge_lines(sec, hw, dirn):
    """[(lat, kind)] of the painted edge lines of a section at half-width hw (scalar or array). Default rule:
    P-7b on both sides of class A / S / GP roads with an edge strip. `edge_lines` (override, direction of travel)
    narrows it; a section with measured `lane_edges` paints only what `edge_lines` names (ADR 0095)."""
    if sec.roundabout:
        return []
    el = getattr(sec, "edge_lines", None)
    le = getattr(sec, "lane_edges", None)
    d = int(dirn) or 1
    half = S.LINE_W_WIDE / 2
    out = []
    if le and sec.oneway:
        el = el or "none"
        if el in ("left", "both"):
            out.append((d * (hw - (le[0] - half if le[0] >= S.LINE_W_WIDE else le[0] + half)), "P-7b"))
        if el in ("right", "both"):
            out.append((d * (hw - (le[-1] - half)), "P-7b"))
        return out
    if sec.cls in ("A", "S", "GP") and sec.edge_strip > 0 and el != "none":
        for sg, name in ((1, "left"), (-1, "right")):       # sg in the travel frame: +1 = travel-left
            if el in (None, "both", name):
                out.append(((d if sec.oneway else 1) * sg * (hw - sec.edge_strip + half), "P-7b"))
    return out


def build_markings(buf: MeshBuf, net, juncs, ctx_points, report: dict):
    first''')
s = rep(s, '''                    if sec.oneway:            # one-way lane lines are laid out from the left gutter: follow it
                        dl = float(lat) - hw
                        lat = (lambda ss_, dl=dl: c.hw_at(ss_) + dl)''', '''                    if sec.oneway:            # one-way lane lines are laid out from the left gutter: follow it
                        lat = (lambda ss_, l0=float(lat), sec=sec, hw=hw, dirn=dirn:
                               follow_edge(sec, l0, hw, c.hw_at(ss_), dirn))''')
s = rep(s, '''                if sec.cls in ("A", "S", "GP") and sec.edge_strip > 0 and not sec.roundabout:
                    for sg in (-1, 1):
                        strip(buf, c, sa, sb, (lambda ss_, sg=sg, e=sec.edge_strip:
                                               sg * (c.hw_at(ss_) - e + S.LINE_W_WIDE / 2)), S.LINE_W_WIDE, "P-7b")
                    cnt("P-7b edge line", 2)''', '''                for k_e, _ in enumerate(edge_lines(sec, hw, dirn)):
                    strip(buf, c, sa, sb, (lambda ss_, k_e=k_e, sec=sec, dirn=dirn:
                                           edge_lines(sec, c.hw_at(ss_), dirn)[k_e][0]), S.LINE_W_WIDE, "P-7b")
                    cnt("P-7b edge line")''')
wr(p, s)

p = "tools/worldgen/roads/through_lines.py"
s = rd(p)
a = s.index("    out = []\n    real_edges = False")
b = s.index("    return out, sec\n\n\nclass _Top")
s = s[:a] + '''    out = []
    painted = []
    if sec.highway in marked_hw or sec.roundabout:
        for lat in bounds:
            out.append((float(MKf.follow_edge(sec, float(lat), hw_mid, hw, dirn)) if sec.oneway else float(lat), "lane"))
        if lat_c is not None and sec.width >= S.SEGREGATION_MIN_CARRIAGEWAY:
            out.append((float(lat_c), "P-4" if sec.lanes >= 4 else "centre"))
        painted = [(float(lat), kind) for lat, kind in MKf.edge_lines(sec, hw, dirn)]
        out += painted
    # the bare carriageway edge (inside the edge strip) on every side without a painted edge line
    le = getattr(sec, "lane_edges", None)
    for sg in (-1, 1):
        if any(lat * sg > 0 and abs(lat) > hw - 1.5 for lat, _ in painted):
            continue
        if le and sec.oneway:
            d = int(dirn) or 1
            out.append((d * (hw - le[0]) if sg * d > 0 else d * (hw - le[-1]), "edge"))
        else:
            out.append((sg * (hw - max(float(sec.edge_strip), 0.0)), "edge"))
''' + s[b:]
s = rep(s, "def chain_lines_at(c, s, secs, s0, s1, marked_hw, lane_layout):",
        "def chain_lines_at(c, s, secs, s0, s1, marked_hw, lane_layout):\n    from . import markings as MKf")
wr(p, s)

p = "tools/worldgen/roads/meshing.py"
s = rd(p)
s = rep(s, '''            if sec_mid.oneway or sec_mid.roundabout:
                lanec = (latv + hwv - sec_mid.edge_strip) / lw''', '''            if getattr(sec_mid, "lane_edges", None):
                lanec = sec_mid.lane_coord(latv, hwv, int(c.dirn[c.idx(0.5 * (s0 + s1))]) or 1)
            elif sec_mid.oneway or sec_mid.roundabout:
                lanec = (latv + hwv - sec_mid.edge_strip) / lw''')
wr(p, s)

p = "tools/worldgen/roads/build_world.py"
s = rd(p)
old = '''        lat_l = -trav * (hw - sec.edge_strip - sec.lane_w / 2)     # rightmost lane of travel'''
s = rep(s, old, old + '''
        if getattr(sec, "lane_edges", None):
            lat_l = float(MK.lane_layout(sec, hw, trav)[2]["fwd"][-1])''')
wr(p, s)
print("ok")
