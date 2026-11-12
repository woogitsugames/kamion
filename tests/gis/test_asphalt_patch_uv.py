"""Repair perimeter UVs must not alter road/yard geometry or create seams at chunk cuts (ADR0118)."""
import numpy as np

from roads.meshing import MeshBuf
from streetscape.yard_wear import normalize_asphalt_patch_uvs


def patch(buf, material="decal_patch"):
    points = np.array([[0, 0, 0], [8, 0, 0], [8, 2, 0], [0, 2, 0]], float)
    uv = np.array([[0, 0], [8, 0], [8, 2], [0, 2]], float)
    buf.add("markings", material, points, uv, [[0, 1, 2], [0, 2, 3]],
            UV1=np.tile([.4, .7], (4, 1)))
    return buf.parts[-1]


def test_asphalt_patch_uv_preserves_topology_age_and_chunk_continuity():
    buf = MeshBuf()
    p = patch(buf)
    positions, triangles, age = p.V, p.T, p.UV1
    counts = normalize_asphalt_patch_uvs(buf, {"width_m": .025})
    assert counts == {"normalised": 1, "invalid_uv": 0}
    np.testing.assert_array_equal(p.UV, [[0, 0], [1, 0], [1, 1], [0, 1]])
    assert p.V is positions and p.T is triangles and p.UV1 is age
    # A world chunk cut halfway along the repair interpolates U=.5, not a new edge U=0 or U=1.
    cut_uv = .5 * (p.UV[0] + p.UV[1])
    assert cut_uv[0] == .5
    first = p.UV.copy()
    normalize_asphalt_patch_uvs(buf, {"width_m": .025})
    np.testing.assert_array_equal(p.UV, first)


def test_patch_uv_flag_off_and_yard_material_remain_exact():
    buf = MeshBuf()
    road = patch(buf)
    yard = patch(buf, "decal_yard_patch_dark")
    original_road, original_yard = road.UV, yard.UV
    assert normalize_asphalt_patch_uvs(buf, {})["normalised"] == 0
    assert road.UV is original_road
    normalize_asphalt_patch_uvs(buf, {"width_m": .025})
    assert yard.UV is original_yard


def test_degenerate_uv_does_not_generate_invalid_shader_coordinates():
    buf = MeshBuf()
    p = patch(buf)
    p.UV[:] = 0
    original = p.UV
    assert normalize_asphalt_patch_uvs(buf, {"width_m": .025}) == {"normalised": 0, "invalid_uv": 1}
    assert p.UV is original


def test_material_table_enables_complete_patch_coordinates():
    buf = MeshBuf()
    p = patch(buf)
    assert normalize_asphalt_patch_uvs(buf)["normalised"] == 1
    np.testing.assert_array_equal(p.UV.max(axis=0), [1, 1])
