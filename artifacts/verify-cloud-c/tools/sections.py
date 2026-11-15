"""Print generator cross-sections of given OSM ways in a region (run with cwd = repo root to test)."""
import sys, json
sys.path.insert(0, "tools/worldgen")
from roads import pipeline
reg, ways = sys.argv[1], {int(x) for x in sys.argv[2].split(",")}
r = pipeline.build_network(reg)
net = r[0] if isinstance(r, tuple) else r
g = json.load(open(f"Data/Regions/{reg}/roads.graph.json", encoding="utf8"))
ed = {e["id"]: e for e in g["edges"]}
secs = getattr(net, "sections", None) or getattr(net, "sec", None)
for eid, s in (secs.items() if isinstance(secs, dict) else [(x.edge_id, x) for x in secs]):
    e = ed.get(eid)
    if e and e["osm_way"] in ways:
        geom = e.get("geometry") or e.get("line") or e.get("pts")
        print(reg, e["osm_way"], eid, "cls", s.cls, "lanes", s.lanes, "lane_w", s.lane_w, "edge_strip", s.edge_strip, "width", s.width,
              "edge_lines", s.edge_lines, "mat", s.surface_mat, "construction", getattr(s, "construction", None),
              "ends", [tuple(round(v, 1) for v in geom[0][:2]), tuple(round(v, 1) for v in geom[-1][:2])] if geom else None)
