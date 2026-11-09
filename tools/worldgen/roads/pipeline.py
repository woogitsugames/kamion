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
    pts, foot = ctx_local(ctx, origin)
    Nw.assign_sides(net, foot, built_up=built_up)
    juncs = J.build_junctions(net, pts)
    hf = hf or P.load_heightfield(terrain_meta, REPO, origin)
    prof = P.build_profiles(net, hf)

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
    return w
