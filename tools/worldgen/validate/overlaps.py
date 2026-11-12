"""Check 1 (M37): overlaps visible to the driver.

  object_in_carriageway   a sign / lamp / pole / tree / bus stop / crossing whose footprint circle reaches into
                          the carriageway ribbon of the road graph;
  object_on_kerb          same object standing in the kerb band just outside the carriageway edge
                          (< kerb_zone_m from the edge, footprint included);
  object_in_object        two distinct ground objects closer than min_obj_separation_m;
  tree_in_building        a tree (BDOT point or ortho crown) whose trunk or > 50 % of its crown is inside a
                          building footprint;
  building_in_carriageway a building footprint intersecting a carriageway ribbon by > building_road_area_m2.

Not duplicated with roads/consistency.py: that one tests the generated mesh props against mesh surfaces;
this one tests the source object positions (OSM/BDOT/ortho + generated route_signs/lamp_rows JSON) against
the road-graph ribbons, so it catches placement errors before/independently of meshing.
"""

from __future__ import annotations

import numpy as np
import shapely
from shapely.geometry import Point

from .common import (BUILDING_ROAD_AREA_M2, KERB_ZONE_M, MIN_OBJ_SEPARATION_M, OBJ_FOOTPRINT_M,
                     SKRAJNIA_M, TREE_IN_BUILDING_OVERLAP, Finding, World, carriageway_polygons)


TRUNK_R_M = 0.45          # WORKING_VALUE: tree trunk radius for overlap tests (crown may overhang the road)
OBSTACLE_KINDS = {"tree", "sign", "lamp", "power_pole", "pylon", "bollard"}
# road features that legitimately sit ON the carriageway are NOT obstacles: crossings (zebra), bus stops,
# traffic signals / give_way / stop nodes are placed on the road in OSM by convention.


def _objects(w: World) -> list[dict]:
    """Point objects with an id, kind and footprint radius, from every available source."""
    out = []
    for p in w.points:
        kind = p["kind"]
        if kind in ("street_lamp",):
            kind = "lamp"
        if kind in ("pole", "tower"):
            kind = "power_pole"
        r = OBJ_FOOTPRINT_M.get(kind) or OBJ_FOOTPRINT_M["default"]
        if kind == "tree":
            r = TRUNK_R_M
        out.append({"id": p["id"], "kind": kind, "e": p["e"], "n": p["n"], "r": r})
    for t in w.trees:
        out.append({"id": t["id"], "kind": "tree", "e": t["e"], "n": t["n"], "r": TRUNK_R_M})
    for s in w.signs:
        out.append({"id": f"sign:{s['id']}", "kind": "sign", "e": s["e"], "n": s["n"], "r": OBJ_FOOTPRINT_M["sign"]})
    for l in w.lamps:
        out.append({"id": f"lamp:{l['id']}", "e": l["e"], "n": l["n"], "kind": "lamp", "r": OBJ_FOOTPRINT_M["lamp"]})
    return out


