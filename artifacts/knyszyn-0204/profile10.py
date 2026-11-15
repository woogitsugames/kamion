"""Cross profile of a road on the 0.1 m orthophoto: usage profile10.py x y bearing_deg [half=9] [avg=8]
x,y EPSG:2180 on the axis; bearing of the road (compass). Prints per 0.2 m offset: mean RGB, averaged along `avg` m."""
import sys, glob, math, rasterio, numpy as np
x, y, brg = float(sys.argv[1]), float(sys.argv[2]), math.radians(float(sys.argv[3]))
half = float(sys.argv[4]) if len(sys.argv) > 4 else 9.0; avg = float(sys.argv[5]) if len(sys.argv) > 5 else 8.0
t = np.array([math.sin(brg), math.cos(brg)]); n = np.array([t[1], -t[0]])   # n = right of travel
for f in sorted(glob.glob("Data/raw/gugik/gugik-orto-2025-rgb-0p10-knyszyn/*.tif")):
    ds = rasterio.open(f)
    if ds.bounds.left < x < ds.bounds.right and ds.bounds.bottom < y < ds.bounds.top: break
offs = np.arange(-half, half + 1e-6, 0.2); al = np.arange(-avg / 2, avg / 2, 0.2)
pts = [(x + o * n[0] + a * t[0], y + o * n[1] + a * t[1]) for o in offs for a in al]
v = np.array(list(ds.sample(pts, indexes=[1, 2, 3])), float).reshape(len(offs), len(al), 3)
m = np.median(v, axis=1)
line = ""
for o, c in zip(offs, m):
    g = c.mean(); green = c[1] - (c[0] + c[2]) / 2
    tag = "G" if green > 8 else ("W" if g > 175 else ("a" if g < 150 else "l"))
    line += tag
print("offs -%.0f..+%.0f m, 0.2 m steps (left -> right of bearing): G grass, a dark asphalt(<150), l light(150-175), W white(>175)" % (half, half))
print(line)
print(" ".join("%d" % c.mean() for c in m))
