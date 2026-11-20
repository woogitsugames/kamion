"""Height-aware plan queries shared by furniture and paint safety passes."""
import numpy as np
import shapely


class SurfaceIndex:
    def __init__(self, parts, select):
        tris = [p.V[p.T] for p in parts if select(p) and len(p.T)]
        self.xyz = np.concatenate(tris) if tris else np.empty((0, 3, 3))
        polys = shapely.polygons(self.xyz[:, :, :2])
        good = shapely.area(polys) > 1e-9
        self.xyz, self.polys = self.xyz[good], polys[good]
        self.tree = shapely.STRtree(self.polys)

    def near(self, shape, zlo, zhi, dz=1.0):
        ids = self.tree.query(shape, predicate="intersects")
        if len(ids):
            xyz = self.xyz[ids, :, 2]
            ids = ids[(xyz.min(1) <= zhi + dz) & (xyz.max(1) >= zlo - dz)]
        return shapely.union_all(self.polys[ids])


def carriageway(p):
    return p.layer in ("road", "bridge") and (p.mat.startswith("road_") or p.mat in ("apron_sett", "apron_paving_light"))


def island(p):
    return p.layer == "road" and p.src.startswith("island:")
