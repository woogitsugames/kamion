"""ADR 0117 patch 02 (applied once): cut rail ends join the rail that cut them, authored rails first (queued build),
upper beam slopes down at every end, darker zinc, smoother Putry N nose."""
import pathlib
p = pathlib.Path('tools/worldgen/streetscape/furniture.py')
s = p.read_text(encoding='utf-8')
a = s.index("def _dedup_guardrail(lin, P, Z, key, built, m, tall=None, term=(True, True)):")
b = s.index("STRUCT_GUARD_GAP_M = 8.0")
new = r'''GUARDRAIL_JOIN_M = 4.0      # ADR 0117: a run cut by the dedup is led onto the rail that cut it when that is this close
GUARDRAIL_JOIN_BLEND = 8    # points (1 m) over which the cut end swings onto the other rail


def _dedup_guardrail(lin, P, Z, key, built, m, tall=None, term=(True, True)):
    """Build the parts of run P that are not within the dedup distance of a rail built before (two chains / a chain
    and an authored rail on the same separator crossed and overlapped at E -782 and on the viaduct approaches).

    ADR 0117 (REVIEW s10-0110 P1-6, p0_kerb_merge_eye): a cut end used to stop in the air beside the other rail,
    which itself dived into the ground 2 m further (two runs at two angles, two posts side by side). Now the cut
    end swings onto the nearest point of the rail that cut it (GUARDRAIL_JOIN_M) and, when runs are queued
    (`lin.rail_queue`, guardrails()), the end of that rail it lands on loses its turned-down terminal: one rail."""
    from shapely.geometry import LineString, Point
    from shapely.ops import nearest_points
    P = np.array(P, float)
    keep = np.ones(len(P), bool)
    tall = np.zeros(len(P), bool) if tall is None else np.asarray(tall, bool)
    allb = None
    if built:
        near = shapely.union_all([b.buffer(GUARDRAIL_DEDUP_M) for b in built])
        far = shapely.union_all([b.buffer(GUARDRAIL_DEDUP_GROUND_M) for b in built])
        allb = shapely.union_all(built)
        shapely.prepare(near)
        shapely.prepare(far)
        keep = ~np.where(tall, shapely.contains_xy(near, P[:, 0], P[:, 1]), shapely.contains_xy(far, P[:, 0], P[:, 1]))
    queue = getattr(lin, "rail_queue", None)

    def join(Ps, end):
        """Swing end `end` (0 / -1) of segment Ps onto the rail that cut it; True when joined."""
        q = nearest_points(allb, Point(Ps[end]))[0]
        q = np.array([q.x, q.y])
        dv = q - Ps[end]
        if float(np.hypot(*dv)) > GUARDRAIL_JOIN_M or len(Ps) < GUARDRAIL_JOIN_BLEND + 2:
            return False
        u = np.linspace(1.0, 0.0, GUARDRAIL_JOIN_BLEND + 1)[:-1]
        w = u * u * (3 - 2 * u)
        idx = np.arange(GUARDRAIL_JOIN_BLEND) if end == 0 else len(Ps) - 1 - np.arange(GUARDRAIL_JOIN_BLEND)
        Ps[idx] += dv[None, :] * w[:, None]
        m["joined_ends"] = m.get("joined_ends", 0) + 1
        if queue:
            for it in queue:                       # the rail it lands on: no turned-down terminal at that end
                for e_ in (0, -1):
                    if float(np.hypot(*(it["P"][e_] - q))) < 6.0:
                        t_ = list(it["term"])
                        t_[e_] = False
                        it["term"] = tuple(t_)
        return True

    k = 0
    while k < len(P):
        if not keep[k]:
            k += 1
            continue
        kk = k
        while kk + 1 < len(P) and keep[kk + 1]:
            kk += 1
        if kk - k + 1 >= GUARDRAIL_MIN_RUN:
            Ps = P[k:kk + 1].copy()
            # a cut made by the dedup is not a free end (the other rail carries on there)
            t0, t1 = term[0] and k == 0, term[1] and kk == len(P) - 1
            if allb is not None:
                if k > 0:
                    join(Ps, 0)
                if kk < len(P) - 1:
                    join(Ps, -1)
            it = {"P": Ps, "Z": Z[k:kk + 1], "key": key, "tall": tall[k:kk + 1], "term": (t0, t1)}
            if queue is not None:
                queue.append(it)
            else:
                guardrail(lin, it["P"], it["Z"], key, it["tall"], it["term"])
            built.append(LineString(Ps))
        else:
            m["dedup_dropped_pts"] = m.get("dedup_dropped_pts", 0) + (kk - k + 1)
        k = kk + 1
    m["dedup_skipped_pts"] = m.get("dedup_skipped_pts", 0) + int((~keep).sum())


def _flush_rails(lin):
    for it in getattr(lin, "rail_queue", None) or []:
        guardrail(lin, it["P"], it["Z"], it["key"], it["tall"], it["term"])
    lin.rail_queue = None


'''
s = s[:a] + new + s[b:]
# authored first + queue
a = s.index("    # ADR 0100: authored guardrails on kerbed separators traced on the orthophoto")
b = s.index('    report["guardrails_m"] = {k: round(v) for k, v in m.items()}')
auth = s[a:b]
s = s[:a] + "    _flush_rails(lin)\n" + s[b:]
head = "    structs = _structures(net)\n"
assert s.count(head) == 1
auth = ("    # ADR 0117: authored rails are built FIRST (they are traced; the rule runs give way and join them); runs are\n"
        "    # queued so that a later join can still cancel the turned-down terminal of the rail it lands on\n"
        "    lin.rail_queue = []\n" + auth)
