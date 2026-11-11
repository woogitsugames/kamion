"""ADR 0117 patch 04 (applied once): free ends of queued rails swing onto a neighbouring rail (Y / V noses instead of
two rails ending side by side); pier rails are deduplicated against ground rails only (deck rails pass overhead)."""
import pathlib
p = pathlib.Path('tools/worldgen/streetscape/furniture.py')
s = p.read_text(encoding='utf-8')


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a, s.count(a))
    s = s.replace(a, b)


rep('''def _flush_rails(lin):
    for it in getattr(lin, "rail_queue", None) or []:
        guardrail(lin, it["P"], it["Z"], it["key"], it["tall"], it["term"])
    lin.rail_queue = None
''', '''def _join_free_ends(queue, m):
    """ADR 0117 (p0_kerb_merge_eye): an end of a run that stops within GUARDRAIL_JOIN_M of ANOTHER rail (a deck
    barrier starting 2 m beside the separator rail of the gore, two rails of one nose) swings onto it: the rails meet
    in a V / Y as on the orthophoto (E -781 N 76.5) instead of ending side by side. The end loses its terminal."""
    from shapely.geometry import LineString, Point
    from shapely.ops import nearest_points
    lines = [LineString(it["P"]) for it in queue]
    for i, it in enumerate(queue):
        Ps = it["P"]
        if len(Ps) < GUARDRAIL_JOIN_BLEND + 4:
            continue
        others = [l for j, l in enumerate(lines) if j != i]
        if not others:
            continue
        allb = shapely.union_all(others)
        for end in (0, -1):
            pe = Point(Ps[end])
            d = allb.distance(pe)
            if not (0.3 < d <= GUARDRAIL_JOIN_M):
                continue
            q = nearest_points(allb, pe)[0]
            dv = np.array([q.x, q.y]) - Ps[end]
            u = np.linspace(1.0, 0.0, GUARDRAIL_JOIN_BLEND + 1)[:-1]
            w = u * u * (3 - 2 * u)
            idx = np.arange(GUARDRAIL_JOIN_BLEND) if end == 0 else len(Ps) - 1 - np.arange(GUARDRAIL_JOIN_BLEND)
            Ps[idx] += dv[None, :] * w[:, None]
            t_ = list(it["term"])
            t_[end] = False
            it["term"] = tuple(t_)
            m["joined_free_ends"] = m.get("joined_free_ends", 0) + 1
        lines[i] = LineString(Ps)


def _flush_rails(lin, m=None):
    queue = getattr(lin, "rail_queue", None) or []
    if queue and m is not None:
        _join_free_ends(queue, m)
    for it in queue:
        guardrail(lin, it["P"], it["Z"], it["key"], it["tall"], it["term"])
    lin.rail_queue = None
    return [bool(np.all(it["tall"])) for it in queue]
''')
rep('''    _flush_rails(lin)
''', '''    deck_flags = _flush_rails(lin, m)
''')
rep('''    net.guardrail_built = built                # pier_guardrails (after the bridge supports exist) dedups against these''',
    '''    # pier_guardrails (after the bridge supports exist) dedups against the GROUND rails (deck rails pass overhead)
    net.guardrail_built = [b for b, dk in zip(built, deck_flags) if not dk] if len(deck_flags) == len(built) else built''')
p.write_text(s, encoding='utf-8', newline='\n')

p = pathlib.Path('tests/gis/test_hero_bridge.py')
s = p.read_text(encoding='utf-8')
rep("assert 11.0 < w < 11.6, w                                  # 8.0 m carriageway + 2 x (0.15 + 1.50) m",
    "assert 10.0 < w < 10.6, w                                  # 8.0 m carriageway + 2 x (0.15 + 1.00) m (ADR 0117 cap_w)")
p.write_text(s, encoding='utf-8', newline='\n')
print("patched")
