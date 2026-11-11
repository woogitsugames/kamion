"""ADR 0095 patch 3: height tie for add-up forks whose branches run side by side; center_offset profiles."""
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
s = rep(s, '''    center_offset_end: float | None = None   # authored: offset at the END of the edge (linear from center_offset)''',
        '''    center_offset_end: float | None = None   # authored: offset at the END of the edge (linear from center_offset)
    center_offset_profile: list | None = None  # authored: [[t, offset], ...], t = 0..1 along the edge (ADR 0095)''')
s = rep(s, '''                if isinstance(co, (list, tuple)):       # ADR 0095: [at the start, at the end] of the edge, linear
                    sec.center_offset, sec.center_offset_end = float(co[0]), float(co[1])''',
        '''                if isinstance(co, (list, tuple)) and co and isinstance(co[0], (list, tuple)):
                    prof = sorted((float(t), float(v)) for t, v in co)   # ADR 0095: [[t, offset], ...] along the edge
                    sec.center_offset_profile = prof
                    sec.center_offset, sec.center_offset_end = prof[0][1], prof[-1][1]
                elif isinstance(co, (list, tuple)):     # ADR 0095: [at the start, at the end] of the edge, linear
                    sec.center_offset, sec.center_offset_end = float(co[0]), float(co[1])''')
s = rep(s, '''    if any(s.center_offset or s.center_offset_end for s in secs):''',
        '''    if any(s.center_offset or s.center_offset_end or s.center_offset_profile for s in secs):''')
s = rep(s, '''            if rv:
                t = 1.0 - t
            return (v0 + (v1 - v0) * t) * (-1.0 if rv else 1.0)''', '''            if rv:
                t = 1.0 - t
            if sc.center_offset_profile:
                pr = sc.center_offset_profile
                return float(np.interp(t, [q[0] for q in pr], [q[1] for q in pr])) * (-1.0 if rv else 1.0)
            return (v0 + (v1 - v0) * t) * (-1.0 if rv else 1.0)''')
s = rep(s, '''            if sum(b["sec"].lanes for b in br) <= ssec.lanes:
                continue                                 # lanes add up (align_forks) or fewer: nothing to lay out''',
        '''            if sum(b["sec"].lanes for b in br) <= ssec.lanes:
                # lanes add up (align_forks) or fewer: nothing to lay out. ADR 0095: a branch that then runs edge to
                # edge with its neighbour (a ramp lane beside the main carriageway up to a painted gore) still
                # shares that neighbour's height surface - tie it like an overlapping branch.
                br.sort(key=lambda b: -b["lat"])
                ia = min(range(len(br)), key=lambda i: (abs(br[i]["ang"]), -br[i]["sec"].lanes))
                for i in range(len(br)):
                    if i != ia:
                        _tie_alongside(br[i]["c"], br[i]["e"], br[i + 1]["c"] if i < ia else br[i - 1]["c"], report, node)
                continue''')
s = rep(s, '''def abreast_forks(net: Network, report: list | None = None):''', '''ALONGSIDE_GAP_M = 1.0        # WORKING_VALUE: edges closer than this = one surface (painted separation at most)
ALONGSIDE_MIN_RUN_M = 15.0   # WORKING_VALUE


def _tie_alongside(c: Chain, e: str, nb: Chain, report: list, node: str):
    """Mark chain c (leaving `node` at end e) as sharing nb's height surface when their edges run within
    ALONGSIDE_GAP_M of each other for at least ALONGSIDE_MIN_RUN_M (no lateral move)."""
    if c.meta.get("abreast_of"):
        return
    idx = range(len(c.line.s)) if e == "a" else range(len(c.line.s) - 1, -1, -1)
    run, far = 0.0, 0.0
    for i in idx:
        d = float(c.line.s[i]) if e == "a" else float(c.length - c.line.s[i])
        if d > 250.0:
            break
        s_o, lat = nb.line.project(c.line.p[i])
        if s_o <= 1e-6 or s_o >= nb.length - 1e-6:
            continue
        io = nb.idx(s_o)
        if abs(float(np.dot(nb.line.t[io], c.line.t[i]))) < 0.7 or bool(nb.bridge[io]) != bool(c.bridge[i]):
            continue
        if abs(lat) - float(c.hw[i]) - float(nb.hw_at(s_o)) < ALONGSIDE_GAP_M:
            run += DENSE
            far = d
    if run >= ALONGSIDE_MIN_RUN_M:
        c.meta["abreast_of"] = nb.id
        c.meta["alongside_m"] = round(run, 1)
        report.append({"node": node, "chain": c.id, "beside": nb.id, "alongside_run_m": round(run, 1),
                       "to_m": round(far, 1), "shift_max_m": 0.0})


def abreast_forks(net: Network, report: list | None = None):''')
wr(p, s)

p = "Data/Regions/bialystok-industrial-c/overrides.yaml"
s = rd(p)
a = s.index("  - id: dk8-viaduct-w-ramp-lane-width")
b = s.index("  - id: ", a + 10)
s = s[:a] + '''  - id: dk8-viaduct-w-ramp-lane
    target: {edge: "w240542867:1847044963-1832991672"}
    reason: >-
      Ramp from Rondo Putry beside the main carriageway (strips xsec/km3.png along the ramp way, xsec/km_trunk0.png,
      xsec/km_trunk.png): one lane 3.7 m (stations 0-40 of the main chain) to 4.6 m in the curve (station 60);
      one width per edge: 4.2 m (WORKING_VALUE; was 5.5 m). The OSM way leaves the real lane towards the outside
      of the curve by up to 2.4 m between the separator nose and the merge (lane centre at stations 100 / 84 / 60 /
      44 / 20 of the ramp chain: 0 / 1.55 / 2.25 / 2.4 / 0.5 m left of the way in the direction of travel), so the
      generated ramp left a strip of grass where the P-21 and the solid line are. center_offset = [[t, m], ...]
      along the edge (t = 0 at its start on the viaduct side).
    confidence: medium
    verify: owner drive
    set: {width: 4.2, center_offset: [[0.0, 0.0], [0.28, 0.0], [0.40, 1.55], [0.57, 2.25], [0.68, 2.4], [0.86, 0.5], [1.0, 0.0]]}
''' + s[b:]
wr(p, s)
print("ok")
