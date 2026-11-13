"""Road + terrain generation pipeline (in-memory). The CLI and the exporters live in build_world.py."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

from . import gores as GO
from . import junctions as J
from . import meshing as M
from . import network as Nw
from . import profile as P

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


def build_network(region_id: str, graph: dict | None = None):
    """The road network with its final centre lines and widths (before sides, junctions and heights): graph +
    overrides + width tapers + fork alignment. Shared by build() and scripts/export-route.py, so the start route
    is laid on the lanes the generator builds, not on the raw OSM axes (ADR 0076)."""
    region = load_region(region_id)
    origin = (region["origin"]["x"], region["origin"]["y"])
    rdir = REGIONS / region_id
    graph = graph or json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8"))
    overrides = load_overrides(region_id)
    net = Nw.load(graph, origin, overrides)
    stats = {"fork_tapers": [], "fork_shifts": [], "fork_abreast": []}
    Nw.taper_forks(net, stats["fork_tapers"])
    Nw.align_forks(net, stats["fork_shifts"])       # lane continuity at diverges / merges (ADR 0074)
    Nw.abreast_forks(net, stats["fork_abreast"])    # lane gain / drop merges laid side by side (ADR 0076)
    return net, graph, overrides, stats


def build(region_id: str, built_up: bool = True, hf: P.Heightfield | None = None, side_edit=None) -> World:
    region = load_region(region_id)
    origin = (region["origin"]["x"], region["origin"]["y"])
    rdir = REGIONS / region_id
    ctx = json.loads((rdir / "generated" / "osm_context.json").read_text(encoding="utf-8"))
    terrain_meta = json.loads((rdir / "terrain.json").read_text(encoding="utf-8"))
    net, graph, overrides, net_stats = build_network(region_id)
    net.authored = overrides                         # painted_zone etc. read by the marking stage (ADR 0093)
    from shapely.geometry import LineString as _LS
    net.foot_lines = [(_LS(np.array(f["geometry"]) - np.array(origin)), f["highway"]) for f in ctx["footways"]
                      if len(f["geometry"]) >= 2]      # which way crosses at a crossing node: P-10 or P-11
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
    # second pass now that the junction trims are known: side profiles beside another carriageway are checked
    # right up to the junction patch (ADR 0076: verge / kerb of one branch on the lane of the other)
    Nw.assign_sides(net, foot, built_up=built_up, walkways=walk, yards=yards, trims=True)
    hf = hf or P.load_heightfield(terrain_meta, REPO, origin)
    ties_f = rdir / "profile_ties.json"            # ADR 0146: authored profile ties (authored_override, own file)
    net.profile_ties = json.loads(ties_f.read_text(encoding="utf-8")).get("ties", []) if ties_f.exists() else []
    prof = P.build_profiles(net, hf, net.profile_ties)
    prof["walled_ramps"] = P.mark_walled_ramps(net, hf)
    # gaps between carriageways: island only where OSM / the orthophoto says so, otherwise paved (ADR 0077)
    gore_plan = GO.plan(net, juncs, overrides, origin)
    net.overrides_applied += gore_plan.overrides_applied
    net.overrides_stale += gore_plan.overrides_stale

    buf = M.MeshBuf()
    stats = {"patch": {}}
    if side_edit is not None:            # ADR 0114: dropped kerbs at house driveways (streetscape.plots.apply_drops)
        stats["side_edit"] = side_edit(net)
    for c in net.chains:
        M.build_ribbon(buf, net, c)
        M.build_ribbon(buf, net, c, coarse=True)
    stats["median_fills"] = M.build_median_fills(buf, net)           # ADR 0146
    for j in juncs:
        M.build_patch(buf, net, j, stats=stats["patch"])
        M.build_patch(buf, net, j, coarse=True)
    GO.build(buf, net, gore_plan)                                    # paved gores / P-21 (ADR 0077)
    stats["sides_on_carriageway_culled"] = M.cull_sides_on_carriageway(buf)
    stats["kerb_tris_dropped_in_fills"] = GO.drop_kerbs_in_fills(buf, gore_plan)     # ADR 0093: removed, not sunk
    w = World(region=region, origin=origin, net=net, junctions=juncs, hf=hf, ctx={"points": pts, "foot": foot},
              buf=buf, profiles=prof, stats=stats)
    w.stats.update(net_stats)                                        # fork_tapers / fork_shifts (ADR 0074/0076)
    w.stats["gores"] = GO.report(gore_plan)
    w.gore_plan = gore_plan
    return w
