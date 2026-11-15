"""Knyszyn marketplace: four provisional open market shelters.

The site polygon is OSM way 704368699 (2019); ownership/legal boundaries and
the position, orientation and dimensions of every shelter are WORKING_VALUE.
The owner confirmed the market is across Jagiellonska from address 50. The
owner's drone images are not locally available, so this is PROXY_NOT_APPROVED.
No photo, name, brand, or sign is used. Surface, access, pavilion, islands and
surrounding buildings require separate evidence and integration.

Optional integration: build(buf, region, origin, zsurf, report) after the final
terrain and before buffer flush. The caller must provide terrain/surface and
handle roads and collisions; this module does not generate a plaza or collider.
"""
from __future__ import annotations

import numpy as np
from shapely.geometry import Polygon

from . import buildings_mesh as BM

REGION = "knyszyn"
ASSET_ID = "knyszyn_market_0227"
LAYERS = ("buildings", "buildings_low")
# OSM way 704368699 transformed from EPSG:4326; precision ~0.01 m represents
# coordinate rounding, not survey accuracy or a cadastral boundary.
SITE_EPSG2180 = ((760743.04, 613347.26), (760723.64, 613446.59),
                 (760781.15, 613462.34), (760806.43, 613359.00))
AXIS = np.array([-.205, .979], float)
AXIS /= np.linalg.norm(AXIS)
NORMAL = np.array([-AXIS[1], AXIS[0]])
CENTER = np.array([760764., 613403.], float)
OFFSETS = (-36., -12., 12., 36.)
HALF_LENGTH = 8.0
HALF_WIDTH = 3.5


def _p(p, z):
    return [float(p[0]), float(p[1]), float(z)]


def footprints():
    """OSM-clipped working placements, not a claim about real structures."""
    site = Polygon(SITE_EPSG2180)
    out = []
    for offset in OFFSETS:
        center = CENTER + AXIS*offset
        corners = [center + AXIS*a + NORMAL*b for a,b in
                   ((-HALF_LENGTH,-HALF_WIDTH),(HALF_LENGTH,-HALF_WIDTH),
                    (HALF_LENGTH,HALF_WIDTH),(-HALF_LENGTH,HALF_WIDTH))]
        footprint = Polygon(corners)
        if not site.buffer(-1.).covers(footprint):
            return []
        out.append((center, corners))
    return out


def build(buf, region, origin, zsurf, report):
    result = {"id": ASSET_ID, "status": "skipped", "site": "OSM way 704368699",
              "confidence": "PROXY_NOT_APPROVED / WORKING_VALUE", "shelters": 0,
              "omitted": ["paving", "entrances", "fence", "islands", "pavilion", "rear_buildings", "collisions"]}
    report[ASSET_ID] = result
    if region != REGION:
        return result
    origin = np.asarray(origin, float)
    if origin.shape != (2,) or not np.isfinite(origin).all():
        result["reason"] = "invalid origin"
        return result
    placements = footprints()
    if len(placements) != 4:
        result["reason"] = "shelter outside site margin"
        return result
    anchors = np.asarray([c-origin for c,_ in placements])
    heights = np.asarray(zsurf(anchors[:,0], anchors[:,1]), float).reshape(-1)
    if len(heights) != 4 or not np.isfinite(heights).all():
        result["reason"] = "invalid terrain heights"
        return result
    acc = BM.Acc()
    for (center,corners),z in zip(placements,heights):
        c = center-origin
        q = [p-origin for p in corners]
        eave, ridge = z+3.1, z+4.25
        # Four hipped roof faces, using one existing material on both LODs.
        r0,r1 = c-AXIS*4.5,c+AXIS*4.5
        faces = ((q[0],q[1],r1,r0),(q[1],q[2],r1),
                 (q[2],q[3],r0,r1),(q[3],q[0],r0))
        for layer in LAYERS:
            for face in faces:
                vertices = [_p(p, ridge if np.linalg.norm(p-r0)<1e-6 or np.linalg.norm(p-r1)<1e-6 else eave) for p in face]
                if len(vertices)==4:
                    acc.quad(layer,"roof_metal_graphite",*vertices)
                else:
                    acc.add(layer,"roof_metal_graphite",vertices,[[0,1,2]])
            for a in (-6.8, 6.8):
                for b in (-2.7, 2.7):
                    p=c+AXIS*a+NORMAL*b
                    acc.box(layer,"plinth_dark",_p(p,z+1.55),np.r_[AXIS*.09,0],
                            np.r_[NORMAL*.09,0],[0,0,1.55],skip=(0,))
    acc.flush(buf,ASSET_ID)
    result.update(status="applied", shelters=4, dimensions="WORKING_VALUE 16 x 7 m", collision="not generated")
    return result
