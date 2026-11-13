#!/usr/bin/env python3
"""Przypisanie kadrów do ulic wg reguły M51-FIX:
kadr należy do ulicy X tylko gdy geotag <= 25 m od osi X.
(Azymut kamery nie jest tu używany do przypisania; Commons nie ma GPSImgDirection.)

Wejście: data/roads.graph.json (osie OSM/BDOT10k, EPSG:2180).
Wyjście: street_assignment.json + wydruk tabeli.
"""
import csv, json, math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from tm2180 import forward

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOL_M = 25.0
FOCAL_STREETS = ["Skidelska", "Wileńska", "Łańcucka", "Kowieńska", "Lidzka",
                 "Wołkowyska", "Grodzieńska", "Racławicka", "Świsłocka", "Buska"]


def load_axes():
    g = json.load(open(os.path.join(HERE, "data", "roads.graph.json")))
    axes = {}  # name -> list of polylines [(x,y),...]
    for e in g["edges"]:
        a = e.get("attrs") or {}
        nm = a.get("name")
        if isinstance(nm, dict):
            nm = nm.get("v")
        if not nm:
            continue
        pts = [(p[0], p[1]) for p in e["geometry"]]
        axes.setdefault(nm, []).append(pts)
    return axes


def dist_to_polyline(px, py, pts):
    best = float("inf")
    bx = by = None
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        if L2 == 0:
            t = 0.0
        else:
            t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
        qx, qy = x1 + t * dx, y1 + t * dy
        d = math.hypot(px - qx, py - qy)
        if d < best:
            best, bx, by = d, qx, qy
    return best, bx, by


def main():
    axes = load_axes()
    rows = []
    with open(os.path.join(HERE, "manifest.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row = { (k or "").lstrip("﻿").strip('"'): (v or "").strip('"') for k, v in row.items() }
            rid = row["id"].strip('"')
            if not (rid.startswith("M51-1") and rid[4:7].isdigit() and 101 <= int(rid[4:7]) <= 118):
                continue
            lat, lon = float(row["lat"]), float(row["lon"])
            x, y = forward(lat, lon)
            cand = []
            for nm, polys in axes.items():
                best = float("inf"); bx = by = None
                for pts in polys:
                    d, qx, qy = dist_to_polyline(x, y, pts)
                    if d < best:
                        best, bx, by = d, qx, qy
                cand.append((best, nm, bx, by))
            cand.sort()
            within = [(d, nm) for d, nm, _, _ in cand if d <= TOL_M]
            rows.append({
                "id": rid,
                "lat": lat, "lon": lon,
                "x2180": round(x, 1), "y2180": round(y, 1),
                "street_manifest": row["ulica"],
                "within_25m": [{"street": nm, "dist_m": round(d, 1)} for d, nm in within],
                "nearest": [{"street": nm, "dist_m": round(d, 1)} for d, nm, _, _ in cand[:5]],
                "_q": [(nm, d, qx, qy) for d, nm, qx, qy in cand[:1]],
            })
        out = {r["id"]: {k: v for k, v in r.items() if not k.startswith("_")} for r in rows}
    json.dump(out, open(os.path.join(HERE, "street_assignment.json"), "w"), ensure_ascii=False, indent=1)
    for r in rows:
        az = None
        nm, d, qx, qy = r["_q"][0]
        az = (math.degrees(math.atan2(qx - r["x2180"], qy - r["y2180"])) + 360) % 360
        print(f"{r['id']}  manifest={r['street_manifest']:45s} "
              f"najbliżej: {nm} {d:6.1f} m (azymut do osi {az:3.0f}° — NIE azymut kamery)  "
              f"<=25 m: {', '.join(f'{c['street']} {c['dist_m']:.1f}m' for c in r['within_25m']) or 'BRAK'}")


if __name__ == "__main__":
    main()
