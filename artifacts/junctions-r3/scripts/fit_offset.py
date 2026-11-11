"""Fit a center_offset profile of one edge so the generated centre line passes through traced lane-centre points.

    fit_offset.py <override-id> <edge-id> "t0,t1,..." E,N E,N ...
Knots listed are free; other knots of the existing profile stay. Prints the fitted profile (YAML flow list)."""
import json
import sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import network as Nw
from roads import pipeline
from roads.geom import Polyline

RID = "bialystok-industrial-c"
oid, eid = sys.argv[1], sys.argv[2]
free = [float(v) for v in sys.argv[3].split(",")]
tg = np.array([[float(v) for v in a.split(",")] for a in sys.argv[4:]])
region = pipeline.load_region(RID)
origin = (region["origin"]["x"], region["origin"]["y"])
graph = json.loads((pipeline.REGIONS / RID / "roads.graph.json").read_text(encoding="utf-8"))
ovs = pipeline.load_overrides(RID)
ov = next(o for o in ovs if o["id"] == oid)
prof = {float(t): float(v) for t, v in ov["set"]["center_offset"]}
for t in free:
    prof.setdefault(t, float(np.interp(t, sorted(prof), [prof[k] for k in sorted(prof)])))


def build():
    ov["set"]["center_offset"] = [[t, prof[t]] for t in sorted(prof)]
    net = Nw.load(graph, origin, ovs)
    Nw.taper_forks(net, [])
    Nw.align_forks(net, [])
    Nw.abreast_forks(net, [])
    c = next(c for c in net.chains if any(e == eid for e, _ in c.edges))
    return c


for it in range(8):
    c = build()
    a0, a1, _, rv = next(sp for sp in c.raw_spans if sp[2] == eid)
    raw = Polyline(np.asarray(c.raw, float))
    errs = []
    for p in tg:
        s_r, _ = raw.project(p)
        t = float(np.clip((s_r - a0) / max(a1 - a0, 1e-6), 0, 1))
        t = 1 - t if rv else t
        _, lat = c.line.project(p)              # + = target is chain-left of the line
        errs.append((t, lat * (-1.0 if rv else 1.0)))   # edge frame: + = target left of the line (travel dir)
    print("iter", it, "errors (t, m left):", [(round(t, 3), round(e, 2)) for t, e in errs])
    if max(abs(e) for _, e in errs) < 0.15:
        break
    for t, e in errs:
        ks = sorted(free, key=lambda k: abs(k - t))[:2]
        w = [1.0 / (abs(k - t) + 0.02) for k in ks]
        for k, wk in zip(ks, w):
            prof[k] += 0.7 * e * wk / sum(w)
print("center_offset:", json.dumps([[t, round(prof[t], 2)] for t in sorted(prof)]))
