"""fields2-s24: top-down numpy port of KamionFieldMosaic.hlsl r2 (albedo only, flat light) - a logic check of the
wobbling edges, baulks, headlands with turning arcs, field tracks, rows and streaks before the Unity renders.
python preview_r2.py out.png [E0 N0 width height res_m] (EPSG:2180; default: 600 x 400 m at 0.25 m near Knyszyn)."""
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, "tools/worldgen")
from streetscape import vegetation as VG  # noqa: E402

u01, h32, h32s = VG._u01, VG._h32, VG._h32s
args = sys.argv[2:]
E0, N0 = (float(args[0]), float(args[1])) if len(args) >= 2 else (759700.0, 613300.0)
WM, HM = (float(args[2]), float(args[3])) if len(args) >= 4 else (600.0, 400.0)
RES = float(args[4]) if len(args) >= 5 else 0.25
ARABLE = True
W, H = int(WM / RES), int(HM / RES)
x = E0 + (np.arange(W)[None, :] + 0.5) * RES + np.zeros((H, 1))
y = N0 - (np.arange(H)[:, None] + 0.5) * RES + np.zeros((1, W))
fp = RES            # footprint = one texel

# ---- layout with the extras the shader derives (copy of VG.field_layout)
DM, BM, HO, ST = VG.FIELD_DISTRICT_M, VG.FIELD_BLOCK_M, VG.FIELD_BLOCK_HASH_OFS, VG.FIELD_STRETCH
di_, dj_, sdx, sdy, sdx2, sdy2, e1, e2 = VG._nearest2(
    x, y, DM, lambda i, j: ((i + 0.15 + 0.7 * u01(h32(i, j, 971))) * DM, (j + 0.15 + 0.7 * u01(h32(i, j, 973))) * DM))
dl = np.maximum(np.hypot(sdx2 - sdx, sdy2 - sdy), 1e-3)
district_edge = (e2 - e1) / (2.0 * dl)
dsalt = h32(di_, dj_, 977)
thD = np.pi * u01(h32(di_, dj_, 975))
ax, ay = np.cos(thD), np.sin(thD)
nx, ny = -ay, ax
r0x, r0y = x - sdx, y - sdy
qx, qy = (r0x * ax + r0y * ay) / ST, r0x * nx + r0y * ny
# second-nearest block index is needed for the border id: rerun the search keeping it
cx, cy = np.floor(qx / BM), np.floor(qy / BM)
d1 = np.full(x.shape, np.inf); d2 = np.full(x.shape, np.inf)
s1x = np.zeros(x.shape); s1y = np.zeros(x.shape); s2x = np.zeros(x.shape); s2y = np.zeros(x.shape)
b1i = np.zeros(x.shape); b1j = np.zeros(x.shape); b2i = np.zeros(x.shape); b2j = np.zeros(x.shape)
for dj in (-1, 0, 1):
    for di in (-1, 0, 1):
        i, j = cx + di, cy + dj
        sx_ = (i + 0.15 + 0.7 * u01(h32s(i + HO, j + HO, np.uint32(911) ^ dsalt))) * BM
        sy_ = (j + 0.15 + 0.7 * u01(h32s(i + HO, j + HO, np.uint32(913) ^ dsalt))) * BM
        dd = (qx - sx_) ** 2 + (qy - sy_) ** 2
        m1 = dd < d1
        m2 = ~m1 & (dd < d2)
        d2 = np.where(m1, d1, np.where(m2, dd, d2))
        s2x = np.where(m1, s1x, np.where(m2, sx_, s2x)); s2y = np.where(m1, s1y, np.where(m2, sy_, s2y))
        b2i = np.where(m1, b1i, np.where(m2, i + HO, b2i)); b2j = np.where(m1, b1j, np.where(m2, j + HO, b2j))
        d1 = np.where(m1, dd, d1)
        s1x = np.where(m1, sx_, s1x); s1y = np.where(m1, sy_, s1y)
        b1i = np.where(m1, i + HO, b1i); b1j = np.where(m1, j + HO, b1j)
