"""numbers.py <before tag> <after tag>: before / after numbers of ADR 0110 from artifacts/junctions-r4/logs (markdown rows)."""
import json, re, sys, subprocess
A, B = sys.argv[1], sys.argv[2]
L = "artifacts/junctions-r4/logs/"
def j(t, n):
    return json.load(open(f"{L}{t}_{n}.json", encoding="utf-8"))
def row(name, a, b):
    print(f"| {name} | {a} | {b} |")
print("| miara | przed (b0 = main 7a685901 + pole P-21) | po |\n|---|---|---|")
wa, wb = j(A, "terrain_walls_qa"), j(B, "terrain_walls_qa")
row("ściany terenu > 0,15 m (`terrain_walls_qa`: count / max)", f"{wa['count']} / {wa['max_m']}", f"{wb['count']} / {wb['max_m']} ({wb['by_source']})")
row("pasy trawy: strome trójkąty / pionowe ścianki / max (`verge_strips`)", "—", str({k: v for k, v in wb.get('verge_strips', {}).items() if k != 'worst'}))
ca, cb = j(A, "road_consistency_qa"), j(B, "road_consistency_qa")
row("road_consistency (wszystkie / na trasie)", f"{ca['count']} {ca['by_kind']} / {ca['on_route']}", f"{cb['count']} {cb['by_kind']} / {cb['on_route']}")
ra, rb = j(A, "roads_qa")["summary"], j(B, "roads_qa")["summary"]
row("override'y zastosowane / nieaktualne", f"{len(ra['overrides_applied'])} / {len(ra['overrides_stale'])}", f"{len(rb['overrides_applied'])} / {len(rb['overrides_stale'])}")
za = {z['id']: z for z in ra['painted_zones']}; zb = {z['id']: z for z in rb['painted_zones']}
n = 'n10015785253-p21-north'
row("pole P-21 n100 N: pasy (analityczne / w siatce), pole", f"{za[n]['stripes']} / ?, {za[n]['area_m2']} m²", f"{zb[n]['stripes']} / {zb[n].get('stripes_built')}, {zb[n]['area_m2']} m², pokrycie {zb[n].get('stripe_cover')}")
row("pola P-21: pasy razem", sum(z['stripes'] for z in za.values()), sum(z['stripes'] for z in zb.values()))
sa, sb = j(A, "streetscape_qa"), j(B, "streetscape_qa")
row("bariery [m] (`guardrails_m`)", sa['furniture']['guardrails_m'], sb['furniture']['guardrails_m'])
row("pasy trawy w terenie (trójkąty / chunki)", "—", rb.get('verge_strips'))
fa = {f['camera']: f for f in sa['mesh_budget']['frame_estimate']}; fb = {f['camera']: f for f in sb['mesh_budget']['frame_estimate']}
lo = [100 * (fb[k]['tris_low'] / fa[k]['tris_low'] - 1) for k in fa]; hi = [100 * (fb[k]['tris_high'] / fa[k]['tris_high'] - 1) for k in fa]
row("szacunek siatek na kadr (`mesh_budget.frame_estimate`, 23 kamery): Low min…max / High min…max", "0", f"{min(lo):+.1f}…{max(lo):+.1f} % / {min(hi):+.1f}…{max(hi):+.1f} %")
