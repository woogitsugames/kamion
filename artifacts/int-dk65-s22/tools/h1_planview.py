import sys, json, time
from pathlib import Path
import numpy as np
WT = Path(r"C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\int-dk65-s22")
sys.path.insert(0, str(WT / "tools" / "worldgen"))
from roads import pipeline as PL
from PIL import Image, ImageDraw
t0 = time.time()
w = PL.build("knyszyn")
print("build s", round(time.time() - t0, 1))
print("stale", w.net.overrides_stale)
print(json.dumps(w.stats.get("compact_roundabouts"), indent=1))
print("patch stats", {k: v for k, v in w.stats["patch"].items()})
j = next(j for j in w.junctions if j.compact is not None)
print(j.id, "arms", [(a.chain.id, a.end, round(float(j.trims[i]), 2)) for i, a in enumerate(j.arms)], "nb", len(j.boundary), "internal", len(j.internal), "notes", j.notes)
print("islands", [(i.id[-30:], i.built, i.note) for i in w.gore_plan.islands if "cr:" in i.id])
C = j.compact.center; S_ = 16.0; W = 1400
COL = {"road_asphalt": (70, 70, 74), "curb_concrete": (215, 215, 210), "sidewalk_paving": (150, 146, 138), "verge_grass": (88, 120, 70),
       "apron_paving_light": (200, 199, 195), "island_gravel": (190, 170, 130), "shoulder_gravel": (140, 130, 110)}
im = Image.new("RGB", (W, W), (50, 70, 45)); d = ImageDraw.Draw(im)
def px(p): return (W/2 + (p[0]-C[0])*S_, W/2 - (p[1]-C[1])*S_)
parts = [p for p in w.buf.parts if p.layer == "road"]
# painter: draw by mean z
tris = []
for p in parts:
    col = COL.get(p.mat, (255, 0, 255) if not p.mat.startswith("marking") else (255, 255, 255))
    V = p.V
    for t in p.T:
        q = V[t]
        if np.min(np.hypot(*(q[:, :2] - C).T)) < 46:
            n = np.cross(q[1] - q[0], q[2] - q[0])
            tris.append((q[:, 2].mean(), [px(x) for x in q], col if n[2] >= -1e-9 else (255, 0, 0)))
tris.sort(key=lambda x: x[0])
for _, pts, col in tris:
    d.polygon(pts, fill=col)
mats = {}
for p in parts:
    if np.min(np.hypot(*(p.V[:, :2] - C).T)) < 46: mats[p.mat] = mats.get(p.mat, 0) + len(p.T)
print(mats)
im.save(sys.argv[1])
