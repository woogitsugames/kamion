"""Control cameras for the building typology work (ADR 0081): the blocks, halls, garages, houses and concrete
fences nearest to the start route, each seen from the route side at pedestrian eye height.

    uv run --project tools/worldgen python tools/worldgen/qa/buildings_cameras.py --region bialystok-industrial-c

Writes Data/Regions/<region>/buildings_r10_cameras.json (gate3-cameras schema, `seat: road` = re-seated by a ray cast
on the imported collision, kind photo_match = 1.7 m eye). Render:
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast -Gate3 Data/Regions/<region>/buildings_r10_cameras.json \
        -Cameras <ids> -OutputDir artifacts/buildings-r10/<round>/High-overcast
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml
from shapely.geometry import LineString, Point, shape
from shapely.strtree import STRtree

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from streetscape import buildings_mesh as BM  # noqa: E402

N_PER = {"block": 5, "hall": 4, "shed": 3, "house": 2, "office": 2}
# ADR 0091 (review s9 P2): the eye and the look-at point are written RAY_UP above the building ground, so the engine's
# re-seating ray (Gate3Cameras.ComputePose: from pos + 4 m down) starts above raised ground too - r10_hall_3 stood on a
# ramp 6 m above the hall's ground and was seated under the terrain. The offset cancels out in the re-seating.
RAY_UP = 10.0
# authored view angles (deg off the route side) for buildings whose default view is blocked by things the generator
# does not know (r10_hall_1: a parked trailer at the docks, since ADR 0071)
ANGLES = (25, -25, 50, -50, 0, 75, -75, 110, -110, 150, -150, 180)
ANGLES_FOR = {"bdot:7abd670e-1a55-4ccb-9da0-9a2ad052ff32": (50, 75, -75, 0, 110, -110),
              # ADR 0094 (review s9 P2-2): the default eye of r10_shed_2 stood behind the glazed noise barrier of the
              # route - the "green band over the ridge" and the "vertical seam of the slope" were the barrier's rail and
              # a panel joint seen through the glass, not the roof
              "bdot:2BE4B431-BD32-1BF0-E053-CC2BA8C0D140": (-50, 50, -75, 75, 110, -110)}
# ADR 0094 (review s9 P2-7): eye distance from the nearest wall (m) for buildings whose default distance (scaled with
# the footprint) leaves them a strip on the horizon - r10_hall_1 is a 5.7 m high, very long hall
DIST_FOR = {"bdot:7abd670e-1a55-4ccb-9da0-9a2ad052ff32": 22.0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    a = ap.parse_args()
    rdir = REPO / "Data" / "Regions" / a.region
    reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    fc = json.loads((rdir / "buildings.geojson").read_text(encoding="utf-8"))
    ovr = yaml.safe_load((rdir / "overrides.yaml").read_text(encoding="utf-8")) or {}
    ovr = ovr.get("overrides", ovr) if isinstance(ovr, dict) else ovr
    blds = BM.load(fc, (ox, oy), [o for o in ovr if isinstance(o, dict)])
    route = LineString(json.loads((rdir / "route_start.json").read_text(encoding="utf-8"))["points_en"])
    polys = [b["poly"] for b in blds]
    tree = STRtree(polys)
    cams = []

    def clear(p, q, skip):
        seg = LineString([p, q])
        return all(i == skip or not polys[i].intersects(seg) for i in tree.query(seg))

    def add(cid, pos, look, zg, zlook, note, kind="photo_match", fov=60.0):
        cams.append({"id": cid, "type": "persp", "kind": kind, "seat": "road",
                     "pos": [round(float(pos[0]), 2), round(float(pos[1]), 2), round(float(zg + 1.7 + RAY_UP), 2)],
                     "look_at": [round(float(look[0]), 2), round(float(look[1]), 2), round(float(zlook + RAY_UP), 2)],
                     "fov_deg": fov, "note": note})

    by = {}
    for i, b in enumerate(blds):
        if b["ovr"].get("hero") or b["typ"] not in N_PER or b["poly"].area < 30:
            continue
        by.setdefault(b["typ"], []).append((route.distance(b["poly"]), i))
    for typ, lst in by.items():
        lst.sort()
        n = 0
        for dist, i in lst:
            if n >= N_PER[typ]:
                break
            b = blds[i]
            poly, p = b["poly"], b["props"]
            if typ == "block" and (p.get("storeys") or 0) < 3:
                continue
            if typ == "hall" and poly.area < 500:
                continue
            c = np.asarray(poly.centroid.coords[0])
            h = float(p.get("height_m") or 6.0)
            zg = float(p.get("ground_z_evrf2007") or reg["origin"]["z"])
            size = float(np.sqrt(poly.area))
            # view from the route side, 30 deg off the facade normal, far enough to hold the facade in a 60 deg frame
            rp = np.asarray(route.interpolate(route.project(Point(*c))).coords[0])
            v = rp - c
            v = v / max(np.hypot(*v), 1e-6)
            done = False
            for ang in ANGLES_FOR.get(b["id"], ANGLES):
                ca, sa = np.cos(np.radians(ang)), np.sin(np.radians(ang))
                w = np.array([v[0] * ca - v[1] * sa, v[0] * sa + v[1] * ca])
                for k in (1.0, 0.75, 1.3):
                    r = poly.exterior.distance(Point(*c)) + k * max(14.0, 0.7 * size, 1.1 * h)
                    pos = c + w * (r + 0.5 * size)
                    if b["id"] in DIST_FOR:          # first point of the ray that is DIST_FOR x k outside the footprint
                        want = DIST_FOR[b["id"]] * k
                        for rr in np.arange(1.0, 600.0, 0.5):
                            q = Point(*(c + w * rr))
                            if not poly.contains(q) and poly.exterior.distance(q) >= want:
                                pos = c + w * rr
                                break
                    if any(polys[j].contains(Point(*pos)) for j in tree.query(Point(*pos))):
                        continue
                    edge_pt = np.asarray(poly.exterior.interpolate(poly.exterior.project(Point(*pos))).coords[0])
                    if clear(pos, edge_pt + (pos - edge_pt) * 0.02, i):
                        look = edge_pt + (c - edge_pt) * 0.1 if b["id"] in DIST_FOR else c
                        add(f"r10_{typ}_{n + 1}", pos, look, zg, zg + min(h * 0.5, 6.0),
                            f"{typ} {b['id']} ({p.get('function')}, h {h:.1f} m, storeys {p.get('storeys')}), "
                            f"{dist:.0f} m from the start route, view {ang:+d} deg off the route side")
                        done = True
                        break
                if done:
                    break
            n += done
    # concrete fences (OSM barrier=wall that are not noise barriers): eye 6 m off the wall, looking along it
    src = json.loads((rdir / "generated" / "streetscape_sources.json").read_text(encoding="utf-8"))
    walls = []
    for f in src["osm"]["ways"]:
        t = f["tags"]
        if t.get("barrier") == "wall" and t.get("wall") != "noise_barrier":
            ls = LineString(np.asarray(f["geometry"]["coordinates"], float) - [ox, oy])
            if ls.length > 25:
                walls.append((route.distance(ls), ls, f.get("osm_way")))
    walls.sort(key=lambda w: w[0])
    for k, (dist, ls, wid) in enumerate(walls[:3]):
        for side in (1, -1):
            a_, b_ = np.asarray(ls.interpolate(0.25, True).coords[0]), np.asarray(ls.interpolate(0.6, True).coords[0])
            d = (b_ - a_) / max(np.hypot(*(b_ - a_)), 1e-6)
            nrm = np.array([-d[1], d[0]]) * side
            pos = a_ + nrm * 6.0 - d * 4.0
            if any(polys[j].contains(Point(*pos)) for j in tree.query(Point(*pos))) or not clear(pos, a_ + nrm * 0.3, -1):
                continue
            zg = float(reg["origin"]["z"])
            add(f"r10_fence_{k + 1}", pos, b_, zg, zg + 1.2, f"concrete fence osm way {wid}, {ls.length:.0f} m, "
                f"{dist:.0f} m from the start route", fov=55.0)
            break
    out = {"schema": "truck-sim-pl/gate3-cameras/1", "region": a.region,
           "frame": "local E,N,U (E,N = EPSG:2180 minus region origin; U = EVRF2007, re-seated on the collision)",
           "cameras": cams}
    p = rdir / "buildings_r10_cameras.json"
    p.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(p, len(cams))
    for c in cams:
        print(" ", c["id"], c["pos"], c["note"][:110])


if __name__ == "__main__":
    main()
