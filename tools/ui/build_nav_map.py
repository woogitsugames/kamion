"""Cab navigation map data (KNAV v1) for the infotainment screen (game/Assets/_Project/UI/CabDisplays/NavMapData.cs).

Reads the region products (all in git, no network):
  Data/Regions/<id>/roads.graph.json  - road centrelines (OSM ODbL + BDOT10k), class, name, width, oneway
  Data/Regions/<id>/buildings.geojson - footprints (BDOT10k / OSM), outer rings only
  Data/Regions/<id>/route_start.json  - the start route (G3) in region-local metres, edge id per point
  Data/Regions/<id>/region.yaml       - origin (region-local frame: E = x - origin.x, N = y - origin.y, ADR 0003)
and writes game/Assets/_Project/UI/Resources/CabDisplay/Nav/<id>.bytes (little endian):

  "KNAV" u16 version=1
  f32 minE minN maxE maxN                         region-local bounds of the data
  u16 nNames, nNames x (u16 len, utf8)            street names (index 0 = "")
  u16 nRoads, nRoads x (u8 class, u8 flags, f32 width_m, u16 name, u16 nPts, nPts x (f32 e, f32 n))
  u16 nBuildings, nBuildings x (u16 nPts, nPts x (f32 e, f32 n), u16 nTris, nTris x 3 u16)
  u32 nRoute, nRoute x (f32 e, f32 n, u16 name, u16 maxspeed_kmh)

Classes: 0 service / living_street / track, 1 residential / unclassified / tertiary (+link), 2 secondary (+link),
3 trunk / primary (+link). flags bit0 oneway, bit1 *_link. Polylines simplified (Douglas-Peucker 0.6 m roads,
0.4 m buildings); buildings triangulated by ear clipping here, so the game never triangulates.

Usage: python tools/ui/build_nav_map.py --region bialystok-industrial-c   (stdlib only)
"""
import argparse
import json
import math
import os
import struct
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(REPO, "game", "Assets", "_Project", "UI", "Resources", "CabDisplay", "Nav")

CLASS = {
    "service": 0, "living_street": 0, "track": 0, "pedestrian": 0,
    "residential": 1, "unclassified": 1, "tertiary": 1, "tertiary_link": 1,
    "secondary": 2, "secondary_link": 2,
    "primary": 3, "primary_link": 3, "trunk": 3, "trunk_link": 3, "motorway": 3, "motorway_link": 3,
}