Ls = np.maximum(np.hypot(s2x - s1x, s2y - s1y), 1e-3)
nqx, nqy = (s2x - s1x) / Ls, (s2y - s1y) / Ls
gqx, gqy = nqx / ST, nqy
gql = np.maximum(np.hypot(gqx, gqy), 1e-4)
block_edge = (d2 - d1) / (2.0 * Ls) / gql
distr = district_edge < block_edge
dWx, dWy = (sdx2 - sdx) / dl, (sdy2 - sdy) / dl
gWx = np.where(distr, dWx, (ax * gqx + nx * gqy) / gql)
gWy = np.where(distr, dWy, (ay * gqx + ny * gqy) / gql)
crossK = np.clip((np.abs(gWx * ax + gWy * ay) - 0.30) / 0.25, 0, 1)
hB = (h32s(b1i, b1j, np.uint32(991) ^ dsalt).astype(np.uint64) + h32s(b2i, b2j, np.uint32(991) ^ dsalt).astype(np.uint64)).astype(np.uint32)
track_on = u01(h32(hB.astype(np.int32).astype(np.float64), np.zeros(x.shape), 993)) < 0.40
block_edge = np.minimum(block_edge, district_edge)
th = thD + 0.5 * np.pi + (u01(h32s(b1i, b1j, np.uint32(917) ^ dsalt)) - 0.5) * 0.2
w = 16.0 + 24.0 * u01(h32s(b1i, b1j, np.uint32(919) ^ dsalt))
sx = sdx + ax * (s1x * ST) + nx * s1y
sy = sdy + ay * (s1x * ST) + ny * s1y
rx, ry = x - sx, y - sy
n5, n17, n47, n1 = (VG._kf_noise(x, y, s, salt) for s, salt in ((5.0, 951), (17.0, 953), (47.0, 983), (1.7, 985)))
wob = (n47 - 0.5) * 2.6 + (n17 - 0.5) * 1.0 + (n5 - 0.5) * 0.2
t = (rx * np.cos(th) + ry * np.sin(th) + wob) / w
along = -rx * np.sin(th) + ry * np.cos(th)
k = np.floor(t)
across = (t - k) * w
bid = h32s(b1i, b1j, np.uint32(923) ^ dsalt)
i32 = lambda a: a.astype(np.int32).astype(np.float64)     # (int)uint of the shader
zero = np.zeros(x.shape)
fid = h32(i32(bid), k, 929)
own = u01(h32(i32(fid), zero, 931)) < 0.55
r = np.where(own, u01(h32(i32(fid), zero, 937)), u01(h32(i32(bid), zero, 939)))
ca = np.array([c for _, c in VG.FIELD_USES_ARABLE]); cg = np.array([c for _, c in VG.FIELD_USES_GRASS])
u = np.minimum(np.searchsorted(ca, r, side="right"), len(ca) - 1) if ARABLE else len(ca) + np.minimum(np.searchsorted(cg, r, side="right"), len(cg) - 1)
dev = u01(h32(i32(fid), zero, 943)) - 0.5

ALB = np.array([(0.350, 0.240, 0.085), (0.315, 0.262, 0.120), (0.300, 0.212, 0.095), (0.265, 0.205, 0.110),
                (0.165, 0.145, 0.095), (0.036, 0.078, 0.020), (0.050, 0.096, 0.026), (0.150, 0.112, 0.072),
                (0.085, 0.150, 0.034), (0.068, 0.132, 0.030), (0.120, 0.128, 0.050), (0.068, 0.148, 0.030),
                (0.054, 0.098, 0.025), (0.150, 0.172, 0.060), (0.225, 0.195, 0.085), (0.128, 0.124, 0.060)])
col = ALB[u].copy()
ploughed = (u == 7) & (u01(h32(i32(fid), zero, 995)) < 0.5)
col[ploughed] = (0.105, 0.079, 0.054)
col *= (1.0 + dev * 0.12)[..., None]


def band(xx, p, bw, f):
    q = np.mod(xx / p, 1.0) * p
    d = np.minimum(q, p - q)
    return np.clip((0.5 * bw - d) / f + 0.5, 0, 1) * np.clip(p / (3.0 * f) - 0.5, 0, 1)


def nsf(a, l, sa, sl, salt):
    px, py = a / sa, l / sl
    gx, gy = np.floor(px), np.floor(py)
    fx, fy = px - gx, py - gy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    gx, gy = gx + HO * 4, gy + HO * 4
    a0, b0 = u01(h32(gx, gy, salt)), u01(h32(gx + 1, gy, salt))
    c0, d0 = u01(h32(gx, gy + 1, salt)), u01(h32(gx + 1, gy + 1, salt))
    return (a0 * (1 - fx) + b0 * fx) * (1 - fy) + (c0 * (1 - fx) + d0 * fx) * fy


def lerp(a, b, t_):
    t_ = np.asarray(t_)[..., None] if np.ndim(t_) == 2 else t_
    return a + (np.asarray(b) - a) * t_


