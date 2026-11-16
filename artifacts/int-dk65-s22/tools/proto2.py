import sys, json
from pathlib import Path
import numpy as np
WT = Path(r"C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\int-dk65-s22")
sys.path.insert(0, str(WT / "tools" / "worldgen"))
from roads import pipeline as PL, junctions as J, network as Nw
from PIL import Image, ImageDraw
import shapely
from shapely.geometry import Polygon, Point, LineString
out = sys.argv[1]; RC = float(sys.argv[2])
net, graph, ov, st = PL.build_network("knyszyn")
ring = [c for c in net.chains if c.roundabout and "1426801304" in c.id]
pts = np.vstack([c.line.p for c in ring])
A = np.column_stack([2*pts, np.ones(len(pts))]); b = (pts**2).sum(1)
sol = np.linalg.lstsq(A, b, rcond=None)[0]; C = sol[:2]; R = float(np.sqrt(sol[2] + C @ C))
W_ASPH, W_APR = 5.0, 3.2
Ri = R - W_ASPH/2; Ro = R + W_ASPH/2
ring_nodes = {c.node_a for c in ring} | {c.node_b for c in ring}
ow = [c for c in net.chains if not c.roundabout and (c.node_a in ring_nodes or c.node_b in ring_nodes)]
split = {(c.node_b if c.node_a in ring_nodes else c.node_a) for c in ow}
ext = [c for c in net.chains if c not in ring and c not in ow and (c.node_a in split or c.node_b in split)]
disc = Point(C).buffer(Ro, 64)
ribs = []
for c in ow:
    s = np.linspace(0, c.length, 60); hw = c.hw_at(s)
    L = c.line.offset_point(s, hw); Rr = c.line.offset_point(s, -hw)
    ribs.append(Polygon(np.vstack([L, Rr[::-1]])).buffer(0))
stubs = []
for c in ext:
    end_a = c.node_a in split
    s = np.linspace(0, min(6.0, c.length*0.5), 8) if end_a else np.linspace(c.length - min(6.0, c.length*0.5), c.length, 8)
    hw = c.hw_at(s)
    stubs.append(Polygon(np.vstack([c.line.offset_point(s, hw), c.line.offset_point(s, -hw)[::-1]])).buffer(0))
raw = shapely.union_all([disc] + ribs + stubs)
closed = raw.buffer(RC, 32).buffer(-RC, 32)
paved_extra = closed.difference(raw)
parts = [g for g in getattr(paved_extra, "geoms", [paved_extra]) if g.area > 0.5]
print("R", round(R,2), "Ri", round(Ri,2), "Ro", round(Ro,2), "raw area", round(raw.area,1), "closed", round(closed.area,1), "holes in raw", len(raw.interiors) if raw.geom_type=="Polygon" else "multi")
for g in parts:
    c0 = np.array(g.centroid.coords[0]); 
    # width estimate: 2*area/perimeter-ish via negative buffer
    w = 0.0
    for t in np.arange(0.25, 6, 0.25):
        if g.buffer(-t).is_empty: break
        w = 2*t
    print(" fill part area", round(g.area,1), "dist centre", round(float(np.hypot(*(c0-C))),1), "ang", round(float(np.degrees(np.arctan2(*(c0-C)[::-1]))),0), "max width ~", w)
rs = json.loads((WT/"Data/Regions/knyszyn/route_start.json").read_text(encoding="utf-8"))
RP = np.array(rs["points_en"]); near = RP[np.hypot(*(RP - C).T) < 30]
print("route pts outside closed:", sum(not closed.contains(Point(p)) for p in near), "min dist route->outline", round(min(closed.exterior.distance(Point(p)) for p in near), 2), "route min r", round(float(np.hypot(*(near - C).T).min()), 2))
S_ = 14.0; Wd = 1200
def px(p): return (Wd/2 + (p[0]-C[0])*S_, Wd/2 - (p[1]-C[1])*S_)
im = Image.new("RGB", (Wd, Wd), (60, 90, 50)); d = ImageDraw.Draw(im)
d.polygon([px(p) for p in closed.exterior.coords], fill=(70, 70, 74))
for g in parts:
    d.polygon([px(p) for p in g.exterior.coords], fill=(110, 110, 150))
ang = np.linspace(0, 2*np.pi, 361)
d.polygon([px(C + Ri*np.array([np.cos(t), np.sin(t)])) for t in ang], fill=(205, 204, 200))
d.polygon([px(C + (Ri-W_APR)*np.array([np.cos(t), np.sin(t)])) for t in ang], fill=(190, 170, 130))
d.line([px(C + Ro*np.array([np.cos(t), np.sin(t)])) for t in ang], fill=(255, 255, 255), width=1)
d.line([px(p) for p in near], fill=(255, 0, 255), width=2)
for c in ow:
    d.line([px(p) for p in c.line.p], fill=(40, 40, 40), width=1)
im.save(out)
