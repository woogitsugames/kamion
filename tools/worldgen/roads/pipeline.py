"""Road + terrain generation pipeline (in-memory). The CLI and the exporters live in build_world.py."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

from . import junctions as J
from . import meshing as M
from . import network as Nw
from . import profile as P
from .context import footway_lines

REPO = Path(__file__).resolve().parents[3]
REGIONS = REPO / "Data" / "Regions"


@dataclass
class World:
    region: dict
    origin: tuple
    net: Nw.Network
    junctions: list
    hf: P.Heightfield
    ctx: dict
    buf: M.MeshBuf
    profiles: dict
    stats: dict = field(default_factory=dict)
    bridges: list = field(default_factory=list)


def load_region(region_id: str) -> dict:
    d = REGIONS / region_id
    return yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))


def load_overrides(region_id: str) -> list:
    p = REGIONS / region_id / "overrides.yaml"
    if not p.exists():
        return []
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return data.get("overrides", []) or []


def ctx_local(ctx, origin):
    ox, oy = origin
    pts = [dict(p, e=p["x"] - ox, n=p["y"] - oy) for p in ctx["points"]]
    from shapely.geometry import LineString
    foot = [LineString(np.array(f["geometry"]) - np.array([ox, oy])) for f in ctx["footways"]]
    return pts, foot


def build(region_id: str, built_up: bool = True, hf: P.Heightfield | None = None) -> World:
    region = load_region(region_id)
    origin = (region["origin"]["x"], region["origin"]["y"])
    rdir = REGIONS / region_id
    graph = json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8"))
    ctx = json.loads((rdir / "generated" / "osm_context.json").read_text(encoding="utf-8"))
    terrain_meta = json.loads((rdir / "terrain.json").read_text(encoding="utf-8"))
    overrides = load_overrides(region_id)

    net = Nw.load(graph, origin, overrides)
    M.BRIDGE_STYLES.clear()
    for o in overrides:
        if o.get("kind") == "bridge_style":
            ways = {str(e["id"]).split(":")[0].lstrip("w") for e in graph["edges"]}
            hit = [w for w in o["target"]["osm_way"] if str(w) in ways]
            for wid in hit:
                M.BRIDGE_STYLES[str(wid)] = o["set"]
            if hit:
                net.overrides_applied.append({"id": o["id"], "targets": [f"w{w}" for w in hit]})
            else:
                net.overrides_stale.append(o["id"])
    pts, foot = ctx_local(ctx, origin)
    tapers = []
    Nw.taper_forks(net, tapers)
    fork_shifts = []
    Nw.align_forks(net, fork_shifts)          # lane continuity at diverges / merges (ADR 0074)
    # walkways that make a road "urban" (kerbed): OSM footway/cycleway + BDOT10k paved paths (not forest paths)
    from shapely.geometry import LineString
    walk = [LineString(np.array(f["geometry"]) - np.array(origin)) for f in ctx["footways"] if f["highway"] != "path"]
    ss = rdir / "generated" / "streetscape_sources.json"
    yards = None
    if ss.exists():
        import shapely
        from shapely.geometry import Polygon
        src = json.loads(ss.read_text(encoding="utf-8"))
        walk += [LineString(np.array(f["geometry"]["coordinates"]) - np.array(origin))
                 for f in src["bdot10k"]["OT_SKRP_L"] if f["props"].get("materialnawierzchni") not in (None, "grunt naturalny")]
        polys = [Polygon(np.array(f["geometry"]["coordinates"][0]) - np.array(origin)) for f in src["bdot10k"]["OT_PTPL_A"]
                 if f["props"].get("materialnawierzchni") != "grunt naturalny"]
        polys += [Polygon(np.array(a["geometry"]["coordinates"][0]) - np.array(origin)) for a in src["osm"]["areas"]
                  if a["tags"].get("amenity") == "parking"]
        polys += [Polygon(np.array(o["polygon_epsg2180"]) - np.array(origin)) for o in overrides if o.get("kind") == "paved_area"]
        yards = shapely.union_all([shapely.make_valid(p) for p in polys])
        shapely.prepare(yards)
    Nw.assign_sides(net, foot, built_up=built_up, walkways=walk, yards=yards)
    juncs = J.build_junctions(net, pts)
    hf = hf or P.load_heightfield(terrain_meta, REPO, origin)
    prof = P.build_profiles(net, hf)
    prof["walled_ramps"] = P.mark_walled_ramps(net, hf)

    buf = M.MeshBuf()
    stats = {"patch": {}}
    for c in net.chains:
        M.build_ribbon(buf, net, c)
        M.build_ribbon(buf, net, c, coarse=True)
    for j in juncs:
        M.build_patch(buf, net, j, stats=stats["patch"])
        M.build_patch(buf, net, j, coarse=True)
    w = World(region=region, origin=origin, net=net, junctions=juncs, hf=hf, ctx={"points": pts, "foot": foot},
              buf=buf, profiles=prof, stats=stats)
    w.stats["fork_tapers"] = tapers
    w.stats["fork_shifts"] = fork_shifts
    return w
