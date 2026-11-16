"""Plot planner A/B on the same input (D34, docs/reports/WORLDGEN-K3B-2026-11-16.md). Analysis only: changes no generator
module. Three steps, so a change of streetscape/plots.py (e.g. K3b) can be measured and compared without a full build:

    # 1. capture the arguments of streetscape.plots.region_plan from pass 1 of build_world, then stop
    #    (--nmt flat|wave: synthetic NMT, no Data/raw; default raw = the lead's r16). Writes nothing to generated/.
    uv run --project tools/worldgen python tools/worldgen/qa/compare_plots.py capture --region bialystok-industrial-c --out artifacts/k3b/rp_c.pkl
    # 2. run region_plan of a checkout (any worktree) on it: canonical dump + timers (plan, layout, plan_access)
    uv run --project tools/worldgen python tools/worldgen/qa/compare_plots.py run --worktree <main wt> --input artifacts/k3b/rp_c.pkl --out artifacts/k3b/c_main.pkl
    uv run --project tools/worldgen python tools/worldgen/qa/compare_plots.py run --worktree <k3b wt> --input artifacts/k3b/rp_c.pkl --out artifacts/k3b/c_k3b.pkl
    # 3. diff: plot ids / order, polygon bytes and Hausdorff distance, fence runs, gates, wickets, access, kerb drops
    uv run --project tools/worldgen python tools/worldgen/qa/compare_plots.py diff artifacts/k3b/c_main.pkl artifacts/k3b/c_k3b.pkl

The pickle of step 1 holds shapely geometries and the road network object: trusted local data only (pickle runs code).
"""
from __future__ import annotations

import argparse
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np

WG = Path(__file__).resolve().parents[1]


class _Done(Exception):
    pass


def capture(a):
    sys.path.insert(0, str(WG))
    sys.path.insert(0, str(WG / "qa"))
    import profile_build_world as PBW
    if a.nmt != "raw":
        PBW.synthetic_nmt(a.nmt)
    from roads import build_world as BW
    from streetscape import far_field as FF
    from streetscape import plots as PLT
    FF.build_far_field = lambda region_id, out_root=None: {"tiers": {}}
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    def cap(*x, **y):
        out.write_bytes(pickle.dumps((x, y), protocol=5))
        print(f"captured {out} ({out.stat().st_size} bytes)", flush=True)
        raise _Done()
    PLT.region_plan = cap
    try:
        BW.build(a.region, out_root=out.parent / f"world-{a.region}", verbose=True, route_graph=False)
    except _Done:
        return 0
    print("region_plan was never called (KAMION_NO_PLOTS=1 or a region without houses?)")
    return 1


def _arr(x):
    return None if x is None else np.asarray(x, float).tolist()


def run(a):
    wt = Path(a.worktree).resolve()
    sys.path.insert(0, str(wt / "tools" / "worldgen"))
    args, kw = pickle.loads(Path(a.input).read_bytes())
    from streetscape import plots as PLT
    if not Path(PLT.__file__).resolve().is_relative_to(wt):
        raise SystemExit(f"imported {PLT.__file__}, not from {wt}")
    T = {}

    def wrap(name):
        f = getattr(PLT, name)

        def inner(*x, **y):
            t = time.perf_counter()
            try:
                return f(*x, **y)
            finally:
                r = T.setdefault(name, [0, 0.0])
                r[0] += 1
                r[1] += time.perf_counter() - t
        setattr(PLT, name, inner)
    for n in ("plan", "layout", "plan_access", "door_zones", "gate_access"):
        wrap(n)
    t0 = time.perf_counter()
    rp = PLT.region_plan(*args, **kw)
    T["region_plan"] = [1, time.perf_counter() - t0]

    def lay(L):
        def g(d):
            return None if d is None else {"m": _arr(d["m"]), "w": d["w"], "kind": d["kind"]}
        return {"runs": [{"style": r["style"], "h": r["h"], "a": _arr(r["a"]), "b": _arr(r["b"]), "front": r["front"]}
                         for r in L["runs"]],
                "gate": g(L["gate"]), "wicket": g(L["wicket"]), "wickets": [g(w) for w in L["wickets"]],
                "stubs_dropped": L.get("stubs_dropped", 0), "teeth_bridged": L.get("teeth_bridged", 0)}
    res = []
    for p in rp["plots"]:
        ac = p.get("access")
        res.append({"id": p["id"], "wkb": p["poly"].wkb, "coords": np.asarray(p["poly"].exterior.coords).tolist(),
                    "area": p["poly"].area, "age": p["age"], "front_style": p["front_style"], "lay": lay(p["lay"]),
                    "access": None if ac is None else {"chain": ac.get("chain"), "side": ac.get("side"), "s": ac.get("s"),
                                                       "q": _arr(ac.get("q"))}})
    drops = [{k: (_arr(v) if isinstance(v, np.ndarray) else v) for k, v in d.items()} for d in rp["drops"]]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_bytes(pickle.dumps({"plots": res, "drops": drops, "astats": rp["access_stats"], "T": T}))
    print(json.dumps({"timers_s": {k: [v[0], round(v[1], 2)] for k, v in T.items()}, "plots": len(res), "drops": len(drops),
                      "access_stats": rp["access_stats"]}))
    return 0


