import json, pickle, sys, copy
sys.path.insert(0, "tools/worldgen")
from roads import pipeline, tunnels as TN, consistency as CQ
R = "bialystok-kleeberga"
g = json.loads((pipeline.REGIONS / R / "roads.graph.json").read_text(encoding="utf-8"))
for run_tn in (False, True):
    d = pickle.load(open("artifacts/tunnel-0211/dev_dump.pkl", "rb"))
    w = d["w"]
    if run_tn:
        TN.build(w, R, d["zc"], d["mask"], [], g, lambda *a: None)
    rep = CQ.check(w, [], R, pipeline)
    if run_tn:
        for c in rep["cases"]:
            if c["kind"] == "obstacle_in_lane": print(round(c["e"]), round(c["n"]), c["chain"][:30], c.get("what"), c.get("surface"), c.get("lane"), c.get("s"))
    print("tunnel" if run_tn else "base", {k: v for k, v in rep.items() if k in ("by_kind", "count")} if isinstance(rep, dict) else rep)

