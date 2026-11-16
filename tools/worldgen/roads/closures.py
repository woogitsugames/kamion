"""Roads under construction / not open to traffic (ADR 0215, owner decision D65 p.6).

Authored override schema (Data/Regions/<id>/overrides.yaml), same targets as every other edge override:

    - id: <unique id>
      target: {osm_way: [<way>, ...]}        # or {edge: "<graph edge id>"}
      source: "<who / what says the road is not open>"
      reason: ...
      confidence: high | medium | low
      verify: ...
      set: {construction: true}

Meaning of `construction: true` on a graph edge (the carriageway exists in OSM, but is not open to traffic):
  * roads.network      EdgeSection.construction = True, provenance["construction"]; no edge lines, no turn arrows,
                       no rule lamps; surface = CONSTRUCTION_SURFACE_MAT unless the same `set` names a `surface`
  * roads.markings     no horizontal markings on the section (lane / centre / edge lines, arrows, crossings)
  * roads.decals       no repair patches / oil stains (a carriageway that never carried traffic)
  * navgraph           the edge is left out of the routing graph (KRTG): no GPS route, no AI traffic route over it

Not covered here (open, ADR 0215): the arm of a junction shared with an open road (stop / give-way paint of that arm,
a physical closure such as a U-20 barrier), fences, earthworks and plant of the building site.

This module is pure Python (no numpy / shapely): navgraph imports it without the geometry stack."""
from __future__ import annotations

# WORKING_VALUE (ADR 0215): compacted aggregate = the only unbound carriageway material in the library; the 2024
# orthophoto of dk65-05 shows pale sand embankments, a sand / earthworks material does not exist yet (open).
CONSTRUCTION_SURFACE_MAT = "road_gravel"


def is_construction(override: dict) -> bool:
    """True for an authored edge override that closes its targets as a building site."""
    return bool((override.get("set") or {}).get("construction")) and not override.get("kind")


def target_edge_ids(override: dict, graph_edges) -> list:
    """Graph edge ids named by the override target (`edge` or `osm_way`), sorted; [] when nothing matches (stale)."""
    tgt = override.get("target") or {}
    if "edge" in tgt:
        ids = {e["id"] for e in graph_edges}
        return [tgt["edge"]] if tgt["edge"] in ids else []
    if "osm_way" in tgt:
        ways = tgt["osm_way"] if isinstance(tgt["osm_way"], (list, tuple)) else [tgt["osm_way"]]
        ways = {int(w) for w in ways}
        return sorted(e["id"] for e in graph_edges if e.get("osm_way") in ways)
    return []


def construction_edge_ids(graph_edges, overrides) -> set:
    """Ids of the graph edges closed by `set: {construction: true}` overrides."""
    closed = set()
    for ov in overrides or []:
        if is_construction(ov):
            closed.update(target_edge_ids(ov, graph_edges))
    return closed