Hd = 9.0 * (0.65 + 0.7 * u01(h32s(b1i, b1j, np.uint32(949) ^ dsalt))) + (n17 - 0.5) * 2.0
hrow = ARABLE & (crossK > 0.5) & (block_edge < Hd)
rc = np.where(hrow, block_edge, across)
rl = np.where(hrow, t * w, along)
fpr = fp
s2 = nsf(rc, rl, 2.6, 60.0, 987) - 0.5
s1 = (nsf(rc, rl, 0.55, 18.0, 989) - 0.5) * np.clip(0.55 / (1.5 * fpr) - 0.5, 0, 1)
stA1 = np.zeros(x.shape); stA2 = np.zeros(x.shape); rowP = np.zeros(x.shape); rowD = np.zeros(x.shape)
SOIL = np.array((0.150, 0.112, 0.072))
m = (u <= 1) | (u == 8)
qq = np.mod((rc - 9.0) / 18.0, 1.0) * 18.0
dc = np.minimum(qq, 18.0 - qq)
track = np.clip((0.225 - np.abs(dc - 0.9)) / fpr + 0.5, 0, 1) * np.clip(0.9 / fpr - 0.5, 0, 1)
col = np.where(m[..., None], lerp(col, SOIL, track * 0.75) * (1.0 - 0.12 * np.clip((n17 - 0.62) / 0.18, 0, 1))[..., None], col)
stA1[m], stA2[m] = 0.06, 0.16
m = (u >= 2) & (u <= 4)
wp = np.where(u == 4, 6.0, 7.5)
row = band(rc + 1.7, wp, np.where(u == 2, 1.5, 2.6), fpr)
straw = np.where((u == 4)[..., None], (0.210, 0.185, 0.120), (0.420, 0.315, 0.150))
c2 = lerp(col, straw, row * np.where(u == 2, 0.85, 0.35))
c2 = c2 * (1.0 - 0.14 * (band(rc + 0.45, wp, 0.55, fpr) + band(rc - 2.2, wp, 0.55, fpr)))[..., None]
c2 = lerp(c2, (0.085, 0.130, 0.040), 0.30 * np.clip((n5 * 0.6 + n17 * 0.4 - 0.55) / 0.3, 0, 1))
col = np.where(m[..., None], c2, col)
rowP[m] = np.where(u == 4, 0.33, 0.25)[m]; rowD[m] = 0.26; stA1[m], stA2[m] = 0.26, 0.20
m = (u == 5) | (u == 6)
c2 = lerp(col, (0.120, 0.095, 0.062), band(rc + 0.375, 0.75, 0.30, fpr) * 0.45) * (1.0 + 0.10 * (n5 - 0.5))[..., None]
col = np.where(m[..., None], c2, col)
stA1[m], stA2[m] = 0.10, 0.12
m = ploughed
c2 = col * (1.0 + 0.10 * (band(rc, 1.6, 0.8, fpr) - 0.5))[..., None]
c2 = lerp(c2, (0.175, 0.140, 0.098), 0.22 * np.clip((n5 - 0.45) / 0.4, 0, 1))
col = np.where(m[..., None], c2, col)
rowP[m] = 0.40; rowD[m] = 0.42; stA1[m], stA2[m] = 0.30, 0.22
m = (u == 7) & ~ploughed
c2 = col * (1.0 + 0.16 * (band(rc, 3.0, 1.5, fpr) - 0.5))[..., None]
c2 = lerp(c2, (0.260, 0.220, 0.140), 0.18 * np.clip((n5 - 0.5) / 0.4, 0, 1))
col = np.where(m[..., None], c2, col)
rowP[m] = 0.22; rowD[m] = 0.20; stA1[m], stA2[m] = 0.26, 0.20
m = (u == 10) | (u == 12) | (u == 15)
pch = np.clip((n5 * 0.55 + n17 * 0.45 - 0.35) / 0.4, 0, 1)
other = np.where((u == 10)[..., None], (0.170, 0.160, 0.060), np.where((u == 12)[..., None], (0.090, 0.140, 0.035), (0.150, 0.140, 0.080)))
col = np.where(m[..., None], lerp(col, other, pch * 0.6), col)
m = (u == 13) | (u == 14)
row = band(rc + 2.0, 6.0, 1.3, fpr)
col = np.where(m[..., None], lerp(col, np.where((u == 13)[..., None], (0.170, 0.185, 0.070), (0.250, 0.225, 0.105)), row * 0.8), col)
stA1[m], stA2[m] = 0.12, 0.14
m = (u == 9) | (u == 11)
col = np.where(m[..., None], col * (1.0 + 0.07 * (band(rc, 5.6, 2.8, fpr) - 0.5))[..., None], col)
stA1[m], stA2[m] = 0.06, 0.10
col *= (1.0 + stA1 * s1 + stA2 * s2)[..., None]
fr = np.clip(np.where(rowP > 0, rowP, 1.0) / (3.0 * fpr) - 0.5, 0, 1)
cs = np.cos(np.mod(rc / np.where(rowP > 0, rowP, 1.0), 1.0) * 2 * np.pi)
col *= (1.0 - np.where(rowP > 0, rowD, 0.0) * (0.5 + (0.5 - 0.5 * cs - 0.5) * fr))[..., None]

