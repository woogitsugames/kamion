from types import SimpleNamespace
import numpy as np

from streetscape import bus_stop_wear as B
from streetscape import sources as S


def part(layer, material, vertices, triangles):
    return SimpleNamespace(layer=layer, mat=material, V=np.asarray(vertices, float), T=np.asarray(triangles, int))


class Buffer:
    def __init__(self, road=True, oil=True):
        self.parts = []
        if road:
            self.parts.append(part("road", "road_asphalt", [(0,-20,0),(20,-20,.2),(0,0,0),(20,0,.2)], [(0,1,2),(1,3,2)]))
        if oil:
            self.parts.append(part("markings", "decal_oil", [(2,-3,0),(3,-3,0),(2,-2,0)], [(0,1,2)]))

    def add(self, layer, material, vertices, uv, triangles, src=None, UV1=None):
        p=part(layer, material, vertices, triangles)
        p.UV=np.asarray(uv);p.UV1=np.asarray(UV1);p.src=src
        self.parts.append(p)


def stop(**kwargs):
    return dict(osm_node=2367445386, ref="464", bus="yes", local_en=kwargs.get("center", [10,-10]), half_m=1024)


def test_one_reviewed_source_stain_is_deterministic_draped_and_preserves_road():
    a,b=Buffer(),Buffer();road=a.parts[0].V.copy()
    first=B.emit(a,[stop()],{});second=B.emit(b,[stop()],{})
    assert first==second and len(first["applied"])==1
    added=a.parts[-1]
    assert len(added.V)==10 and len(added.T)==9 and added.mat=="decal_oil"
    assert np.allclose(added.V[:,2],added.V[:,0]*.01+.0035,atol=1e-10)
    assert np.array_equal(a.parts[0].V,road)
    assert first["applied"][0]["new_source_material_groups"]==0
    assert first["applied"][0]["working_value"] is True
    assert np.isfinite(added.UV).all() and np.isfinite(added.UV1).all()


def test_unreviewed_stop_never_projects_every_platform_to_a_stain():
    buf=Buffer();s=stop();s["osm_node"]=999
    result=B.emit(buf,[s],{})
    assert not result["applied"] and result["rejected"][0]["reason"]=="no_reviewed_bay_photo"
    assert len(buf.parts)==2


def test_footway_is_not_driveable_asphalt():
    buf=Buffer();buf.parts[0].mat="sidewalk_paving"
    result=B.emit(buf,[stop()],{})
    assert not result["applied"] and result["rejected"][0]["reason"]=="outside_driveable_asphalt"


def test_missing_existing_chunk_oil_rejects_new_draw_group():
    result=B.emit(Buffer(oil=False),[stop()],{})
    assert not result["applied"] and result["rejected"][0]["reason"]=="would_add_material_group"


def test_overlapping_road_levels_reject_instead_of_highest_surface():
    buf=Buffer();other=part("road","road_asphalt",buf.parts[0].V+[0,0,2],buf.parts[0].T);buf.parts.append(other)
    result=B.emit(buf,[stop()],{})
    assert not result["applied"] and result["rejected"][0]["reason"]=="ambiguous_road_levels"


def test_whole_fan_not_just_stop_center_needs_road_support():
    buf=Buffer();buf.parts[0]=part("road","road_asphalt",[(9.95,-10.05,0),(10.05,-10.05,0),(10.05,-9.95,0),(9.95,-9.95,0)],[(0,1,2),(0,2,3)])
    result=B.emit(buf,[stop()],{})
    assert not result["applied"] and result["rejected"][0]["reason"]=="outside_driveable_asphalt"
    assert len(buf.parts)==2


def test_stain_never_covers_existing_paint():
    buf=Buffer();buf.parts.append(part("markings","marking_white",[(9,-11,.006),(11,-11,.006),(10,-9,.006)],[(0,1,2)]))
    result=B.emit(buf,[stop()],{})
    assert not result["applied"] and result["rejected"][0]["reason"]=="paint_overlap_or_invalid_polygon"


def test_source_selector_retains_on_road_stop_and_bus_identity():
    assert S._match({"public_transport":"stop_position","bus":"yes"},S.OSM_NODE_KEYS)
    assert not S._match({"public_transport":"platform"},S.OSM_NODE_KEYS)
    assert S._tags({"public_transport":"stop_position","bus":"yes","ref":"464"})["bus"]=="yes"
