"""Routing graph of one region (KRTG v1) for the in-game GPS (ADR 0150).

Inputs (all in git, no network):
  Data/Regions/<id>/roads.graph.json       road graph with provenance (OSM ODbL + BDOT10k), EPSG:2180
  Data/Regions/<id>/region.yaml            origin of the region-local frame (E = x - origin.x, N = y - origin.y)
  Data/Regions/<id>/turn_restrictions.json OSM type=restriction relations touching the region's ways
                                           (refreshed from the cached Geofabrik extract with --refresh-restrictions;
                                           needs pyosmium, run through `uv run --project tools/worldgen`)
Output:
  game/Assets/_Project/UI/Resources/CabDisplay/Nav/<id>_route.bytes  (little endian)

  "KRTG" u16 version=1
  u16 nNames, nNames x (u16 len, utf8)                     street names (index 0 = "")
  u32 nNodes, nNodes x (f32 e, f32 n, u8 flags)            flags bit0 boundary (edge leaves the region data)
  u32 nEdges, nEdges x (u32 from, u32 to, f32 length_m, u8 class, u8 flags, u16 name, u8 maxspeed_kmh,
                        u8 maxspeed_src, u16 nPts, nPts x (f32 e, f32 n))
  u16 nRestr, nRestr x (u32 fromEdge, u32 viaNode, u32 toEdge, u8 kind)   kind 0 = no_*, 1 = only_*
  version >= 2, lanes (only edges with a turn:lanes* / lanes* tag):
  u32 nLanes, nLanes x (u32 edge, u8 nFwd, u8 nBwd, nFwd + nBwd x u8 laneMask)   edges in ascending order;
    masks of the stored forward direction (from -> to, after any oneway=-1 reversal) first, then backward.

Edge flags: bit0 oneway (travel only from -> to; oneway=-1 is reversed here), bit1 roundabout, bit2 no trucks
(access=no, hgv=no, service=emergency_access), bit3 restricted access (private / destination / customers / delivery,
service=driveway: allowed only as first / last edge), bit4 *_link.
Classes: 0 service / living_street / track, 1 residential / unclassified / tertiary, 2 secondary, 3 trunk / primary.
maxspeed_src: 0 default (pipeline default, UNVERIFIED), 1 OSM.
Lane mask bits (OSM Key:turn:lanes, one u8 per lane, leftmost lane first): bit0 left, bit1 slight_left, bit2 through,
bit3 slight_right, bit4 right, bit5 merge_to_left, bit6 merge_to_right, bit7 reverse; 0 = none / empty / no data.
turn:lanes applies to both travel directions of a way; turn:lanes:forward / :backward override one direction
(they swap when oneway=-1 reverses the stored geometry). lanes / lanes:forward / :backward give only the lane
count (masks 0). Turn restrictions not tagged in OSM are not known: the game treats every other turn as allowed
except U-turns (a 16.5 m combination) - UNVERIFIED against the street.

Usage:
  python tools/worldgen/navgraph/build_route_graph.py --region bialystok-industrial-c
  uv run --project tools/worldgen python tools/worldgen/navgraph/build_route_graph.py --region <id> --refresh-restrictions
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import struct
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT_DIR = os.path.join(REPO, "game", "Assets", "_Project", "UI", "Resources", "CabDisplay", "Nav")
MAGIC = b"KRTG"
VERSION = 2
SUPPORTED_VERSIONS = (1, 2)

# OSM Key:turn:lanes direction bits (wiki OSM "Key:turn"), one u8 mask per lane, leftmost lane first.
LANE_BITS = {
    "left": 1, "slight_left": 2, "through": 4, "slight_right": 8, "right": 16,
    "merge_to_left": 32, "merge_to_right": 64, "reverse": 128,
}


def parse_turn_lanes(value):
    """OSM turn:lanes value -> list of per-lane direction bitmasks (leftmost lane first), or None when untagged.

    Lanes are '|'-separated, directions within a lane ';'-separated (e.g. "left;through|through|right").
    "none" and empty slots = mask 0 (no direction); unknown tokens are ignored (only the wiki values are defined).
    """
    if value is None:
        return None
    lanes = []
    for lane in str(value).split("|"):
        mask = 0
        for tok in lane.split(";"):
            tok = tok.strip()
            if not tok or tok == "none":
                continue
            bit = LANE_BITS.get(tok)
            if bit is not None:
                mask |= bit
        lanes.append(mask)
    return lanes


def _lane_count(value):
    if value is None or value == "":
        return None
    try:
        return max(0, min(255, int(float(value))))
    except (TypeError, ValueError):
        return None


def edge_lanes(e: dict, reversed_way: bool):
    """(fwdMasks, bwdMasks) for the stored edge direction (fwd = from -> to after any oneway=-1 reversal).

    turn:lanes applies to both travel directions of the OSM way; turn:lanes:forward / :backward override one
    direction of the way - they swap when oneway=-1 reversed the stored geometry. lanes / lanes:forward /
    :backward carry only the lane count (masks 0, direction unknown).
    """
    base = parse_turn_lanes(attr(e, "turn:lanes"))
    f = parse_turn_lanes(attr(e, "turn:lanes:forward"))
    b = parse_turn_lanes(attr(e, "turn:lanes:backward"))
    fwd_way = f if f is not None else base
    bwd_way = b if b is not None else base
    n_base = _lane_count(attr(e, "lanes"))
    n_f = _lane_count(attr(e, "lanes:forward"))
    if n_f is None:
        n_f = n_base
    n_b = _lane_count(attr(e, "lanes:backward"))
    if n_b is None:
        n_b = n_base
    if fwd_way is None and n_f:
        fwd_way = [0] * n_f
    if bwd_way is None and n_b:
        bwd_way = [0] * n_b
    fwd, bwd = fwd_way or [], bwd_way or []
    if reversed_way:
        return bwd, fwd
    return fwd, bwd

CLASS = {
    "service": 0, "living_street": 0, "track": 0,
    "residential": 1, "unclassified": 1, "tertiary": 1, "tertiary_link": 1,
    "secondary": 2, "secondary_link": 2,
    "primary": 3, "primary_link": 3, "trunk": 3, "trunk_link": 3, "motorway": 3, "motorway_link": 3,
}
F_ONEWAY, F_ROUNDABOUT, F_NO_TRUCK, F_RESTRICTED, F_LINK = 1, 2, 4, 8, 16
NO_TRUCK_ACCESS = {"no"}
RESTRICTED_ACCESS = {"private", "destination", "customers", "delivery", "permissive"}


def read_origin(region_dir: str) -> tuple[float, float]:
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


def attr(edge: dict, key: str, default=None):
    a = edge.get("attrs", {}).get(key)
    return a.get("v", default) if isinstance(a, dict) else default


def attr_src(edge: dict, key: str) -> str:
    a = edge.get("attrs", {}).get(key)
    return a.get("src", "") if isinstance(a, dict) else ""


def polyline_length(pts) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def build(graph: dict, origin: tuple[float, float], restrictions: list[dict]) -> dict:
    """Pure transform: road graph JSON -> routing graph tables (lists), deterministic order."""
    ox, oy = origin
    names = [""]
    name_idx = {"": 0}

    def name_id(n: str) -> int:
        n = n or ""
        if n not in name_idx:
            name_idx[n] = len(names)
            names.append(n)
        return name_idx[n]

    node_ids = sorted(n["id"] for n in graph["nodes"])
    node_index = {nid: i for i, nid in enumerate(node_ids)}
    by_id = {n["id"]: n for n in graph["nodes"]}
    nodes = [(round(by_id[nid]["x"] - ox, 3), round(by_id[nid]["y"] - oy, 3), 1 if by_id[nid].get("boundary") else 0)
             for nid in node_ids]
    osm_node_to_idx = {by_id[nid]["osm_node"]: node_index[nid] for nid in node_ids if "osm_node" in by_id[nid]}

    edges = []
    skipped = 0
    for e in sorted(graph["edges"], key=lambda e: e["id"]):
        hw = attr(e, "highway", "service")
        cls = CLASS.get(hw)
        if cls is None:
            skipped += 1
            continue
        geom = e["geometry"]
        if isinstance(geom, str):
            geom = json.loads(geom)
        pts = [(round(x - ox, 3), round(y - oy, 3)) for x, y in geom]
        a, b = node_index[e["from"]], node_index[e["to"]]
        ow = str(attr(e, "oneway", "no"))
        flags = 0
        if ow in ("yes", "true", "1", "-1"):
            flags |= F_ONEWAY
        if ow == "-1":
            pts.reverse()
            a, b = b, a
        fwd_lanes, bwd_lanes = edge_lanes(e, ow == "-1")
        if ow in ("yes", "true", "1", "-1"):
            bwd_lanes = []   # the backward direction of a one-way edge is never driven
        if attr(e, "junction") in ("roundabout", "circular"):
            flags |= F_ROUNDABOUT | F_ONEWAY   # OSM: roundabouts imply oneway
        access = str(attr(e, "access", "") or "")
        if access in NO_TRUCK_ACCESS or str(attr(e, "hgv", "") or "") == "no" or attr(e, "service") == "emergency_access":
            flags |= F_NO_TRUCK
        elif access in RESTRICTED_ACCESS or attr(e, "service") == "driveway":
            flags |= F_RESTRICTED
        if hw.endswith("_link"):
            flags |= F_LINK
        ms = attr(e, "maxspeed", 0) or 0
        try:
            ms = int(float(ms))
        except (TypeError, ValueError):
            ms = 0
        ms_src = 1 if attr_src(e, "maxspeed") == "osm" else 0
        length = round(polyline_length(pts), 3)
        edges.append({
            "id": e["id"], "osm_way": e.get("osm_way"), "from": a, "to": b, "length": length, "class": cls,
            "flags": flags, "name": name_id(attr(e, "name", "") or ""), "maxspeed": max(0, min(255, ms)),
            "maxspeed_src": ms_src, "pts": pts, "lanes": (fwd_lanes, bwd_lanes),
        })

    # Turn restrictions: OSM (from way, via node, to way) -> (from edge, via node, to edge) on the split edges.
    restr = []
    unmapped = []
    for r in restrictions:
        via = osm_node_to_idx.get(r.get("via_node"))
        kind = r.get("restriction", "")
        if via is None or not (kind.startswith("no_") or kind.startswith("only_")):
            unmapped.append(r.get("id"))
            continue
        fe = [i for i, e in enumerate(edges) if e["osm_way"] == r["from_way"] and via in (e["from"], e["to"])]
        te = [i for i, e in enumerate(edges) if e["osm_way"] == r["to_way"] and via in (e["from"], e["to"])]
        if not fe or not te:
            unmapped.append(r.get("id"))
            continue
        for f in fe:
            for t in te:
                if f == t and kind != "no_u_turn":
                    continue
                restr.append((f, via, t, 0 if kind.startswith("no_") else 1))
    restr = sorted(set(restr))
    return {"names": names, "nodes": nodes, "edges": edges, "restrictions": restr, "unmapped_restrictions": unmapped,
            "skipped_edges": skipped}


def serialize(t: dict, version: int = VERSION) -> bytes:
    """version 1 omits the lane section (kept to compare against the committed v1 file before regeneration)."""
    if version not in SUPPORTED_VERSIONS:
        raise SystemExit(f"unsupported version {version}")
    out = bytearray()
    out += MAGIC + struct.pack("<H", version)
    if len(t["names"]) > 65535 or len(t["restrictions"]) > 65535:
        raise SystemExit("too many names / restrictions for u16 counts")
    out += struct.pack("<H", len(t["names"]))
    for n in t["names"]:
        b = n.encode("utf-8")
        out += struct.pack("<H", len(b)) + b
    out += struct.pack("<I", len(t["nodes"]))
    for e, n, f in t["nodes"]:
        out += struct.pack("<ffB", e, n, f)
    out += struct.pack("<I", len(t["edges"]))
    for e in t["edges"]:
        out += struct.pack("<IIfBBHBBH", e["from"], e["to"], e["length"], e["class"], e["flags"], e["name"],
                           e["maxspeed"], e["maxspeed_src"], len(e["pts"]))
        for x, y in e["pts"]:
            out += struct.pack("<ff", x, y)
    out += struct.pack("<H", len(t["restrictions"]))
    for f, v, to, k in t["restrictions"]:
        out += struct.pack("<IIIB", f, v, to, k)
    if version >= 2:
        blocks = [(i, e["lanes"]) for i, e in enumerate(t["edges"]) if e["lanes"][0] or e["lanes"][1]]
        out += struct.pack("<I", len(blocks))
        for i, (fwd, bwd) in blocks:
            out += struct.pack("<IBB", i, len(fwd), len(bwd))
            for m in fwd:
                out += struct.pack("<B", m)
            for m in bwd:
                out += struct.pack("<B", m)
    return bytes(out)


def parse(data: bytes) -> dict:
    """Reader (tests and QA): inverse of serialize."""
    o = 0

    def take(fmt):
        nonlocal o
        v = struct.unpack_from(fmt, data, o)
        o += struct.calcsize(fmt)
        return v

    if data[:4] != MAGIC:
        raise ValueError("not KRTG")
    o = 4
    (ver,) = take("<H")
    if ver not in SUPPORTED_VERSIONS:
        raise ValueError(f"version {ver}")
    (nn,) = take("<H")
    names = []
    for _ in range(nn):
        (ln,) = take("<H")
        names.append(data[o:o + ln].decode("utf-8"))
        o += ln
    (nnodes,) = take("<I")
    nodes = [take("<ffB") for _ in range(nnodes)]
    (ne,) = take("<I")
    edges = []
    for _ in range(ne):
        a, b, length, cls, flags, name, ms, mss, npts = take("<IIfBBHBBH")
        pts = [take("<ff") for _ in range(npts)]
        edges.append({"from": a, "to": b, "length": length, "class": cls, "flags": flags, "name": name,
                      "maxspeed": ms, "maxspeed_src": mss, "pts": pts})
    (nr,) = take("<H")
    restr = [take("<IIIB") for _ in range(nr)]
    lanes = {}
    if ver >= 2:
        (nl,) = take("<I")
        for _ in range(nl):
            ei, nf, nb = take("<IBB")
            if ei >= len(edges):
                raise ValueError("lane block edge out of range")
            fwd = [take("<B")[0] for _ in range(nf)]
            bwd = [take("<B")[0] for _ in range(nb)]
            lanes[ei] = (fwd, bwd)
    if o != len(data):
        raise ValueError("trailing bytes")
    for i, e in enumerate(edges):
        e["lanes"] = lanes.get(i, ([], []))
    return {"names": names, "nodes": nodes, "edges": edges, "restrictions": restr, "lanes": lanes, "version": ver}


def refresh_restrictions(region_dir: str, graph: dict, pbf: str | None = None) -> list[dict]:
    """Reads type=restriction relations touching the region's ways from the cached Geofabrik extract (pyosmium)."""
    import osmium  # noqa: PLC0415  (only for the refresh)

    pbf_dir = os.path.join(REPO, "Data", "raw", "osm")
    if pbf:
        pbf_dir, pbfs = os.path.dirname(pbf), [os.path.basename(pbf)]
    else:
        pbfs = sorted(p for p in os.listdir(pbf_dir) if p.endswith(".osm.pbf")) if os.path.isdir(pbf_dir) else []
    if not pbfs:
        raise SystemExit(f"no .osm.pbf in {pbf_dir}: run tools/worldgen/fetch_osm.py first")
    pbf = os.path.join(pbf_dir, pbfs[-1])
    ways = {e.get("osm_way") for e in graph["edges"]}
    rows = []
    for rel in osmium.FileProcessor(pbf, osmium.osm.RELATION):
        tags = dict(rel.tags)
        if tags.get("type") != "restriction":
            continue
        kind = tags.get("restriction") or tags.get("restriction:hgv") or ""
        mem = [(m.type, m.ref, m.role) for m in rel.members]
        fw = [r for t, r, role in mem if t == "w" and role == "from"]
        tw = [r for t, r, role in mem if t == "w" and role == "to"]
        vn = [r for t, r, role in mem if t == "n" and role == "via"]
        if not any(w in ways for w in fw + tw):
            continue
        rows.append({"id": rel.id, "restriction": kind, "hgv_only": "restriction:hgv" in tags and "restriction" not in tags,
                     "from_way": fw[0] if fw else None, "to_way": tw[0] if tw else None,
                     "via_node": vn[0] if len(vn) == 1 else None, "via_is_way": any(t == "w" and role == "via" for t, _, role in mem)})
    rows.sort(key=lambda r: r["id"])
    sha = hashlib.sha256(open(pbf, "rb").read()).hexdigest()
    doc = {"schema": "truck-sim-pl/turn-restrictions/1", "source": os.path.basename(pbf), "source_sha256": sha,
           "license": "ODbL 1.0, © OpenStreetMap contributors",
           "note": "OSM type=restriction relations touching the region's ways. Turns without a relation are NOT verified "
                   "(UNVERIFIED): absence in OSM does not mean the turn is legal.",
           "restrictions": rows}
    with open(os.path.join(region_dir, "turn_restrictions.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--refresh-restrictions", action="store_true")
    ap.add_argument("--out-dir", default=OUT_DIR)
    ap.add_argument("--pbf", help="extract to read restrictions from (default: newest Data/raw/osm/*.osm.pbf)")
    args = ap.parse_args(argv)
    rdir = os.path.join(REPO, "Data", "Regions", args.region)
    graph = json.load(open(os.path.join(rdir, "roads.graph.json"), encoding="utf-8"))
    rpath = os.path.join(rdir, "turn_restrictions.json")
    if args.refresh_restrictions:
        rows = refresh_restrictions(rdir, graph, args.pbf)
    elif os.path.exists(rpath):
        rows = json.load(open(rpath, encoding="utf-8"))["restrictions"]
    else:
        rows = []
        print("WARNING: no turn_restrictions.json - all turns treated as allowed (UNVERIFIED)")
    t = build(graph, read_origin(rdir), rows)
    data = serialize(t)
    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.out_dir, args.region + "_route.bytes")
    with open(path, "wb") as f:
        f.write(data)
    oneway = sum(1 for e in t["edges"] if e["flags"] & F_ONEWAY)
    lane_blocks = sum(1 for e in t["edges"] if e["lanes"][0] or e["lanes"][1])
    lane_dir = sum(1 for e in t["edges"] if any(e["lanes"][0]) or any(e["lanes"][1]))
    print(f"KRTG v{VERSION} {path}: {len(data) / 1024:.1f} KB, nodes {len(t['nodes'])}, edges {len(t['edges'])} "
          f"(oneway {oneway}, skipped {t['skipped_edges']}), names {len(t['names'])}, "
          f"restrictions {len(t['restrictions'])} (OSM relations {len(rows)}, unmapped {len(t['unmapped_restrictions'])}), "
          f"lane blocks {lane_blocks} (with turn directions {lane_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