hm_ = ARABLE & (crossK > 0.5)
head = np.clip((Hd - block_edge) / fp + 0.5, 0, 1) * np.clip(block_edge / max(fp, 0.5), 0, 1)
hc = np.where((u <= 4)[..., None], col * np.array((0.86, 0.90, 0.98)), lerp(col, (0.11, 0.095, 0.065), 0.25))
c2 = lerp(col, hc, head * 0.8)
P = np.where((u <= 1) | (u == 8), 9.0, np.where(u <= 4, 7.5, 6.0))
ac = np.floor(across / P)
am = (across / P - ac) * P - 0.5 * P
ua = u01(h32(i32(fid), ac, 997))
dr = np.hypot(am, block_edge - (Hd - 0.6))
ring = np.abs(np.abs(dr - (0.30 + 0.12 * ua) * P) - 0.9)
arc = np.clip((0.22 - ring) / fp + 0.5, 0, 1) * np.clip(0.9 / fp - 0.5, 0, 1) * ((block_edge < Hd - 0.6) & (ua < 0.7))
arc = arc * (0.35 + 0.65 * n5)
c2 = lerp(c2, lerp(c2 * 0.72, SOIL, 0.40), arc * 0.6)
col = np.where(hm_[..., None], c2, col)

upper = across >= 0.5 * w
kE = np.where(upper, k + 1.0, k)
fidN = h32(i32(bid), np.where(upper, k + 1.0, k - 1.0), 929)
has = own | (u01(h32(i32(fidN), zero, 931)) < 0.55)
bw = 1.0 + 1.6 * u01(h32(i32(bid), kE, 947))
e = np.minimum(across, w - across)
hw = np.maximum(0.5 * bw * (0.55 + 0.9 * n5) + (n1 - 0.5) * 0.35, 0.12)
baulk = np.where(has, np.clip((hw - e) / fp + 0.5, 0, 1) * np.clip(2.0 * hw / fp, 0, 1), 0.0)
thin = np.where(has, np.clip(1.0 - (e - hw) / (0.6 + 2.2 * n17), 0, 1), 0.0)
hb = np.where(track_on, 1.9, 1.2) + (n17 - 0.5) * 1.2 + (n5 - 0.5) * 0.5 + (n1 - 0.5) * 0.3
bblock = np.clip((hb - block_edge) / fp + 0.5, 0, 1) * np.clip(2.0 * hb / fp, 0, 1)
thin = np.maximum(thin, np.clip(1.0 - (block_edge - hb) / (0.6 + 2.2 * n17), 0, 1))
baulk = np.maximum(baulk, bblock)
bc = lerp(np.array((0.072, 0.112, 0.036)) + np.zeros(col.shape), (0.150, 0.140, 0.072), np.clip((n5 - 0.45) / 0.35, 0, 1)) * (0.85 + 0.30 * n1)[..., None]
col = col + (lerp(col, bc, 0.55) - col) * (thin * thin * (0.25 + 0.70 * n5))[..., None]
col = col + (bc - col) * (baulk * 0.92)[..., None]
rut = np.clip((0.26 - np.abs(block_edge - 0.8)) / fp + 0.5, 0, 1) * np.clip(0.52 / fp, 0, 1) * track_on
col = col + (np.array((0.215, 0.180, 0.120)) * (0.85 + 0.30 * n5)[..., None] - col) * (rut * (0.55 + 0.40 * n17))[..., None]

c = col * 2.2
srgb = np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, 1) ** (1 / 2.4) - 0.055)
Image.fromarray((np.clip(srgb, 0, 1) * 255).astype(np.uint8)).save(sys.argv[1], quality=90)
print("saved", sys.argv[1], W, H, {VG.FIELD_USES[i]: round(float(np.mean(u == i)), 3) for i in range(16) if (u == i).any()},
      "headland share", round(float(np.mean(hrow)), 3), "track borders", round(float(np.mean(track_on)), 2))