def check(w: World) -> list[Finding]:
    findings: list[Finding] = []
    polys = carriageway_polygons(w)
    if polys:
        union = shapely.unary_union([p for _, p in polys])
        tree = shapely.STRtree([p for _, p in polys])
    else:
        union, tree = None, None

    # ---- objects vs carriageway / kerb band (only true obstacles; road features excluded).
    # Signed distance s from the carriageway edge: s > 0 = centre inside the carriageway (in the lane),
    # -skrajnia_m < s <= 0 = closer to the edge than the required clearance (on the kerb).
    for o in _objects(w):
        if o["kind"] not in OBSTACLE_KINDS or union is None:
            continue
        pt = Point(o["e"], o["n"])
        if union.covers(pt):
            s = float(union.boundary.distance(pt))
            findings.append(Finding("object_in_carriageway", o["e"], o["n"], o["id"],
                                    f"{o['kind']} centre {s:.2f} m inside the carriageway edge",
                                    severity="error" if s > KERB_ZONE_M else "warn",
                                    extra={"kind": o["kind"], "depth_m": round(s, 2)}))
        else:
            s = -float(union.distance(pt))
            if s > -SKRAJNIA_M:
                findings.append(Finding("object_on_kerb", o["e"], o["n"], o["id"],
                                        f"{o['kind']} only {abs(s):.2f} m outside the carriageway edge "
                                        f"(< skrajnia {SKRAJNIA_M:.2f} m) - stands on the kerb",
                                        severity="warn",
                                        extra={"kind": o["kind"], "dist_to_edge_m": round(abs(s), 2)}))

    # ---- objects in each other (true obstacles only)
    objs = [o for o in _objects(w) if o["kind"] in OBSTACLE_KINDS]
    if len(objs) > 1:
        circles = [Point(o["e"], o["n"]).buffer(o["r"] + MIN_OBJ_SEPARATION_M) for o in objs]
        otree = shapely.STRtree(circles)
        pi, ti = otree.query(shapely.points([(o["e"], o["n"]) for o in objs]), predicate="intersects")
        seen = set()
        for a, b in zip(pi.tolist(), ti.tolist()):
            if a == b or a > b or objs[a]["id"] == objs[b]["id"]:
                continue
            key = (objs[a]["id"], objs[b]["id"])
            if key in seen:
                continue
            seen.add(key)
            d = float(Point(objs[a]["e"], objs[a]["n"]).distance(Point(objs[b]["e"], objs[b]["n"])))
            if d < objs[a]["r"] + objs[b]["r"] + MIN_OBJ_SEPARATION_M:
                mx, my = (objs[a]["e"] + objs[b]["e"]) / 2, (objs[a]["n"] + objs[b]["n"]) / 2
                fam_a = "osm" if objs[a]["id"].startswith(("osm:", "sign:osm", "lamp:")) else "bdot"
                fam_b = "osm" if objs[b]["id"].startswith(("osm:", "sign:osm", "lamp:")) else "bdot"
                # same physical object digitised in OSM and BDOT (e.g. power pole) = source duplicate, info
                sev = "warn" if (fam_a == fam_b or objs[a]["kind"] != objs[b]["kind"]) else "info"
                findings.append(Finding("object_in_object", mx, my, f"{objs[a]['id']}|{objs[b]['id']}",
                                        f"{objs[a]['kind']} and {objs[b]['kind']} only {d:.2f} m apart "
                                        f"(need >= {(objs[a]['r'] + objs[b]['r'] + MIN_OBJ_SEPARATION_M):.2f} m)",
                                        severity=sev,
                                        extra={"a": objs[a]["id"], "b": objs[b]["id"], "dist_m": round(d, 2)}))

    # ---- trees in buildings
    if w.buildings and w.trees:
        bpolys = [b["poly"] for b in w.buildings]
        btree = shapely.STRtree(bpolys)
        bpts = [Point(b["poly"].centroid.x, b["poly"].centroid.y) for b in w.buildings]
        tpts = shapely.points([(t["e"], t["n"]) for t in w.trees])
        pi, ti = btree.query(tpts, predicate="intersects")
        hits: dict[int, list[int]] = {}
        for a, b in zip(pi.tolist(), ti.tolist()):
            hits.setdefault(a, []).append(b)
        for a, blist in hits.items():
            t = w.trees[a]
            pt = Point(t["e"], t["n"])
            for b in blist:
                bld = w.buildings[b]
                crown = pt.buffer(t["r"])
                inter = float(crown.intersection(bld["poly"]).area)
                frac = inter / max(crown.area, 1e-9)
                if pt.within(bld["poly"]) or frac > TREE_IN_BUILDING_OVERLAP:
                    findings.append(Finding("tree_in_building", t["e"], t["n"], t["id"],
                                            f"tree crown r={t['r']:.1f} m overlaps building {bld['id']} by "
                                            f"{frac * 100:.0f} % (trunk inside: {pt.within(bld['poly'])})",
                                            severity="error",
                                            extra={"building": bld["id"], "crown_overlap_frac": round(frac, 2)}))

    # ---- buildings in the carriageway
    if polys and w.buildings:
        for b in w.buildings:
            _pi, ti = tree.query([b["poly"]], predicate="intersects")
            hit = 0.0
            for e_i in set(np.atleast_1d(ti).tolist()):
                hit += float(b["poly"].intersection(polys[e_i][1]).area)
            if hit > BUILDING_ROAD_AREA_M2:
                c = b["poly"].centroid
                findings.append(Finding("building_in_carriageway", c.x, c.y, b["id"],
                                        f"building footprint intersects the carriageway by {hit:.1f} m2",
                                        severity="error", extra={"area_m2": round(hit, 2)}))
    return findings
