import sys; sys.path.insert(0,"tests/gis"); sys.path.insert(0,"tools/worldgen")
import test_rail_0217 as T, test_rail_approach_0255 as A
from streetscape import rail_props as RP
for kw in ({"barrier":"no"},{"barrier":"half","light":True}):
    p = A._plan(**kw); RP.PROTOS.clear(); pl, rep, boards = T._Placer(), {}, {}
    RP.place_approach(pl, p, T.road_z_at, rep, boards)
    pr = RP.prototypes()
    t0 = {k: sum(len(q["T"]) for q in v[0].out()) for k,v in pr.items()}
    t1 = {k: sum(len(q["T"]) for q in v[1].out()) for k,v in pr.items()}
    mats = {k: sorted({q["mat"] for q in v[0].out()}) for k,v in pr.items()}
    inst = {}
    for it in pl.items: inst[it["p"]] = inst.get(it["p"],0)+1
    print(kw, "instances", len(pl.items), "LoD0 tris", sum(t0[k]*n for k,n in inst.items()), "LoD1 tris", sum(t1[k]*n for k,n in inst.items()))
    for k in pr: print("  ", k, inst[k], "x", t0[k], "/", t1[k], mats[k])
    print("  boards", {k:(v[0],v[1],v[2].size) for k,v in boards.items()})
