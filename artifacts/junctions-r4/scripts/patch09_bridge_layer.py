"""ADR 0110 step 3c: a run with a bridge barrier-railing is meshed in the `bridge` layer (draw budget: in the furniture
chunk mesh it enlarged the bounds of fences / hedges of the chunk and pulled 8 more draws into frames that see the
viaduct; the bridge mesh is drawn whenever the deck is)."""
p = 'tools/worldgen/streetscape/furniture.py'
s = open(p, encoding='utf-8').read()
old = '''    n = len(P)
    tall = np.zeros(n, bool) if tall is None else np.asarray(tall, bool)
    top = np.full(n, S.GUARDRAIL_H)
'''
new = '''    n = len(P)
    tall = np.zeros(n, bool) if tall is None else np.asarray(tall, bool)
    first = len(lin.buf.parts)
    top = np.full(n, S.GUARDRAIL_H)
'''
assert old in s; s = s.replace(old, new)
old = '''    lin.buf.add("furniture", "barrier_steel", V, UV, T, src=key)
    lin.buf.add("furniture", "barrier_steel", V, UV, T[:, [0, 2, 1]], src=key)
    lin.buf.add("collision", "collision_steel", V, UV, np.concatenate([T, T[:, [0, 2, 1]]]), src=key)


# ADR 0110: posts share'''
new = '''    lin.buf.add("furniture", "barrier_steel", V, UV, T, src=key)
    lin.buf.add("furniture", "barrier_steel", V, UV, T[:, [0, 2, 1]], src=key)
    if tall.any():
        # ADR 0110: a run on a deck belongs to the bridge mesh of its chunk (drawn with the deck), not to the furniture
        # mesh (fences, hedges: its bounds grew by the viaduct and 8 more draws entered frames beside it)
        for prt in lin.buf.parts[first:]:
            if prt.layer == "furniture":
                prt.layer = "bridge"
    lin.buf.add("collision", "collision_steel", V, UV, np.concatenate([T, T[:, [0, 2, 1]]]), src=key)


# ADR 0110: posts share'''
assert old in s; s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
p = 'tools/worldgen/streetscape/hero_bridge.py'
s = open(p, encoding='utf-8').read()
old = '''or (p.layer in ("furniture", "collision") and p.src.rsplit(":", 1)[-1] in rails)]'''
new = '''or (p.layer in ("furniture", "collision", "bridge") and p.mat in ("barrier_steel", "barrier_post",
                                                                                           "collision_steel")
                               and p.src.rsplit(":", 1)[-1] in rails)]'''
assert old in s; s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
