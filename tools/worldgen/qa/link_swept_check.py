"""seams-fix-s23: does the tractor + 13.6 m semitrailer stay on the hard surface when the autopilot follows the path
`route tail + route link` exactly (front axle on the lane polyline)? Kinematic model of roads/swept_path.py
(tractrix, valid at low speed); every tyre edge point tested against the built hard surface of the tile (chunk GLBs:
node `road` + `paved` without grass, qa/seam_section.tris / locate). Prints the tyre points off the hard surface.
    uv run --project tools/worldgen python tools/worldgen/qa/link_swept_check.py <link id> [tail_m] [head_m]
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import seam_section as S  # noqa: E402
from roads.swept_path import Combination, _unit  # noqa: E402
ROOT = Path(__file__).resolve().parents[3]
LINKS = ROOT / "game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/route_links.json"


def check(link_id, tail_m=60.0, head_m=160.0, v=Combination()):
    L = next(x for x in json.loads(LINKS.read_text(encoding="utf-8"))["links"] if x["id"] == link_id)
    tile = L["afterRoute"] or L["tile"]
    r = json.loads((ROOT / "Data/Regions" / L["tile"] / "route_start.json").read_text(encoding="utf-8"))
    R = np.array(r["points_en"], float)[-int(tail_m / 2) - 1:]
    P = np.column_stack([L["e"], L["n"]])[1:int(head_m / 2) + 1]
    path = np.vstack([R, P])
    # densify to 0.25 m
    seg = np.hypot(*np.diff(path, axis=0).T); s = np.concatenate([[0], np.cumsum(seg)])
    si = np.arange(0, s[-1], 0.25); path = np.column_stack([np.interp(si, s, path[:, 0]), np.interp(si, s, path[:, 1])])
    c = 0.5 * (path.min(0) + path.max(0)); rad = float(np.max(path.max(0) - path.min(0))) / 2 + 30.0
    road = S.tris(ROOT, L["tile"], "road", c, rad=rad); paved = S.tris(ROOT, L["tile"], "paved", c, rad=rad)
    hard = np.concatenate([t for k, t in list(road.items()) + list(paved.items()) if "grass" not in k and "verge" not in k])
    t0 = _unit(path[1] - path[0]); pr = path[0] - t0 * v.L1; pk = pr + t0 * v.c; pt = pk - t0 * v.l2
    th = v.trailer_track / 2 + v.trailer_tyre_w / 2; fo = v.front_track / 2 + v.front_tyre_w / 2
    pts, tags = [], []
    for i in range(1, len(path)):
        pf = path[i]; u1 = _unit(pf - pr); pr = pf - u1 * v.L1; pk = pr + u1 * v.c; u2 = _unit(pk - pt); pt = pk - u2 * v.l2
        n1 = np.array([-u1[1], u1[0]]); n2 = np.array([-u2[1], u2[0]])
        if i % 4:
            continue
        for sg in (1, -1):
            pts += [pf + sg * n1 * fo, pr + sg * n1 * v.rear_outer_half] + [pk - u2 * d + sg * n2 * th for d in v.trailer_axles]
            tags += [(i * 0.25, "front"), (i * 0.25, "drive")] + [(i * 0.25, "trailer")] * 3
    z = S.locate(hard, np.array(pts))
    cw = np.concatenate([t for k, t in road.items() if k.startswith("road_")])
    zc = S.locate(cw, np.array(pts))
    off = [(round(t[0] - tail_m, 1), t[1]) for t, zz in zip(tags, z) if np.isnan(zz)]
    offc = [(round(t[0] - tail_m, 1), t[1]) for t, zz in zip(tags, zc) if np.isnan(zz)]
    return {"link": link_id, "tyre_points": len(pts), "off_hard": len(off), "first_off": off[:12],
            "off_carriageway": len(offc), "first_off_carriageway": offc[:20],
            "note": "s [m] from the route -> link join (negative = route tail); off_carriageway = on kerb / sidewalk / paving"}


if __name__ == "__main__":
    a = sys.argv[1:]
    print(json.dumps(check(a[0], *map(float, a[1:3])), indent=1))