def diff(a):
    import shapely
    A = pickle.loads(Path(a.a).read_bytes())
    B = pickle.loads(Path(a.b).read_bytes())
    pa, pb = {p["id"]: p for p in A["plots"]}, {p["id"]: p for p in B["plots"]}
    common = sorted(set(pa) & set(pb))
    r = {"plots": [len(pa), len(pb)], "only_a": sorted(set(pa) - set(pb)), "only_b": sorted(set(pb) - set(pa)),
         "order_same": [p["id"] for p in A["plots"]] == [p["id"] for p in B["plots"]]}
    haus, ex, nv, same, lay_same = [], [], 0, 0, 0
    for i in common:
        x, y = pa[i], pb[i]
        if x["wkb"] == y["wkb"]:
            same += 1
        else:
            ga, gb = shapely.from_wkb(x["wkb"]), shapely.from_wkb(y["wkb"])
            h = ga.hausdorff_distance(gb)
            haus.append(h)
            nv += len(x["coords"]) != len(y["coords"])
            ex.append((h, i, round(ga.area, 3), round(gb.area, 3)))
    r.update(poly_bytes_same=same, poly_bytes_diff=len(haus), poly_vertex_count_diff=nv)
    if haus:
        h = np.array(haus)
        r["hausdorff_m"] = {f"p{q}": float(np.percentile(h, q)) for q in (50, 90, 99, 100)}
        r["hausdorff_over"] = {"1mm": int((h > 1e-3).sum()), "10cm": int((h > 0.1).sum()), "1m": int((h > 1.0).sum())}
        r["worst"] = sorted(ex, reverse=True)[:8]

    def rl(p):
        return sum(float(np.hypot(*(np.array(q["b"]) - np.array(q["a"])))) for q in p["lay"]["runs"])
    mx, gate_ch, wick_ch, acc_ch, runs_ch, flen = 0.0, [], [], [], [], []
    for i in common:
        x, y = pa[i], pb[i]
        if x["lay"] == y["lay"]:
            lay_same += 1
        for ra, rb in zip(x["lay"]["runs"], y["lay"]["runs"]):
            for e in "ab":
                mx = max(mx, float(np.max(np.abs(np.array(ra[e]) - np.array(rb[e])))))
        ga, gb = x["lay"]["gate"], y["lay"]["gate"]
        if (ga is None) != (gb is None) or (ga and np.hypot(*(np.array(ga["m"]) - np.array(gb["m"]))) > 1e-3):
            gate_ch.append(i)
        wa = [x["lay"]["wicket"]] + x["lay"]["wickets"]
        wb = [y["lay"]["wicket"]] + y["lay"]["wickets"]
        if sum(w is not None for w in wa) != sum(w is not None for w in wb):
            wick_ch.append(i)
        aa, ab = x["access"], y["access"]
        if (aa is None) != (ab is None) or (aa and (aa["chain"], aa["side"]) != (ab["chain"], ab["side"])):
            acc_ch.append(i)
        if len(x["lay"]["runs"]) != len(y["lay"]["runs"]):
            runs_ch.append(i)
        d = rl(y) - rl(x)
        if abs(d) > 1e-3:
            flen.append((round(d, 3), i))
    r.update(layout_same=lay_same, layout_diff=len(common) - lay_same, run_endpoint_max_diff_m=mx,
             gate_changed=gate_ch, wicket_count_changed=wick_ch, access_changed=acc_ch, run_count_changed=runs_ch,
             fence_len_changed=sorted(flen, key=lambda q: -abs(q[0]))[:12],
             fence_len_total_m=[round(sum(rl(p) for p in A["plots"]), 3), round(sum(rl(p) for p in B["plots"]), 3)],
             gates=[sum(p["lay"]["gate"] is not None for p in A["plots"]), sum(p["lay"]["gate"] is not None for p in B["plots"])],
             runs=[sum(len(p["lay"]["runs"]) for p in A["plots"]), sum(len(p["lay"]["runs"]) for p in B["plots"])],
             drops_same=A["drops"] == B["drops"], drops=[len(A["drops"]), len(B["drops"])],
             access_stats=[A["astats"], B["astats"]],
             timers_s=[{k: round(v[1], 2) for k, v in A["T"].items()}, {k: round(v[1], 2) for k, v in B["T"].items()}])
    print(json.dumps(r, indent=1, default=str))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture")
    c.add_argument("--region", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--nmt", choices=("raw", "flat", "wave"), default="raw")
    r = sub.add_parser("run")
    r.add_argument("--worktree", required=True)
    r.add_argument("--input", required=True)
    r.add_argument("--out", required=True)
    d = sub.add_parser("diff")
    d.add_argument("a")
    d.add_argument("b")
    a = ap.parse_args()
    sys.stdout.reconfigure(line_buffering=True)
    return {"capture": capture, "run": run, "diff": diff}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
