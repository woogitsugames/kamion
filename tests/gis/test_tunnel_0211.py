"""ADR 0211: cut-and-cover tunnel (slab, walls, ground on the slab) for OSM tunnel=yes roads in a cutting."""
import json
import sys
from pathlib import Path

import numpy as np
import shapely

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from roads import tunnels as TN  # noqa: E402
from terrain_mesh import chunks as CH  # noqa: E402


def _graph(rid):
    return json.loads((REPO / "Data" / "Regions" / rid / "roads.graph.json").read_text(encoding="utf-8"))


def test_kleeberga_tunnel_ways_are_the_two_dk8_carriageways():
    g = _graph("bialystok-kleeberga")
    ids = TN.tunnel_edge_ids(g)
    ways = {e["osm_way"] for e in g["edges"] if e["id"] in ids}
    assert ways == {23982181, 76073122}


def test_regions_without_tunnel_roads_are_untouched():
    # C has only building_passage tunnels, Dojlidy none: plan() is None there, build() returns ({}, None) and
    # build_world leaves zc, the parts and the terrain LODs as they were (determinism of region C)
    for rid in ("bialystok-industrial-c", "bialystok-dojlidy"):
        assert TN.tunnel_edge_ids(_graph(rid)) == set(), rid


def test_building_passage_and_footways_are_not_tunnels():
    g = {"edges": [
        {"id": "a", "attrs": {"tunnel": {"v": "building_passage"}, "highway": {"v": "service"}}},
        {"id": "b", "attrs": {"tunnel": {"v": "yes"}, "highway": {"v": "footway"}}},
        {"id": "c", "attrs": {"tunnel": {"v": "yes"}, "highway": {"v": "trunk"}}},
        {"id": "d", "attrs": {"highway": {"v": "trunk"}}},
    ]}
    assert TN.tunnel_edge_ids(g) == {"c"}


class _HF:
    x0, y1 = 10.0, 50.0


def test_grid_plane_matches_the_terrain_triangles():
    """The ground re-emitted on the slab uses the planes of the terrain triangles (chunks.grid_mesh diagonal), so it
    meets the terrain at the cover boundary without a crack."""
    rng = np.random.default_rng(1)
    z = rng.uniform(0, 3, (12, 14))
    grid = TN.Grid(_HF, z)
    V, _N, T = CH.grid_mesh(z, CH.normals(z, 1), _HF.x0, _HF.y1, 1, 0, 13, 0, 11, skirt=1.0)
    T = T[np.all(T < 12 * 14, axis=1)]          # top surface only (no skirts)
    tri = V[T]
    for _ in range(200):
        x, y = rng.uniform(_HF.x0 + 0.01, _HF.x0 + 12.99), rng.uniform(_HF.y1 - 10.99, _HF.y1 - 0.01)
        hit = None
        for t in tri:
            (x1, y1), (x2, y2), (x3, y3) = t[:, :2]
            d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
            a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / d
            b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / d
            if min(a, b, 1 - a - b) >= -1e-9:
                hit = a * t[0, 2] + b * t[1, 2] + (1 - a - b) * t[2, 2]
                break
        assert hit is not None
        assert abs(float(grid.plane(x, y)) - hit) < 1e-6


def test_clipped_triangles_are_ccw_and_keep_the_area():
    poly = shapely.Polygon([(0, 0), (3.3, 0.4), (2.9, 2.7), (0.2, 2.2)])
    tris = TN._clip_grid(poly, 1.0, poly.bounds)
    area = 0.0
    for t in tris:
        cr = (t[1, 0] - t[0, 0]) * (t[2, 1] - t[0, 1]) - (t[1, 1] - t[0, 1]) * (t[2, 0] - t[0, 0])
        assert cr > 0                              # up-facing (CCW seen from above)
        area += cr / 2
    assert abs(area - poly.area) < 1e-6


def test_low_cut_only_touches_the_coarse_lods():
    z = np.full((513, 513), 10.0)
    mask = np.zeros_like(z, bool)
    lm = np.zeros_like(z, bool)
    lm[100:140, 100:140] = True
    a = CH.build_chunks(z, mask, 0.0, 512.0, 512)
    b = CH.build_chunks(z, mask, 0.0, 512.0, 512, low_cut=(lm, np.full_like(z, 2.0)))
    for key in a:
        for li in a[key]:
            za = np.concatenate([p["V"][:, 2] for p in a[key][li]])
            zb = np.concatenate([p["V"][:, 2] for p in b[key][li]])
            if CH.LODS[li] < 4:
                assert np.array_equal(za, zb)
    assert any(np.concatenate([p["V"][:, 2] for p in b[k][2]]).min() < 3.0 for k in b)


def test_clearance_is_the_polish_minimum_or_more():
    assert TN.CLEARANCE_M >= 4.70
    assert TN.SOFFIT_MAX_M >= TN.CLEARANCE_M


def test_cover_is_its_own_primitive_not_merged_into_the_terrain():
    """r1-r3: the cover was a ":vg" strip merged into the terrain primitives; the Unity importer rebuilds the near
    terrain from the grid nodes of that primitive (WorldMeshBake.TerrainBandData: highest vertex per node), so the
    cover vertices on grid nodes lifted the lowered terrain back up (cliff across the portals, pyramids at the walls)."""
    class Buf:
        def __init__(self):
            self.parts = []

        def add(self, layer, mat, V, UV, T, src="", **kw):
            self.parts.append((layer, mat, src, V, T))

    z = np.full((12, 14), 5.0)
    grid = TN.Grid(_HF, z)
    cells = np.zeros_like(z, bool)
    cells[3:6, 3:6] = True
    K = shapely.box(_HF.x0 + 3.2, _HF.y1 - 5.5, _HF.x0 + 5.4, _HF.y1 - 3.3)
    buf = Buf()
    n = TN._emit_cover(buf, grid, z, cells, K, [])
    assert n > 0 and len(buf.parts) == 1
    layer, mat, src, V, T = buf.parts[0]
    assert layer == "bridge" and mat == "verge_grass"
    assert not src.endswith(":vg")                 # build_world._is_verge: merged into the terrain
    a, b, c = V[T[:, 0], :2], V[T[:, 1], :2], V[T[:, 2], :2]
    area = float(np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])).sum() / 2)
    assert abs(area - K.area) < 1e-6
