"""Park-prop placement and geometry contract, not visual acceptance."""
from pathlib import Path

import numpy as np
from shapely.geometry import MultiPoint, Polygon
import yaml

from streetscape import knyszyn_park_props_0227 as props
from streetscape import paved
from streetscape.buildings_mesh import Acc

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = [761611, 612607]


class Buffer:
    def __init__(self): self.parts=[]
    def add(self, layer, mat, vertices, uv, triangles, src, UV1=None):
        self.parts.append((layer,mat,np.asarray(vertices),np.asarray(triangles),src))


def terrain(e,n): return np.zeros_like(e)+125.


def test_opt_in_and_missing_paths_are_safe():
    buf=Buffer(); r=props.build(buf,"knyszyn-w",ORIGIN,[],terrain,{})
    assert r["status"]=="skipped" and not buf.parts
    buf=Buffer(); r=props.build(buf,"knyszyn",ORIGIN,[],terrain,{})
    assert r["status"]=="applied" and not r["benches"] and not r["lamps"]
    assert len(r["refused"])==len(props.BENCHES)+len(props.LAMPS)


def test_anchors_clear_current_paths_and_geometry_is_finite():
    overrides=yaml.safe_load((ROOT/"Data/Regions/knyszyn/overrides.yaml").read_text(encoding="utf8"))["overrides"]
    buf=Buffer(); r=props.build(buf,"knyszyn",ORIGIN,overrides,terrain,{})
    assert r["king_silhouette"]=="PROXY_NOT_APPROVED"
    assert r["eagle"]=="PROXY_NOT_APPROVED" and r["lighting"]=="no dynamic emission"
    assert len(r["benches"]) == 8 and len(r["lamps"]) == 5 and not r["refused"]
    assert all(1.2 <= x["distance_to_path_m"] <= 5.0 for x in r["benches"]+r["lamps"])
    assert {p[0] for p in buf.parts}==set(props.LAYERS) | {"collision"}
    low = {p[1] for p in buf.parts if p[0] == "buildings_low"}
    assert not low & {"bench_wood", "paint_white_reflective", "plinth_grey", "steel_painted", "plaster_white"}
    assert {"bench_wood", "steel_painted"} <= {p[1] for p in buf.parts if p[0] == "buildings"}
    for layer,mat,v,t,src in buf.parts:
        assert np.isfinite(v).all() and t.min()>=0 and t.max()<len(v)
        assert (np.linalg.norm(np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]]),axis=1)>1e-9).all()
        assert src==props.ASSET_ID


def test_collision_boxes_are_separate_from_lods_and_do_not_block_paths():
    overrides=yaml.safe_load((ROOT/"Data/Regions/knyszyn/overrides.yaml").read_text(encoding="utf8"))["overrides"]
    buf=Buffer(); r=props.build(buf,"knyszyn",ORIGIN,overrides,terrain,{})
    assert len(r["benches"])==8 and len(r["lamps"])==5
    col={mat:(v,t) for layer,mat,v,t,src in buf.parts if layer=="collision"}
    assert set(col)=={"collision_steel","collision_building"}
    # Five faces per box: mast + eight benches + five lamps; obelisk + king + sundial.
    assert len(col["collision_steel"][1])==14*10
    assert len(col["collision_building"][1])==3*10
    paved=props._paved(overrides,np.asarray(ORIGIN,float))
    vertices=col["collision_steel"][0]
    assert len(vertices)==14*20
    for start in range(0,len(vertices),20):
        footprint=MultiPoint(vertices[start:start+20,:2]).convex_hull
        assert footprint.disjoint(paved), footprint.intersection(paved).area


def test_terrain_nan_drops_objects_without_writing_invalid_mesh():
    buf=Buffer()
    r=props.build(buf,"knyszyn",ORIGIN,[],lambda e,n: np.full_like(e,np.nan),{})
    assert not buf.parts and len(r["refused"])==3+len(props.BENCHES)+len(props.LAMPS)


