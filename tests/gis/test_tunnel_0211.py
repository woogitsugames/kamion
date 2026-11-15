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


def test_inside_the_tunnel_no_grass_verge_and_no_rule_guardrail():
    """r4 renders (tunnel_eb_inside): a grass verge under the slab and an 8 m W-beam stub of the "beside a structure"
    rule between the tunnel walls; Mapillary 111496044347413 / 1142430022898855: paved ledge at the walls. Under the
    slab: side rows of the tunnel carriageway -> paving (visual + collision), rule guardrails dropped; in the walled cut
    outside the slab: only the side facing the wall is paved; outside the cut, above the soffit, ":vg" strips and other
    chains: untouched."""
    from types import SimpleNamespace as NS
    from roads.meshing import MeshBuf

    def quad(x0, z):
        V = np.array([[x0, 0, z], [x0 + 2, 0, z], [x0 + 2, 2, z], [x0, 2, z]], float)
        return V, V[:, :2].copy(), np.array([[0, 1, 2], [0, 2, 3]])

    cid = "c:w1:1-2"
    g = {"F": shapely.box(0, -5, 20, 5), "zroad": lambda q: 100.0, "clear": 4.7,
         "runs": [{"c": NS(id=cid), "inner": {"L": False, "R": True}}]}
    cut = shapely.box(0, -5, 60, 5)
    buf = MeshBuf()
    buf.add("road", "verge_grass", *quad(5, 99.8), src=cid + ":L:3")                 # under the slab: paved
    buf.add("road", "shoulder_gravel", *quad(5, 99.9), src=cid + ":R:2")             # under the slab, inner side: paved
    buf.add("collision", "collision_grass", *quad(5, 99.8), src=cid + ":L:3")        # its collision surface too
    buf.add("road", "verge_grass", *quad(40, 99.8), src=cid + ":L:3")                # walled cut, outer side: paved
    buf.add("road", "verge_grass", *quad(40, 99.7), src=cid + ":R:3")                # walled cut, median side: stays
    buf.add("road", "verge_grass", *quad(80, 99.8), src=cid + ":L:3")                # outside the cut: stays
    buf.add("road", "verge_grass", *quad(5, 99.8), src="c:w9:8-9:L:3")               # another chain: stays
    buf.add("road", "verge_grass", *quad(5, 99.9), src=cid + ":R:vg")                # merged-into-terrain skirt: stays
    buf.add("road", "curb_concrete", *quad(5, 100.1), src=cid + ":L:1")              # kerb: stays
    buf.add("bridge", "barrier_steel", *quad(8, 100.5), src=cid + ":L:structure")    # under the slab: dropped
    buf.add("collision", "collision_steel", *quad(8, 100.5), src=cid + ":L:structure")
    buf.add("bridge", "barrier_steel", *quad(8, 106.0), src=cid + ":L:structure")    # above the soffit: stays
    buf.add("bridge", "barrier_steel", *quad(40, 100.5), src=cid + ":L:median")      # outside the slab: stays
    rep = TN._dress_inside(NS(buf=buf), [g], cut)
    assert rep == {"side_paved_tris": 6, "side_paved_collision_tris": 2, "guardrail_tris": 2, "guardrail_collision_tris": 2}
    got = sorted((p.layer, p.mat, p.src, float(p.V[p.T].mean((0, 1))[0]), float(p.V[:, 2].max())) for p in buf.parts)
    assert got == sorted([
        ("road", "sidewalk_paving", cid + ":L:3:tunnel", 6.0, 99.8),
        ("road", "sidewalk_paving", cid + ":R:2:tunnel", 6.0, 99.9),
        ("collision", "collision_paving", cid + ":L:3:tunnel", 6.0, 99.8),
        ("road", "sidewalk_paving", cid + ":L:3:tunnel", 41.0, 99.8),
        ("road", "verge_grass", cid + ":R:3", 41.0, 99.7),
        ("road", "verge_grass", cid + ":L:3", 81.0, 99.8),
        ("road", "verge_grass", "c:w9:8-9:L:3", 6.0, 99.8),
        ("road", "verge_grass", cid + ":R:vg", 6.0, 99.9),
        ("road", "curb_concrete", cid + ":L:1", 6.0, 100.1),
        ("bridge", "barrier_steel", cid + ":L:structure", 9.0, 106.0),
        ("bridge", "barrier_steel", cid + ":L:median", 41.0, 100.5),
    ])
