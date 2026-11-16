import sys, json
from pathlib import Path
import numpy as np
WT = Path(r"C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\int-dk65-s22")
sys.path.insert(0, str(WT / "tools" / "worldgen"))
from roads import pipeline as PL, junctions as J, network as Nw
from PIL import Image, ImageDraw
out = sys.argv[1]
net, graph, ov, st = PL.build_network("knyszyn")
Nw.assign_sides(net, [], built_up=True, walkways=[], yards=None)
juncs = J.build_junctions(net, [])
C = np.array([-987.0, -611.0]); S_ = 22.0; W = 1100
def px(p): return (W/2 + (p[0]-C[0])*S_, W/2 - (p[1]-C[1])*S_)
im = Image.new("RGB", (W, W), (30, 30, 30)); d = ImageDraw.Draw(im)
cols = [(255,80,80),(80,255,80),(80,160,255),(255,255,80),(255,80,255),(80,255,255),(255,160,60),(200,200,200)]
k = 0
for c in net.chains:
    p = c.line.p
    if np.min(np.hypot(*(p - C).T)) < 30:
        d.line([px(q) for q in p], fill=(255,255,255) if c.roundabout else (120,120,120), width=1)
        print("chain", c.id, "ring" if c.roundabout else "", round(c.length,2), "t_a", round(c.t_a,2), "t_b", round(c.t_b,2), "hw", np.round(c.hw_at(np.array([0.0, c.length])),2), "absorbed", c.meta.get("absorbed"))
for j in juncs:
    if np.hypot(*(j.center - C)) < 25:
        col = cols[k % 8]; k += 1
        b = [px(p) for p, _ in j.boundary]
        d.line(b + b[:1], fill=col, width=2)
        print(j.id, "nodes", j.nodes, "arms", [(a.chain.id[-24:], a.end, round(float(t),2)) for a, t in zip(j.arms, j.trims)], "corners", [(c.kind, round(c.R,1)) for c in j.corners], "nb", len(j.boundary))
im.save(out)
