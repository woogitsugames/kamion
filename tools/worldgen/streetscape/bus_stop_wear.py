"""ADR0099: one source/photo-reviewed bus stopping zone, not shelter projection.

Oil location/radius is an explicit WORKING_VALUE appearance rule at an actual OSM
stop_position. The photograph verifies the paved bay, not a measured oil leak.
Unknown stops are recorded and left untouched. Existing roads.decals atlas/fan is reused.
"""
from __future__ import annotations

import math
import numpy as np
from shapely.geometry import Polygon
from roads import decals as DC
from roads.build_world import chunk_of
from .furniture import SurfaceTop

REVIEWED = {2367445386: {"ref": "464", "photo": "mapillary:1170695487387705"}}
RADIUS_M = .22  # WORKING_VALUE small accumulated drip zone, no arbitrary engine offset


def _height(top, point):
    """Single supported asphalt level; a bridge/overlap is not silently reduced to highest."""
    e, n = point
    ids = top.grid.get((math.floor(e / top.CELL), math.floor(n / top.CELL)), [])
    if not ids:
        raise ValueError("outside_driveable_asphalt")
    t = top.A[ids]
    a, b, c = t[:, 0], t[:, 1], t[:, 2]
    det = (b[:, 1]-c[:, 1])*(a[:, 0]-c[:, 0])+(c[:, 0]-b[:, 0])*(a[:, 1]-c[:, 1])
    valid = abs(det) > 1e-12
    safe = np.where(valid, det, 1.)
    u = ((b[:, 1]-c[:, 1])*(e-c[:, 0])+(c[:, 0]-b[:, 0])*(n-c[:, 1]))/safe
    v = ((c[:, 1]-a[:, 1])*(e-c[:, 0])+(a[:, 0]-c[:, 0])*(n-c[:, 1]))/safe
    w = 1-u-v
    inside = valid & (u >= -1e-6) & (v >= -1e-6) & (w >= -1e-6)
    z = (u*a[:, 2]+v*b[:, 2]+w*c[:, 2])[inside]
    if not len(z):
        raise ValueError("outside_driveable_asphalt")
    if float(np.ptp(z)) > .02:
        raise ValueError("ambiguous_road_levels")
    return float(z.mean())


def emit(buf, candidates, report):
    rep = {"applied": [], "rejected": []}
    parts = [p for p in buf.parts if p.layer == "road" and p.mat in ("road_asphalt", "road_asphalt_new")]
    top = SurfaceTop(parts, layers=("road",))
    for stop in candidates:
        node = stop["osm_node"]
        evidence = REVIEWED.get(node)
        if evidence is None:
            rep["rejected"].append({"osm_node": node, "reason": "no_reviewed_bay_photo"})
            continue
        if stop.get("bus") != "yes" or str(stop.get("ref")) != evidence["ref"]:
            rep["rejected"].append({"osm_node": node, "reason": "source_identity_changed"})
            continue
        center = np.asarray(stop["local_en"], float)
        half = float(stop["half_m"])
        anchor_chunk = tuple(int(x[0]) for x in chunk_of(center[0:1], center[1:2], half))
        # A reused atlas is zero new source group only when this exact chunk already has oil.
        oil_chunks = set()
        for p in buf.parts:
            if p.layer != "markings" or p.mat != "decal_oil":
                continue
            centroids = p.V[p.T, :2].mean(axis=1)
            ci, cj = chunk_of(centroids[:, 0], centroids[:, 1], half)
            oil_chunks.update(zip(ci.tolist(), cj.tolist()))
        if anchor_chunk not in oil_chunks:
            rep["rejected"].append({"osm_node": node, "reason": "would_add_material_group"})
            continue
        paint = [Polygon(p.V[t, :2]) for p in buf.parts if p.layer == "markings" and p.mat.startswith("marking_") for t in p.T]
        captured = {}

        def heights(points):
            polygon = Polygon(points[1:])
            if not polygon.is_valid or any(polygon.intersects(p) for p in paint):
                raise ValueError("paint_overlap_or_invalid_polygon")
            triangles = np.array([(0, 1+k, 1+(k+1) % 9) for k in range(9)])
            tri = points[triangles]
            samples = np.vstack([points, tri.mean(axis=1), (tri[:, 0]+tri[:, 1])/2,
                                 (tri[:, 1]+tri[:, 2])/2, (tri[:, 2]+tri[:, 0])/2])
            ci, cj = chunk_of(samples[:, 0], samples[:, 1], half)
            if any((int(i), int(j)) != anchor_chunk for i, j in zip(ci, cj)):
                raise ValueError("cross_chunk_footprint")
            zs = np.array([_height(top, point) for point in samples])
            # Curbs/holes/other road levels reject the entire fan. Lift each vertex from actual triangles.
            if float(np.ptp(zs)) > .08:
                raise ValueError("road_height_discontinuity")
            captured.update(footprint_en=points.tolist(), road_z=zs[:len(points)].tolist(), chunk=list(anchor_chunk))
            return zs[:len(points)] + DC.LIFT_OIL

        before = len(buf.parts)
        try:
            DC.stain(buf, center, heights, RADIUS_M, ("bus_stop", node), f"oil:bus_stop:osm:{node}")
        except ValueError as exc:
            assert len(buf.parts) == before  # DC.stain samples the whole fan before adding it.
            rep["rejected"].append({"osm_node": node, "reason": str(exc)})
            continue
        rep["applied"].append({"osm_node": node, "ref": evidence["ref"], "photo": evidence["photo"],
                               "working_value": True, "radius_m": RADIUS_M, "triangles": 9,
                               "vertices": 10, "new_source_material_groups": 0,
                               "lift_m": DC.LIFT_OIL, "engine_offset_m": 0, **captured})
    report["bus_stop_oil"] = rep
    return rep
