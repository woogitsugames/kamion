"""seams-fix-s23: the solid P-2a of a junction approach carried across a tile seam.

The marking stage paints the lane / centre lines of a junction approach solid (P-2a) for S.P2A_MIN_LEN = 20 m before
the junction (Dz.U. 2019 poz. 2311 zał. 2 pkt 2.2.1.6). When the junction lies in tile A less than 20 m from the seam,
tile A paints only its part and tile B, which does not know the junction, painted dashed lines right from the seam: on
DW671 Tykocka at the knyszyn | knyszyn-w seam the solid lines ended at the seam and the dashes of knyszyn-w began with a
2 m gap (11.5 m solid in knyszyn instead of 20 m).

Rule (the same data and code on both sides, like ADR 0275): tile B reads the neighbour's graph + overrides + OSM
context from git (region.yaml, roads.graph.json, overrides.yaml, generated/osm_context.json - the build_region input of
the junction stage, never the build_world output), builds the neighbour's plain network and junctions, asks the marking
rule (markings.approach_ends) which chain ends are P-2a approaches, and for every road cut by the seam (ends paired by
OSM way + position, seam_taper.match) whose neighbour half approaches a junction closer than P2A_MIN_LEN to the seam,
paints the rest solid from the seam: carry = P2A_MIN_LEN - (distance from the seam to the junction end of the
neighbour chain). Nothing else changes; tiles with no such road are byte-identical.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import yaml

from . import junctions as J
from . import seam_taper as ST
from . import standards as S

MIN_CARRY_M = 0.5      # a remainder shorter than this is left alone (float noise of the junction trim)


@lru_cache(maxsize=32)
def _neighbour_approaches(region_dir: str) -> tuple:
    """((End, carry_from_seam_needed or None), ...) for the boundary ends of a tile: what its own marking rule paints
    solid next to the seam. Cached per tile directory (a build reads every neighbour once)."""
    from . import markings as MK
    from .pipeline import ctx_local
    d = Path(region_dir)
    reg = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
    origin = (reg["origin"]["x"], reg["origin"]["y"])
    graph = json.loads((d / "roads.graph.json").read_text(encoding="utf-8"))
    net = ST.plain_network(graph, origin, ST._load_overrides(d))
    ctx_f = d / "generated" / "osm_context.json"
    pts = ctx_local(json.loads(ctx_f.read_text(encoding="utf-8")), origin)[0] if ctx_f.exists() else None
    juncs = J.build_junctions(net, pts)
    arm_info = MK.arm_infos(juncs, net.sec_list)
    chains = {c.id: c for c in net.chains}
    out = []
    for e in ST.ends(net):
        c = chains[e.chain]
        appr = MK.approach_ends(c, arm_info, net.sec_list)
        other = "b" if e.end == 0 else "a"           # the junction end is the other end of the chain
        rest = None
        if other in appr:
            s_seam = 0.0 if e.end == 0 else float(c.length)
            rest = S.P2A_MIN_LEN - abs(float(appr[other]) - s_seam)
        out.append((e, rest))
    return tuple(out)


def plan(net, region_id: str, regions: Path | None = None) -> dict:
    """{(chain id, "a" | "b"): solid length from the seam [m]} for this tile's boundary chain ends."""
    regions = regions or ST.REGIONS
    own = ST.ends(net)
    if not own:
        return {}
    out = {}
    for nb, se in ST.neighbours(region_id, regions):
        mine = [e for e in own if ST.on_seam(e.xy, se)]
        if not mine:
            continue
        theirs = [(e, r) for e, r in _neighbour_approaches(str(regions / nb)) if ST.on_seam(e.xy, se)]
        rest = {(e.chain, e.end): r for e, r in theirs}
        for a, b in ST.match(mine, [e for e, _ in theirs]):
            r = rest.get((b.chain, b.end))
            if r is not None and r >= MIN_CARRY_M:
                key = (a.chain, "a" if a.end == 0 else "b")
                out[key] = max(out.get(key, 0.0), round(float(r), 3))
    return out
