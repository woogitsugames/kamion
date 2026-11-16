import sys, json
from pathlib import Path
import numpy as np
WT = Path(r"C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\int-dk65-s22")
sys.path.insert(0, str(WT / "tools" / "worldgen"))
from roads import pipeline as PL, junctions as J, network as Nw
from PIL import Image, ImageDraw
import shapely
from shapely.geometry import Polygon, Point, LineString
out = sys.argv[1]; Rov = float(sys.argv[2]) if len(sys.argv) > 2 else None
net, graph, ov, st = PL.build_network("knyszyn")
Nw.assign_sides(net, [], built_up=True, walkways=[], yards=None)
ring = [c for c in net.chains if c.roundabout and "1426801304" in c.id]
pts = np.vstack([c.line.p for c in ring])
# circle fit (Kasa)
A = np.column_stack([2*pts, np.ones(len(pts))]); b = (pts**2).sum(1)
sol = np.linalg.lstsq(A, b, rcond=None)[0]; C = sol[:2]; R = float(np.sqrt(sol[2] + C @ C))
rr = np.hypot(*(pts - C).T)
print("centre", np.round(C, 2), "R", round(R, 2), "r range", round(rr.min(), 2), round(rr.max(), 2))
ring_nodes = {c.node_a for c in ring} | {c.node_b for c in ring}
ow = [c for c in net.chains if not c.roundabout and (c.node_a in ring_nodes or c.node_b in ring_nodes)]
split = {(c.node_b if c.node_a in ring_nodes else c.node_a) for c in ow}
nodes = ring_nodes | split
ext = [c for c in net.chains if c not in ring and c not in ow and (c.node_a in split or c.node_b in split)]
arms = []
for c in ext:
    if c.node_a in split: arms.append(J.Arm(c, "a", c.node_a))
    if c.node_b in split: arms.append(J.Arm(c, "b", c.node_b))
arms.sort(key=lambda a: (J._ang(a.gutter(min(6.0, a.L*0.5), 0) - C), a.key))
j = J.Junction(id="j:test", nodes=sorted(nodes), arms=arms, center=C)
mt = {i: a.L - 0.5 for i, a in enumerate(arms)}
j.corners, j.trims = J.compute_corners(net, j, mt, Rov)
print("arms", [(a.chain.id, a.end, round(a.L, 1), round(float(a.chain.hw_at(np.array([a.s(0.0)]))[0]), 2), round(float(np.hypot(*(net.nodes[a.node]['xy'] - C))), 1)) for a in arms])
print("trims", {k: round(float(v), 2) for k, v in (j.trims.items() if isinstance(j.trims, dict) else enumerate(j.trims))})
print("corners", [(c.kind, round(c.R, 1)) for c in j.corners])
j.boundary = J.patch_boundary(j)
poly = Polygon([p for p, _ in j.boundary])
print("valid", poly.is_valid, "area", round(poly.area, 1))
ang = np.linspace(0, 2*np.pi, 721)
dist = []
for t in ang:
    ray = LineString([C, C + 80*np.array([np.cos(t), np.sin(t)])])
    x = ray.intersection(poly.exterior)
    dist.append(min((Point(C).distance(g) for g in getattr(x, "geoms", [x])), default=np.nan) if not x.is_empty else np.nan)
dist = np.array(dist)
print("min centre->outline", round(np.nanmin(dist), 2), "at deg", round(float(np.degrees(ang[np.nanargmin(dist)])), 0), "need >=", 6.3 + 5.0)
# one-way lanes inside?
worst = 0
for c in ow:
    s = np.linspace(0, c.length, 40); hw = c.hw_at(s)
    for sg in (+1, -1):
        P = c.line.offset_point(s, sg*hw)
        d = np.array([0.0 if poly.contains(Point(p)) else poly.exterior.distance(Point(p)) for p in P])
        worst = max(worst, d.max())
        if d.max() > 0.05: print(" lane edge outside", c.id, sg, round(d.max(), 2))
print("worst lane edge outside m", round(worst, 2))
rs = json.loads((WT/"Data/Regions/knyszyn/route_start.json").read_text(encoding="utf-8"))
RP = np.array(rs["points_en"])
S_ = 14.0; W = 1200
def px(p): return (W/2 + (p[0]-C[0])*S_, W/2 - (p[1]-C[1])*S_)
im = Image.new("RGB", (W, W), (30, 30, 30)); d = ImageDraw.Draw(im)
bb = [px(p) for p, _ in j.boundary]; d.line(bb + bb[:1], fill=(80, 255, 80), width=2)
for c in ow + ring:
    s = np.linspace(0, c.length, 40); hw = c.hw_at(s)
    for sg in (+1, -1):
        d.line([px(p) for p in c.line.offset_point(s, sg*hw)], fill=(110, 110, 255) if c in ow else (90, 90, 90), width=1)
for r, col in ((R + 2.5, (255, 255, 255)), (R - 2.5, (255, 200, 80)), (R - 2.5 - 3.2, (255, 80, 80))):
    d.line([px(C + r*np.array([np.cos(t), np.sin(t)])) for t in ang], fill=col, width=1)
d.line([px(p) for p in RP if np.hypot(*(p - C)) < 45], fill=(255, 0, 255), width=2)
im.save(out)
