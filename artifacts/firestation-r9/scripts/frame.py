"""BDOT rings and LoD2 roof planes of JRG2 in the building frame (u along the SW facade to SE, v to NE)."""
import json, math
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[3]
A = np.array([-262.92, -142.67])
B = np.array([-224.75, -172.17])
u = (B - A) / np.linalg.norm(B - A)
v = np.array([-u[1], u[0]])
print("u", u.round(4), "v", v.round(4), "yaw_deg(u from E)", round(math.degrees(math.atan2(u[1], u[0])), 2))


def uv(p):
    d = np.asarray(p[:2]) - A
    return [round(float(d @ u), 2), round(float(d @ v), 2)]


main = [[-262.92, -142.67], [-248.56, -154.39], [-248.18, -153.91], [-240.74, -159.51], [-239.85, -158.33], [-237.42, -160.1], [-233.51, -165.5], [-224.75, -172.17], [-209.53, -153.03], [-220.88, -143.87], [-219.95, -142.68], [-231.72, -133.16], [-229.42, -130.09], [-235.82, -125.08], [-243.99, -118.69], [-262.92, -142.67]]
out = [[-199.44, -156.78], [-185.29, -169.4], [-176.69, -159.75], [-190.83, -147.12], [-199.44, -156.78]]
print("main", [uv(p) for p in main])
print("outb", [uv(p) for p in out])
d = json.load(open(REPO / "art-source/world/landmarks/fire_station_jrg2/lod2_roofs.json"))
for b in d["buildings"]:
    print(b["id"], "h", b["height"], "zmin", b["zmin"])
    for r in b["roofs"]:
        print("  ", [uv(p) + [p[2]] for p in r[:-1]])
r = json.load(open(REPO / "Data/Regions/bialystok-industrial-c/route_start.json"))
P = np.array(r["points_en"])
dd = (P - A) @ v
i = int(np.argmin(np.abs((P - A) @ u - 24)))
print("route at u=24: v=", round(float(dd[i]), 1))
