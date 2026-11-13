"""Software preview of the LOD1 walls of one building: every buildings_low quad of the <wall>__far_* materials drawn
in elevation with the far-row atlas (tint = wall colour). usage: elev.py <building id> out.png [bearing ...]"""
import sys
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from PIL import Image
from shapely.geometry import box
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen")); sys.path.insert(0, str(REPO / "tests" / "gis"))
from streetscape import buildings_mesh as BM, facade_atlas as FA, materials as MT
from test_buildings_0167 import _loaded
bid, out = sys.argv[1], sys.argv[2]
want = [float(x) for x in sys.argv[3:]] or [208.0, 118.0]
atlas = np.asarray(Image.open(REPO / "game/Assets/_Generated/World/bialystok-industrial-c/Textures/PBR/facade_far/T_facade_far_BaseColor.png").convert("RGB"), float) / 255.0
AH, AW = atlas.shape[:2]
class Buf:
    def __init__(self): self.parts = []
    def add(self, layer, mat, V, UV, T, **kw): self.parts.append((layer, mat, np.asarray(V, float), np.asarray(UV, float), np.asarray(T).reshape(-1, 3)))
b = _loaded({bid})[bid]
buf = Buf()
BM.build(buf, [b], SimpleNamespace(sample=lambda x, y: np.full(np.shape(x), 100.0)), None, None, box(-5000, -5000, -4990, -4990), {}, sign_out=[])
PX = 12
imgs = []
for brg in want:
    n = np.array([np.sin(np.radians(brg)), np.cos(np.radians(brg))]); d = np.array([-n[1], n[0]])   # left -> right seen from outside
    quads = []
    for layer, mat, V, UV, T in buf.parts:
        if layer != "buildings_low": continue
        for t in T:
            P = V[t]; nn = np.cross(P[1] - P[0], P[2] - P[0])
            if np.linalg.norm(nn) < 1e-9: continue
            nn /= np.linalg.norm(nn)
            if nn[:2] @ n < 0.95: continue
            quads.append((mat, P[:, :2] @ d, P[:, 2], UV[t] if len(UV) else None))
    us = np.concatenate([q[1] for q in quads]); zs = np.concatenate([q[2] for q in quads])
    u0, z0 = us.min(), zs.min(); W, H = int((us.max() - u0) * PX) + 1, int((zs.max() - z0) * PX) + 1
    img = np.zeros((H, W, 3))
    for mat, u, z, uv in quads:
        col = np.array(MT.M.get(mat, {}).get("color", [1, 0, 1])[:3]) ** (1 / 2.2)
        x = (u - u0) * PX; y = (z - z0) * PX
        xa, xb, ya, yb = int(np.floor(x.min())), int(np.ceil(x.max())), int(np.floor(y.min())), int(np.ceil(y.max()))
        gx, gy = np.meshgrid(np.arange(xa, xb) + 0.5, np.arange(ya, yb) + 0.5)
        A = np.array([[x[1] - x[0], x[2] - x[0]], [y[1] - y[0], y[2] - y[0]]])
        if abs(np.linalg.det(A)) < 1e-9: continue
        w = np.linalg.solve(A, np.stack([gx.ravel() - x[0], gy.ravel() - y[0]]))
        m = (w[0] >= -1e-6) & (w[1] >= -1e-6) & (w[0] + w[1] <= 1 + 1e-6)
        px, py = gx.ravel()[m].astype(int), gy.ravel()[m].astype(int)
        ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
        if "__far_" in mat and uv is not None:
            tuv = uv[0] + np.outer(w[0][m], uv[1] - uv[0]) + np.outer(w[1][m], uv[2] - uv[0])
            tx = (tuv[:, 0] / FA.FAR_M[0] * AW).astype(int) % AW
            ty = (AH - 1 - (tuv[:, 1] / FA.FAR_M[1] * AH).astype(int)) % AH
            c = np.clip(atlas[ty, tx] * 2.0 * col, 0, 1)
        else:
            c = np.tile(col, (m.sum(), 1))
        img[H - 1 - py[ok], px[ok]] = c[ok]
    imgs.append(img)
Hm = max(i.shape[0] for i in imgs)
canvas = np.concatenate([np.pad(i, ((Hm - i.shape[0], 0), (0, 20), (0, 0)), constant_values=0.3) for i in imgs], axis=1)
Image.fromarray((canvas * 255).astype(np.uint8)).save(out)
print(out, canvas.shape)