def test_king_proxy_has_crowned_head_and_cheaper_low_geometry():
    outputs = {}
    for layer in props.LAYERS:
        acc = Acc()
        props._king(acc, layer, [0., 0.], 0.)
        buf = Buffer()
        acc.flush(buf, props.ASSET_ID)
        outputs[layer] = sum(len(p[3]) for p in buf.parts)
        figure = next(p for p in buf.parts if p[1] == "steel_painted")
        vertices, tris = figure[2], figure[3]
        assert np.isfinite(vertices).all()
        assert (np.linalg.norm(np.cross(vertices[tris[:,1]]-vertices[tris[:,0]],
                                        vertices[tris[:,2]]-vertices[tris[:,0]]), axis=1) > 1e-9).all()
        # Head and three separated crown tips make this a figure rather than a pillar.
        assert np.isclose(vertices[:,2].max(), 3.39)
        tips = vertices[np.isclose(vertices[:,2], 3.39), :2] @ props.KING_TANGENT
        assert np.any(tips < -.1) and np.any(np.abs(tips) < .05) and np.any(tips > .1)
        # Arms extend forward and to both sides above the pedestal.
        arms = vertices[(vertices[:,2] > 1.7) & (vertices[:,2] < 2.7) &
                        ((vertices[:,:2] @ props.KING_FORWARD) > .3)]
        sides = arms[:,:2] @ props.KING_TANGENT
        assert sides.min() < -.4 and sides.max() > .4
    assert outputs["buildings"] > outputs["buildings_low"]
    assert outputs["buildings"] <= 200 and outputs["buildings_low"] <= 160


def test_memorial_forecourt_and_sundial_face_town_hall():
    ovs=yaml.safe_load((ROOT/"Data/Regions/knyszyn/overrides.yaml").read_text(encoding="utf8"))["overrides"]
    buf=Buffer(); r=props.build(buf,"knyszyn",ORIGIN,ovs,terrain,{})
    assert r["king_plaza"] == "authored_paved_area"
    plaza=Polygon(np.asarray(props.KING_PLAZA_EPSG2180)-ORIGIN).buffer(1e-7)
    assert not [p for p in buf.parts if p[0]=="paved"]
    item=next(o for o in ovs if o.get("id")=="rynek-king-plaza-0227")
    assert item["park_flush"] is True and item["material"]=="yard_paving"
    assert Polygon(np.asarray(item["polygon_epsg2180"])-ORIGIN).equals_exact(
        Polygon(np.asarray(props.KING_PLAZA_EPSG2180)-ORIGIN),1e-7)
    src={"osm":{"areas":[]},"bdot10k":{"OT_PTPL_A":[],"OT_KUKO_A":[],"OT_SKRP_L":[]}}
    candidates=paved.collect(src,np.asarray(ORIGIN),[item],[],Polygon(),None,{})
    assert len(candidates)==1 and candidates[0]["park_flush"] is True
    assert candidates[0]["mat"]=="yard_paving" and candidates[0]["poly"].area>100
    # Third building-collision box is the separate sundial, aimed towards the
    # hall. Its centre must coincide with the visible block, not the old -N position.
    col=next(p for p in buf.parts if p[0]=="collision" and p[1]=="collision_building")
    center=col[2][40:60,:2].mean(axis=0)
    wanted=np.asarray(props.KING)-ORIGIN+props.KING_FORWARD*props.KING_BLOCK_DISTANCE_M
    assert np.allclose(center,wanted)
    assert plaza.covers(MultiPoint(col[2][40:60,:2]).convex_hull)


def test_proxy_bird_and_sundial_are_on_monuments_and_double_sided():
    for layer in props.LAYERS:
        acc=Acc(); props._obelisk(acc,layer,[0.,0.],0.)
        bird=acc.d[(layer,"steel_painted")][-1]
        v,t=bird[:2]
        assert v[:,2].min() >= 3.2 and v[:,2].max() <= 3.5
        assert len(t)==4 and np.isclose(np.ptp(v[:,0]),.64)
        assert np.allclose(np.cross(v[t[0,1]]-v[t[0,0]],v[t[0,2]]-v[t[0,0]]),
                           -np.cross(v[t[2,1]]-v[t[2,0]],v[t[2,2]]-v[t[2,0]]))
        acc=Acc(); props._king(acc,layer,[0.,0.],0.)
        disc,gnomon=acc.d[(layer,"steel_painted")][-2:]
        dv,dt=disc[:2]; gv,gt=gnomon[:2]
        expected=props.KING_FORWARD*props.KING_BLOCK_DISTANCE_M
        assert len(dt)==8 and np.allclose(dv[:,2],.758)
        assert np.allclose(dv[0,:2],expected)
        assert len(gt)==2 and np.allclose(gv[:2,2],.762) and np.isclose(gv[2,2],.96)

