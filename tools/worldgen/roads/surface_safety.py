"""Height-aware plan queries shared by furniture and paint safety passes."""
import re

import numpy as np
import shapely


class SurfaceIndex:
    def __init__(self, parts, select):
        sel = [p for p in parts if select(p) and len(p.T)]
        tris = [p.V[p.T] for p in sel]
        self.xyz = np.concatenate(tris) if tris else np.empty((0, 3, 3))
        self.src = np.concatenate([np.full(len(p.T), p.src or "", dtype=object) for p in sel]) if sel \
            else np.empty(0, dtype=object)
        polys = shapely.polygons(self.xyz[:, :, :2])
        good = shapely.area(polys) > 1e-9
        self.xyz, self.polys, self.src = self.xyz[good], polys[good], self.src[good]
        self.tree = shapely.STRtree(self.polys)

    def near(self, shape, zlo, zhi, dz=1.0, exclude=None):
        """Union of the triangles intersecting `shape` within the height band; `exclude` = compiled regex of
        part sources left out (the own paved shoulder of a rule barrier, own_shoulder())."""
        ids = self.tree.query(shape, predicate="intersects")
        if len(ids):
            xyz = self.xyz[ids, :, 2]
            ids = ids[(xyz.min(1) <= zhi + dz) & (xyz.max(1) >= zlo - dz)]
        if exclude is not None and len(ids):
            ids = ids[[not exclude.match(s) for s in self.src[ids]]]
        return shapely.union_all(self.polys[ids])


def carriageway(p):
    return p.layer in ("road", "bridge") and (p.mat.startswith("road_") or p.mat in ("apron_sett", "apron_paving_light"))


def island(p):
    return p.layer == "road" and p.src.startswith("island:")


def own_shoulder(rail_key):
    """Regex of the side-profile parts (`<chain>:<side>:<k>`) of the chain side a RULE barrier run
    (`<chain>:<side>:<kind>`) was laid out from, or None (authored / pier rails, other keys).

    Its post line is computed from that side profile (furniture.rural_barrier_line, ADR 0272: posts on the
    unpaved shoulder behind the flush asphalt shoulder; deck cap, ADR 0117): the flush asphalt shoulder of the
    same side is the strip the barrier protects, not a lane it intrudes on. The lanes of the chain (part
    `<chain>`) and every other surface keep the full ADR 0310 clearance."""
    parts = str(rail_key).rsplit(":", 2)
    if len(parts) != 3 or not parts[0].startswith("c:") or parts[1] not in ("L", "R"):
        return None
    return re.compile(re.escape(f"{parts[0]}:{parts[1]}:") + r"\d+$")
