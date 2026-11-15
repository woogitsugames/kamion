"""ADR 0202: cross-sections of the game terrain (heightmap_2049.r16 = GUGiK NMT) across runway 09R/27L."""
import json, numpy as np
t = json.load(open("Data/Regions/bialystok-dojlidy/terrain.json"))
H = np.fromfile(t["encoding"]["file"], "<u2").reshape(2049, 2049) * t["encoding"]["scale_m_per_unit"] + t["encoding"]["offset_m"]
x0, y0, x1, y1 = t["bbox"]
ox, oy = (x0 + x1) / 2, (y0 + y1) / 2
A = np.array([[-1024.0, -217.0], [-105.0, -192.75]]); L = np.hypot(*(A[1] - A[0])); tt = (A[1] - A[0]) / L; nn = np.array([-tt[1], tt[0]])
def z(e, n):
    i = np.clip(np.round(e + ox - x0).astype(int), 0, 2048); j = np.clip(np.round(y1 - (n + oy)).astype(int), 0, 2048)
    return H[j, i]
lat = np.arange(-120, 121, 5.0)
print("origin", ox, oy)
print("lat  " + " ".join(f"{int(v):5d}" for v in lat))
out = {}
for s in range(20, 920, 60):
    P = A[0] + tt * s + nn[None, :] * lat[:, None]
    zz = z(P[:, 0], P[:, 1]); zc = zz[len(lat) // 2]
    out[s] = [round(float(v - zc), 2) for v in zz]
    print(f"s{s:4d} " + " ".join(f"{v - zc:5.1f}" for v in zz), f" zc={zc:.2f}")
json.dump({"lat_m": lat.tolist(), "dz_vs_axis_m": out}, open("artifacts/dojfix-0202/berms.json", "w"))
# ridge search: lateral profile +-260 m every 1 m; prominence of local maxima above both flanks (30 m window)
lat = np.arange(-260, 261, 1.0)
worst = []
for s in range(10, 915, 10):
    P = A[0] + tt * s + nn[None, :] * lat[:, None]
    zz = z(P[:, 0], P[:, 1])
    for k in range(40, len(lat) - 40):
        if abs(lat[k]) < 20: continue
        prom = zz[k] - max(zz[k - 40:k].min(), zz[k + 1:k + 41].min())
        if zz[k] == zz[k - 6:k + 7].max() and prom > 0.8:
            worst.append((round(float(prom), 2), s, int(lat[k]), round(float(zz[k]), 2)))
worst.sort(reverse=True)
print("ridges with prominence > 0.8 m (prom, s, lat, z):", len(worst)); print(worst[:25])
import collections
print(collections.Counter((w[2] // 10 * 10) for w in worst).most_common(12))
