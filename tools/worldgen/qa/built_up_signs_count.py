"""ADR 0279 D33, read-only: run the sign stage (junction_signs, osm_signs + built_up.rule_signs, roundabout_signs) on
the committed tile data (roads.graph.json + generated/streetscape_sources.json, flat heights, no Data/raw) and count
A-7 + T-1, D-42 / D-43 and A-8 per tile. Usage: uv run --project tools/worldgen python tools/worldgen/qa/built_up_signs_count.py <repo> [tile ...]"""
import json, sys, os
import numpy as np
REPO = sys.argv[1]
sys.path.insert(0, os.path.join(REPO, "tools/worldgen"))
from roads import pipeline as PL, network as Nw, junctions as J
from streetscape import furniture as FU, built_up as BU, signs_route as SR
from pathlib import Path
import shapely
from shapely.geometry import LineString, Polygon

tiles = sys.argv[2:] or sorted(p.name for p in Path(REPO, "Data/Regions").iterdir() if (p / "region.yaml").exists())
tot = {}
out = {}
for rid in tiles:
    rdir = Path(REPO, "Data/Regions", rid)
    try:
        region = PL.load_region(rid)
        origin = (region["origin"]["x"], region["origin"]["y"])
        ctx = json.loads((rdir / "generated/osm_context.json").read_text(encoding="utf-8"))
        net, graph, overrides, _ = PL.build_network(rid)
        pts, foot = PL.ctx_local(ctx, origin)
        walk = [LineString(np.array(f["geometry"]) - np.array(origin)) for f in ctx["footways"] if f["highway"] != "path"]
        src = json.loads((rdir / "generated/streetscape_sources.json").read_text(encoding="utf-8"))
        walk += [LineString(np.array(f["geometry"]["coordinates"]) - np.array(origin))
                 for f in src["bdot10k"]["OT_SKRP_L"] if f["props"].get("materialnawierzchni") not in (None, "grunt naturalny")]
        net.cycle_items = []
        Nw.assign_sides(net, foot, built_up=True, walkways=walk, yards=None)
        juncs = J.build_junctions(net, pts)
        Nw.assign_sides(net, foot, built_up=True, walkways=walk, yards=None, trims=True)
        for c in net.chains:
            k = len(c.line.s)
            if getattr(c, "z", None) is None or len(c.z) != k:
                c.z = np.zeros(k)
            if getattr(c, "e", None) is None or len(c.e) != k:
                c.e = np.zeros(k)
        pl = FU.Placer(lambda e, n: np.zeros(np.shape(e)))
        rep, codes = {}, set()
        attrs = {e["id"]: e["attrs"] for e in graph["edges"]}
        boards = {}
        FU.signals(pl, net, juncs, rep)
        FU.junction_signs(pl, net, juncs, pts, rep, codes)
        FU.speed_signs(pl, net, rep, codes)
        FU.crossing_signs(pl, net, pts, rep, codes)
        FU.direction_boards(pl, net, attrs, rep, boards)
        SR.osm_signs(pl, net, src, np.array(origin), juncs, rep, codes)
        SR.roundabout_signs(pl, net, juncs, attrs, rep, codes, boards, src=src, origin=np.array(origin))
        b = rep["built_up"]
        a8 = [x for x in (rep.get("roundabout_signs") or rep.get("roundabouts") or {}).get("a8", [])] if isinstance(rep.get("roundabout_signs") or rep.get("roundabouts"), dict) else []
        a8p = sum(1 for x in a8 if x.get("placed"))
        nminor = sum(len(getattr(j, "minor_signs", []) or []) for j in juncs)
        out[rid] = {"minor": nminor, "advance": b["advance"], "dropped": len(b["advance_dropped"]),
                    "placed": b["placed"], "boundaries": len(b["boundaries"]), "osm_nodes": b["osm_boundary_nodes"],
                    "a8": a8, "osm_placed": rep.get("osm_signs", {}).get("placed")}
        print(f"{rid:24s} minor={nminor:3d} advance={len(b['advance']):2d} dropped={len(b['advance_dropped']):2d} "
              f"a8={a8p}/{len(a8)} placed={b['placed']} boundaries={len(b['boundaries'])} osm_nodes={b['osm_boundary_nodes']}", flush=True)
    except Exception as ex:
        import traceback; traceback.print_exc()
        print(rid, "ERROR", repr(ex))
json.dump(out, open(os.environ.get("A7_OUT", "/dev/null"), "w"), indent=1, default=str)
