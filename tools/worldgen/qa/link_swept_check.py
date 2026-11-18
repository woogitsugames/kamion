"""seams-fix-s23 / knyszyn-r24: does the tractor + 13.6 m semitrailer stay on the hard surface when the autopilot follows
the path `route tail + route link` exactly (front axle on the lane polyline)? Kinematic model of roads/swept_path.py
(tractrix, valid at low speed); every tyre edge point tested against the built hard surface of the tile (chunk GLBs:
node `road` + `paved` without grass / verge, qa/seam_section.tris / locate). Prints the tyre points off the hard surface.
An `after_route` link is checked with the last tail_m of the route it continues in front of it; a `replaces_route` /
`start_epsg2180` link from its own first point. head_m 0 = the whole link.

    uv run --project tools/worldgen python tools/worldgen/qa/link_swept_check.py <link id> [tail_m] [head_m]
    uv run --project tools/worldgen python tools/worldgen/qa/link_swept_check.py --all     # every link of a built tile

Hard gate (tests/gis/test_route_links_s23.py::test_after_route_links_keep_tyres_on_hard_surface): 0 tyre points off the
hard surface for the after_route links of a built tile (ADR 0289 'Recenzja s24')."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import seam_section as S  # noqa: E402
from roads.swept_path import Combination, _unit  # noqa: E402
ROOT = Path(__file__).resolve().parents[3]
LINKS = ROOT / "game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/route_links.json"
SAMPLE_M = 0.25      # path densification
EVERY = 4            # tyre points every EVERY * SAMPLE_M = 1 m
NOT_HARD = ("grass", "verge", "island_sand")   # the central island of a roundabout is not drivable (its apron is)


def link_path(L, tail_m=60.0, head_m=0.0, root=ROOT):
    """(path (k,2) tile-local E/N densified to SAMPLE_M, s offset of the link start in it [m])."""
    P = np.column_stack([L["e"], L["n"]])
    if head_m:
        P = P[:int(head_m / 2) + 2]
    if L["afterRoute"] and tail_m > 0:
        r = json.loads((root / "Data/Regions" / L["afterRoute"] / "route_start.json").read_text(encoding="utf-8"))
        R = np.array(r["points_en"], float)[-int(tail_m / 2) - 1:]
        path = np.vstack([R, P[1:]])
        lead = float(np.sum(np.hypot(*np.diff(R, axis=0).T)))
    else:
        path, lead = P, 0.0
    seg = np.hypot(*np.diff(path, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    si = np.arange(0, s[-1], SAMPLE_M)
    return np.column_stack([np.interp(si, s, path[:, 0]), np.interp(si, s, path[:, 1])]), lead


def surfaces(tile, path, root=ROOT):
    """(hard triangles, carriageway triangles) of the built tile around path."""
    c = 0.5 * (path.min(0) + path.max(0))
    rad = float(np.max(path.max(0) - path.min(0))) / 2 + 30.0
    road = S.tris(root, tile, "road", c, rad=rad)
    paved = S.tris(root, tile, "paved", c, rad=rad)
    # a bridge deck carries its carriageway in the `bridge` node (ADR 0288; qa/seam_section.py)
    deck = {k: v for k, v in S.tris(root, tile, "bridge", c, rad=rad).items() if k.startswith("road_")}
    hard = np.concatenate([t for k, t in list(road.items()) + list(paved.items()) + list(deck.items())
                           if not any(w in k for w in NOT_HARD)])
    cw = np.concatenate([t for k, t in list(road.items()) + list(deck.items()) if k.startswith("road_")])
    return hard, cw


def tyre_points(path, v=Combination()):
    """(points (m,2), tags [(s along path, axle)]) of the outer tyre edges, front axle on the path (tractrix)."""
    t0 = _unit(path[1] - path[0]); pr = path[0] - t0 * v.L1; pk = pr + t0 * v.c; pt = pk - t0 * v.l2
    th = v.trailer_track / 2 + v.trailer_tyre_w / 2; fo = v.front_track / 2 + v.front_tyre_w / 2
    pts, tags = [], []
    for i in range(1, len(path)):
        pf = path[i]; u1 = _unit(pf - pr); pr = pf - u1 * v.L1; pk = pr + u1 * v.c; u2 = _unit(pk - pt); pt = pk - u2 * v.l2
        n1 = np.array([-u1[1], u1[0]]); n2 = np.array([-u2[1], u2[0]])
        if i % EVERY:
            continue
        for sg in (1, -1):
            pts += [pf + sg * n1 * fo, pr + sg * n1 * v.rear_outer_half] + [pk - u2 * d + sg * n2 * th for d in v.trailer_axles]
            tags += [(i * SAMPLE_M, "front", sg), (i * SAMPLE_M, "drive", sg)] + [(i * SAMPLE_M, "trailer", sg)] * 3
    return np.array(pts), tags


def _locate(T, pts, cell=25.0):
    """S.locate on 25 m cells of the points with only the triangles whose bbox touches the cell (same result, ~100x
    faster on a 1.5 km link)."""
    z = np.full(len(pts), np.nan)
    if not len(T) or not len(pts):
        return z
    lo, hi = T[:, :, :2].min(1), T[:, :, :2].max(1)
    key = np.floor(pts / cell).astype(int)
    for k in {tuple(x) for x in key}:
        m = np.all(key == k, axis=1)
        c0, c1 = np.array(k) * cell, (np.array(k) + 1) * cell
        t = np.all(hi >= c0, axis=1) & np.all(lo <= c1, axis=1)
        if t.any():
            z[m] = S.locate(T[t], pts[m])
    return z


def evaluate(path, hard, cw, lead=0.0, v=Combination(), bbox=None, settle_m=0.0):
    """bbox = (emin, nmin, emax, nmax) tile-local: tyre points outside it (the trailer still behind the seam of a link
    that starts on it, the last metres past the end seam) belong to the neighbour tile and are not tested.
    settle_m: the first metres of a path with no route tail in front of it are skipped (the vehicle is initialised
    straight there - its real pose comes from the previous tile, which this check does not load)."""
    pts, tags = tyre_points(path, v)
    keep = np.array([t[0] >= settle_m for t in tags])
    if bbox is not None:
        keep &= (pts[:, 0] >= bbox[0]) & (pts[:, 0] <= bbox[2]) & (pts[:, 1] >= bbox[1]) & (pts[:, 1] <= bbox[3])
    pts, tags = pts[keep], [t for t, k in zip(tags, keep) if k]
    z, zc = _locate(hard, pts), _locate(cw, pts)
    off = [(round(t[0] - lead, 1), t[1], "left" if t[2] > 0 else "right", [round(float(p[0]), 2), round(float(p[1]), 2)])
           for t, zz, p in zip(tags, z, pts) if np.isnan(zz)]
    offc = [(round(t[0] - lead, 1), t[1]) for t, zz in zip(tags, zc) if np.isnan(zz)]
    return {"tyre_points": len(pts), "off_hard": len(off), "first_off": off[:12],
            "off_carriageway": len(offc), "first_off_carriageway": offc[:20]}


def check(link_id, tail_m=60.0, head_m=0.0, v=Combination(), links=None, root=ROOT):
    links = links or json.loads(LINKS.read_text(encoding="utf-8"))["links"]
    L = next(x for x in links if x["id"] == link_id)
    path, lead = link_path(L, tail_m, head_m, root)
    hard, cw = surfaces(L["tile"], path, root)
    settle = 0.0 if lead > 0 else v.L1 + v.kp_rear       # whole combination length behind the front axle
    r = evaluate(path, hard, cw, lead, v, tile_bbox(L["tile"], root), settle)
    r.update({"link": link_id, "tile": L["tile"],
              "note": "s [m] from the route -> link join (negative = route tail); off_carriageway = on kerb / "
                      "sidewalk / paving / apron"})
    return r


def tile_bbox(tile, root=ROOT, margin=0.5):
    import yaml
    reg = yaml.safe_load((root / "Data/Regions" / tile / "region.yaml").read_text(encoding="utf-8"))
    b, o = reg["bbox"], reg["origin"]
    return (b["xmin"] - o["x"] + margin, b["ymin"] - o["y"] + margin, b["xmax"] - o["x"] - margin, b["ymax"] - o["y"] - margin)


def built(tile, root=ROOT) -> bool:
    m = root / "Data/Regions" / tile / "generated/world_manifest.json"
    if not m.exists():
        return False
    chunks = json.loads(m.read_text(encoding="utf-8"))["chunks"]
    return bool(chunks) and all((root / c["file"]).exists() for c in chunks)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--all":
        res = []
        for L in json.loads(LINKS.read_text(encoding="utf-8"))["links"]:
            if not built(L["tile"]):
                continue
            r = check(L["id"])
            res.append({k: r[k] for k in ("link", "tile", "tyre_points", "off_hard", "off_carriageway")})
        print(json.dumps(res, indent=1))
    else:
        print(json.dumps(check(a[0], *map(float, a[1:3])), indent=1))