s = s.replace(head, head + auth)
o = '''                if k > lo and kk - k >= 4:
                    zt[:3] = np.linspace(S.GUARDRAIL_H - 0.02, S.BRIDGE_BARRIER_H, 3)
                if kk + 1 < hi and kk - k >= 4:
                    zt[-3:] = np.linspace(S.BRIDGE_BARRIER_H, S.GUARDRAIL_H - 0.02, 3)'''
assert s.count(o) == 1
s = s.replace(o, '''                if kk - k >= 6:                       # every end (also a run end: no beam stopping in the air)
                    zt[:3] = np.linspace(S.GUARDRAIL_H - 0.02, S.BRIDGE_BARRIER_H, 3)
                    zt[-3:] = np.linspace(S.BRIDGE_BARRIER_H, S.GUARDRAIL_H - 0.02, 3)''')
p.write_text(s, encoding='utf-8', newline='\n')

p = pathlib.Path('tools/worldgen/roads/build_world.py')
s = p.read_text(encoding='utf-8')
a = '"barrier_steel": {"color": [0.25, 0.255, 0.26], "rough": 0.65'
assert a in s
s = s.replace(a, '"barrier_steel": {"color": [0.11, 0.112, 0.115], "rough": 0.65')
s = s.replace("Albedo 0.25 WORKING_VALUE\n    # from Mapillary",
              "Albedo 0.11 WORKING_VALUE (b1 with 0.25: beam sRGB ~185 at asphalt 60 in the High overcast frame of\n"
              "    # r4_deck_bz_eye; the photo has the beam at 74-102 at asphalt 63 - matched in the frame). Derivation\n"
              "    # from Mapillary")
p.write_text(s, encoding='utf-8', newline='\n')

p = pathlib.Path('Data/Regions/bialystok-industrial-c/overrides.yaml')
s = p.read_text(encoding='utf-8')
a = '''    surface: apron_sett
    polygon_en: [[-555.55, 130.3], [-555.5, 129.4], [-555.0, 128.75], [-554.2, 128.35], [-553.0, 128.2], [-551.8, 128.35],
                 [-551.0, 128.75], [-550.55, 129.4], [-550.5, 130.3]]'''
assert s.count(a) == 1
s = s.replace(a, '''    surface: sidewalk_paving
    # ADR 0117 (REVIEW s10-0110 P1-9, "placek-cokol"): smooth half ellipse (12 segments, was a half octagon), grey
    # setts as on the orthophoto (was beige apron_sett), tip N 128.8 (was 128.2)
    polygon_en: [[-555.6, 130.7], [-555.56, 130.21], [-555.3, 129.75], [-554.89, 129.36], [-554.35, 129.05],
                 [-553.72, 128.86], [-553.05, 128.8], [-552.38, 128.86], [-551.75, 129.05], [-551.21, 129.36],
                 [-550.8, 129.75], [-550.54, 130.21], [-550.5, 130.7]]''')
p.write_text(s, encoding='utf-8', newline='\n')
print("patched")
