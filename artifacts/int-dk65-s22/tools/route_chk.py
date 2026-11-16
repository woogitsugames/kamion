import sys, json
from pathlib import Path
import numpy as np
WT = Path(r"C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\int-dk65-s22")
sys.path.insert(0, str(WT / "tools" / "worldgen"))
from roads import pipeline as PL, junctions as J, network as Nw
from shapely.geometry import Point
net, graph, ov, st = PL.build_network("knyszyn")
Nw.assign_sides(net, [], built_up=True, walkways=[], yards=None)
juncs = J.build_junctions(net, [])
j = next(j for j in juncs if j.compact is not None); sp = j.compact
RP = np.array(json.loads((WT/"Data/Regions/knyszyn/route_start.json").read_text(encoding="utf-8"))["points_en"])
near = RP[np.hypot(*(RP - sp.center).T) < 40]
print("route pts near", len(near), "outside outline", sum(not sp.outline.buffer(0.01).contains(Point(p)) for p in near))
print("min dist to outline edge (inside pts)", round(min(sp.outline.exterior.distance(Point(p)) for p in near if sp.outline.contains(Point(p))), 2))
for sid, pg in sp.splitters:
    print(sid[-12:], "area", round(pg.area, 1), "min dist route", round(min(pg.distance(Point(p)) for p in near), 2))
print("route min r", round(float(np.hypot(*(near - sp.center).T).min()), 2), "apron lip r", round(sp.r_in, 2))