def read_origin(region_dir):
    ox = oy = None
    in_origin = False
    with open(os.path.join(region_dir, "region.yaml"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("origin:"):
                in_origin = True
                continue
            if in_origin:
                if not line.startswith(" "):
                    break
                k, _, v = line.strip().partition(":")
                if k == "x":
                    ox = float(v)
                elif k == "y":
                    oy = float(v)
    if ox is None or oy is None:
        raise SystemExit("origin not found in region.yaml")
    return ox, oy


def attr(edge, key, default=None):
    a = edge.get("attrs", {}).get(key)
    return a.get("v", default) if isinstance(a, dict) else default


def dp(points, tol):
    """Douglas-Peucker on a list of (x, y)."""
    if len(points) < 3:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        a, b = stack.pop()
        ax, ay = points[a]
        bx, by = points[b]
        dx, dy = bx - ax, by - ay
        ll = math.hypot(dx, dy) or 1e-9
        best, bi = -1.0, -1
        for i in range(a + 1, b):
            px, py = points[i]
            d = abs(dy * (px - ax) - dx * (py - ay)) / ll
            if d > best:
                best, bi = d, i
        if best > tol:
            keep[bi] = True
            stack.append((a, bi))
            stack.append((bi, b))
    return [p for p, k in zip(points, keep) if k]


def dp_ring(ring, tol):
    """Douglas-Peucker on a closed ring (first point not repeated): split at the vertex farthest from ring[0]."""
    if len(ring) < 4:
        return list(ring)
    x0, y0 = ring[0]
    k = max(range(len(ring)), key=lambda i: (ring[i][0] - x0) ** 2 + (ring[i][1] - y0) ** 2)
    a = dp(ring[:k + 1], tol)
    b = dp(ring[k:] + [ring[0]], tol)
    return a[:-1] + b[:-1]


def area2(poly):
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return s


def ear_clip(poly):
    """Triangulates a simple polygon (no holes); returns index triples into poly (counter-clockwise)."""
    n = len(poly)
    if n < 3:
        return []
    idx = list(range(n))
    if area2(poly) < 0:
        idx.reverse()

    def inside(p, a, b, c):
        def s(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
        neg = d1 < 0 or d2 < 0 or d3 < 0
        pos = d1 > 0 or d2 > 0 or d3 > 0
        return not (neg and pos)

    tris = []
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        found = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            a, b, c = poly[i0], poly[i1], poly[i2]
            if (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]) <= 1e-9:
                continue  # reflex or degenerate
            if any(inside(poly[j], a, b, c) for j in idx if j not in (i0, i1, i2)):
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            found = True
            break
        if not found:
            break  # self-intersecting remainder: fan the rest (rare, BDOT rings are simple)
    if len(idx) >= 3:
        for k in range(1, len(idx) - 1):
            tris.append((idx[0], idx[k], idx[k + 1]))
    return tris


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    args = ap.parse_args()
    rdir = os.path.join(REPO, "Data", "Regions", args.region)
    ox, oy = read_origin(rdir)
    graph = json.load(open(os.path.join(rdir, "roads.graph.json"), encoding="utf-8"))
    bld = json.load(open(os.path.join(rdir, "buildings.geojson"), encoding="utf-8"))
    route = json.load(open(os.path.join(rdir, "route_start.json"), encoding="utf-8"))

    names = [""]
    name_idx = {"": 0}

    def name_id(n):
        n = n or ""
        if n not in name_idx:
            name_idx[n] = len(names)
            names.append(n)
        return name_idx[n]

    roads = []
    edge_name = {}
    for e in graph["edges"]:
        hw = attr(e, "highway", "service")
        cls = CLASS.get(hw)
        if cls is None:
            continue
        geom = e["geometry"]
        if isinstance(geom, str):
            geom = json.loads(geom)
        pts = dp([(x - ox, y - oy) for x, y in geom], 0.6)
        flags = (1 if attr(e, "oneway") in ("yes", True, 1, "1") else 0) | (2 if hw.endswith("_link") else 0)
        width = float(attr(e, "width", 0) or 0) or [4.0, 6.0, 7.0, 8.0][cls]
        nm = attr(e, "name", "") or ""
        edge_name[e["id"]] = nm
        roads.append((cls, flags, width, name_id(nm), pts))
    roads.sort(key=lambda r: r[0])  # draw order: minor first

    buildings = []
    for f in bld["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            ring = [(x - ox, y - oy) for x, y in poly[0]]
            if len(ring) > 1 and ring[0] == ring[-1]:
                ring = ring[:-1]
            ring = dp_ring(ring, 0.4)
            if len(ring) < 3 or abs(area2(ring)) < 2 * 12.0:  # < 12 m2: sheds, not drawn
                continue
            tris = ear_clip(ring)
            if tris:
                buildings.append((ring, tris))

    rpts = route["points_en"]
    redges = route.get("edge", [""] * len(rpts))
    rlim = route.get("maxspeed_kmh", [0] * len(rpts))
    route_rows = []
    for i, (e, n) in enumerate(rpts):
        nm = edge_name.get(redges[i] if i < len(redges) else "", "")
        lim = rlim[i] if i < len(rlim) and rlim[i] is not None else 0
        route_rows.append((e, n, name_id(nm), int(lim)))

    allx = [p[0] for r in roads for p in r[4]] + [r[0] for r in route_rows]
    ally = [p[1] for r in roads for p in r[4]] + [r[1] for r in route_rows]
    out = bytearray()
    out += b"KNAV" + struct.pack("<H", 1)
    out += struct.pack("<4f", min(allx), min(ally), max(allx), max(ally))
    if len(names) > 65535 or len(roads) > 65535 or len(buildings) > 65535:
        raise SystemExit("too many items for u16 counts")
    out += struct.pack("<H", len(names))
    for n in names:
        b = n.encode("utf-8")
        out += struct.pack("<H", len(b)) + b
    out += struct.pack("<H", len(roads))
    for cls, flags, width, nm, pts in roads:
        out += struct.pack("<BBfHH", cls, flags, width, nm, len(pts))
        for x, y in pts:
            out += struct.pack("<ff", x, y)
    out += struct.pack("<H", len(buildings))
    for ring, tris in buildings:
        out += struct.pack("<H", len(ring))
        for x, y in ring:
            out += struct.pack("<ff", x, y)
        out += struct.pack("<H", len(tris))
        for t in tris:
            out += struct.pack("<3H", *t)
    out += struct.pack("<I", len(route_rows))
    for e, n, nm, lim in route_rows:
        out += struct.pack("<ffHH", e, n, nm, lim)

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, args.region + ".bytes")
    with open(path, "wb") as f:
        f.write(out)
    npts = sum(len(r[4]) for r in roads)
    print(f"KNAV {path}: {len(out) / 1024:.1f} KB, roads {len(roads)} ({npts} pts), buildings {len(buildings)}, "
          f"route {len(route_rows)} pts, names {len(names)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
