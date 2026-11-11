"""ADR 0110: verge strips (now part of the terrain mesh) are reported on their own in terrain_walls_qa.json
("verge_strips"), skirt 1 : 2 instead of 1 : 1.5 (twisted run-out quads fell just under the 'steep grass' limit)."""
p = 'tools/worldgen/terrain_mesh/conform.py'
s = open(p, encoding='utf-8').read()
old = '''    def note(p, P, h, kind):
        hs.append(h)
'''
new = '''    vg = {"steep_grass": 0, "skirt": 0, "max_m": 0.0, "worst": []}

    def note(p, P, h, kind):
        if p.src.endswith(":vg"):
            # ADR 0110: grass strips behind kerbs (roads.meshing._emit_verge) are exported inside the terrain mesh;
            # they are counted on their own ("verge_strips"; ratchet in tests/gis/test_junctions_r4.py), not as walls
            # of the road profile
            vg[kind] += len(h)
            if len(h) and float(np.max(h)) > vg["max_m"]:
                k_ = int(np.argmax(h))
                vg["max_m"] = float(np.max(h))
                vg["worst"] = [kind, p.src, round(float(P[k_][0]), 1), round(float(P[k_][1]), 1)]
            return
        hs.append(h)
'''
assert old in s; s = s.replace(old, new)
old = '''                flag = (hv > thresh).any(1)
                if flag.any():'''
new = '''                flag = (hv > thresh).any(1)
                if flag.any() and not p.src.endswith(":vg"):'''
assert old in s; s = s.replace(old, new)
old = '''    if not hs:
        return {"thresh_m": thresh, "count": 0, "max_m": 0.0, "p99_m": 0.0, "by_source": {}, "worst": [],
                "skirt_area": [], "thin_steep_faces_skipped": slivers[0]}'''
new = '''    vg["max_m"] = round(vg["max_m"], 3)
    if not hs:
        return {"thresh_m": thresh, "count": 0, "max_m": 0.0, "p99_m": 0.0, "by_source": {}, "worst": [],
                "skirt_area": [], "thin_steep_faces_skipped": slivers[0], "verge_strips": vg}'''
assert old in s; s = s.replace(old, new)
old = '''            "sliver_m2": SLIVER_M2, "skirt_area": rows, "thin_steep_faces_skipped": slivers[0],'''
new = '''            "sliver_m2": SLIVER_M2, "skirt_area": rows, "thin_steep_faces_skipped": slivers[0], "verge_strips": vg,'''
assert old in s; s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)

p = 'tools/worldgen/roads/standards.py'
s = open(p, encoding='utf-8').read()
old = '''MEDIAN_VERGE_MAX = 3.00 '''
new = '''VERGE_SKIRT_SLOPE = 2.0              # WORKING_VALUE (ADR 0110): run per unit fall of the grass skirt of a verge strip
MEDIAN_VERGE_MAX = 3.00 '''
assert old in s; s = s.replace(old, new)
open(p, 'w', encoding='utf-8', newline='\n').write(s)

p = 'tools/worldgen/roads/meshing.py'
s = open(p, encoding='utf-8').read()
a = s.index('def _emit_verge('); b = s.index('# ADR 0100 (REVIEW s10-0095 P1-8): a concrete strip wider than a kerb top')
body = s[a:b]
assert body.count('S.EMBANKMENT_SLOPE') == 2
body = body.replace('(1 : EMBANKMENT_SLOPE, FLANGE_DEPTH deep)', '(1 : VERGE_SKIRT_SLOPE, FLANGE_DEPTH deep)')
body = body.replace('S.FLANGE_DEPTH * S.EMBANKMENT_SLOPE', 'S.FLANGE_DEPTH * S.VERGE_SKIRT_SLOPE').replace('depth * S.EMBANKMENT_SLOPE', 'depth * S.VERGE_SKIRT_SLOPE')
body = body.replace('same 1:1.5 slope', 'same 1:2 slope')
s = s[:a] + body + s[b:]
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('ok')
