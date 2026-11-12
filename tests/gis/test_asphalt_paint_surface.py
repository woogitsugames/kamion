"""Fresh paint classification must follow the actual road level, with no road/paint geometry changes."""
import numpy as np

from roads.meshing import MeshBuf
from streetscape.yard_wear import mark_fresh_road_paint, mark_traffic_oil_strength


def road(buf, material, z=0, x0=0, x1=10):
    p = [[x0,0,z], [x1,0,z], [x1,4,z], [x0,4,z]]
    buf.add("road", material, p, np.zeros((4,2)), [[0,1,2], [0,2,3]])


def paint(buf, x0=2, x1=3, z=.006, exposure=2.4):
    p = [[x0,1,z], [x1,1,z], [x1,3,z], [x0,3,z]]
    buf.add("markings", "marking_white", p, np.zeros((4,2)), [[0,1,2], [0,2,3]],
            UV1=np.tile([.26, exposure], (4,1)))
    return buf.parts[-1]


def test_fresh_surface_preserves_fractional_age_lane_and_geometry():
    buf=MeshBuf(); road(buf,"road_asphalt_new"); p=paint(buf)
    positions,triangles=p.V,p.T
    before=p.UV1.copy()
    assert mark_fresh_road_paint(buf,True)["fresh_parts"] == 1
    np.testing.assert_allclose(p.UV1[:,1],6.4)
    np.testing.assert_allclose(np.mod(p.UV1[:,1],1),np.mod(before[:,1],1),atol=1e-12)
    np.testing.assert_array_equal(p.UV1[:,0],before[:,0])
    assert p.V is positions and p.T is triangles
    first=p.UV1.copy(); mark_fresh_road_paint(buf,True)
    np.testing.assert_array_equal(p.UV1,first)


def test_fresh_overpass_does_not_reclassify_old_road_below():
    buf=MeshBuf(); road(buf,"road_asphalt"); road(buf,"road_asphalt_new",z=5); p=paint(buf)
    before=p.UV1
    assert mark_fresh_road_paint(buf,True)["fresh_parts"] == 0
    assert p.UV1 is before


def test_fresh_road_above_an_old_underpass_is_supported():
    buf=MeshBuf(); road(buf,"road_asphalt",z=-5); road(buf,"road_asphalt_new"); paint(buf)
    assert mark_fresh_road_paint(buf,True)["fresh_parts"] == 1


def test_mixed_and_coplanar_ambiguous_surfaces_stay_unchanged():
    for overlap in (False,True):
        buf=MeshBuf(); road(buf,"road_asphalt_new",x1=10 if overlap else 2.5)
        road(buf,"road_asphalt",x0=0 if overlap else 2.5)
        p=paint(buf); before=p.UV1
        assert mark_fresh_road_paint(buf,True)["fresh_parts"] == 0
        assert p.UV1 is before


def test_disabled_and_no_data_contracts_stay_exact():
    buf=MeshBuf(); road(buf,"road_asphalt_new"); p=paint(buf)
    before=p.UV1
    assert mark_fresh_road_paint(buf,False)["fresh_parts"] == 0
    assert p.UV1 is before
    p.UV1[:]=[-1,5]; before=p.UV1
    assert mark_fresh_road_paint(buf,True)["fresh_parts"] == 0
    assert p.UV1 is before


def test_traffic_oil_strength_does_not_change_private_yard_or_bus_stains():
    buf=MeshBuf()
    for src in ("oil:j:test:0:0:0", "wear:kwadrat:oil:1", "bus_stop:464:oil"):
        buf.add("markings","decal_oil",[[0,0,0],[1,0,0],[0,1,0]],[[0,0],[1,0],[0,1]],[[0,1,2]],
                src=src,UV1=np.tile([0,.7],(3,1)))
    geometry=[(p.V,p.T) for p in buf.parts]
    assert mark_traffic_oil_strength(buf,1.15) == 1
    np.testing.assert_array_equal(buf.parts[0].UV1[:,0],1.15)
    for p in buf.parts[1:]:
        np.testing.assert_array_equal(p.UV1[:,0],0)
    for p,(positions,triangles) in zip(buf.parts,geometry):
        assert p.V is positions and p.T is triangles
        np.testing.assert_array_equal(p.UV1[:,1],.7)
