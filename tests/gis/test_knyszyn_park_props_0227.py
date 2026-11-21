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
    assert not low & {"bench_wood", "paint_white_reflective", "plinth_grey", "steel_painted", "plaster_white",
                       "monument_bronze", "monument_bronze_patina", "monument_bronze_rubbed", "monument_granite"}
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


def test_king_proxy_has_crowned_head_and_valid_geometry():
    # ADR 0325: sculpted bronze figure (faceted cloak, head, ruff, crown, lapels, chains) about 3.05 m on the 1.05 m
    # granite block (Commons photos of the monument + owner photos 1 / 8).
    from streetscape import knyszyn_king_0325 as KF
    outputs = {}
    for layer in props.LAYERS:
        acc = Acc()
        props._king(acc, layer, [0., 0.], 0.)
        buf = Buffer()
        acc.flush(buf, props.ASSET_ID)
        outputs[layer] = sum(len(p[3]) for p in buf.parts)
        bronze = [p for p in buf.parts if p[1].startswith("monument_bronze")]
        assert {p[1] for p in bronze} == {KF.BRONZE, KF.PATINA, KF.RUBBED}
        for _, _, vertices, tris, _ in bronze:
            assert np.isfinite(vertices).all()
            assert (np.linalg.norm(np.cross(vertices[tris[:,1]]-vertices[tris[:,0]],
                                            vertices[tris[:,2]]-vertices[tris[:,0]]), axis=1) > 1e-9).all()
        crown = next(p[2] for p in bronze if p[1] == KF.RUBBED)
        top = crown[:,2].max()
        assert 4.0 <= top <= props.KING_H + 1e-9
        # Crown fleurons all round the head, above every other part of the figure.
        tips = crown[crown[:,2] > top - .06, :2] @ props.KING_TANGENT
        assert np.any(tips < -.07) and np.any(tips > .07)
        assert max(p[2][:,2].max() for p in bronze if p[1] != KF.RUBBED) < top - .05
        assert {p[1] for p in buf.parts} >= {"monument_granite"}
    assert outputs["buildings_low"] <= 420 < 1800 <= outputs["buildings"] <= 3200


def test_king_figure_is_a_person_not_a_lathe():
    # ADR 0325 (CRITIC s24 wave 6, 1.3): the silhouette must not be a body of revolution.
    from streetscape import knyszyn_king_0325 as KF
    sc = KF.sculpt(False)
    cloak = sc.parts[KF.BRONZE][0][0]
    hem = cloak[np.isclose(cloak[:, 2], 0.30)]
    r = np.hypot(hem[:, 0], hem[:, 1])
    assert r.max() / r.min() > 1.25                       # faceted, elongated plan
    shoulders = cloak[np.isclose(cloak[:, 2], 2.30)]
    assert np.ptp(shoulders[:, 0]) < 0.66 * np.ptp(hem[:, 0])       # tapers to the shoulders
    assert np.ptp(hem[:, 0]) > 1.15 * np.ptp(hem[:, 1])             # wider than deep
    head = sc.parts[KF.BRONZE][1][0]
    assert 0.20 < np.ptp(head[:, 0]) < 0.30 and head[:, 2].min() >= 2.49
    # nose stands proud of the face; the beard hangs below the chin in front only
    nose = sc.parts[KF.BRONZE][2][0]
    assert nose[:, 1].max() > head[:, 1].max() + 0.03
    pat = np.concatenate([v for v, _ in sc.parts[KF.PATINA]])
    assert pat[:, 2].min() < 1.6                                    # fur lapels run down the chest
    # no arms: nothing of the figure reaches outside the cloak outline below the shoulders
    allv = np.concatenate([v for parts in sc.parts.values() for v, _ in parts])
    below = allv[allv[:, 2] < 2.3]
    assert np.abs(below[:, 0]).max() <= np.abs(cloak[:, 0]).max() + 1e-9
    low = KF.sculpt(True)
    assert low.tris() < 0.2 * sc.tris() and set(low.parts) == {KF.BRONZE, KF.PATINA, KF.RUBBED}


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
        bird,other=acc.d[(layer,"steel_painted")][-2:]
        v,t=bird[:2]
        assert v[:,2].min() >= 3.2 and v[:,2].max() <= 3.5
        assert len(t)==4 and np.isclose(np.ptp(v[:,0]),.64)
        assert np.allclose(np.cross(v[t[0,1]]-v[t[0,0]],v[t[0,2]]-v[t[0,0]]),
                           -np.cross(v[t[2,1]]-v[t[2,0]],v[t[2,2]]-v[t[2,0]]))
        ov,ot=other[:2]
        assert np.isclose(np.ptp(ov[:,1]),.64) and np.isclose(np.ptp(ov[:,0]),0.)
        n1=np.cross(v[t[0,1]]-v[t[0,0]],v[t[0,2]]-v[t[0,0]])
        n2=np.cross(ov[ot[0,1]]-ov[ot[0,0]],ov[ot[0,2]]-ov[ot[0,0]])
        assert np.isclose(n1@n2,0.)
        acc=Acc(); props._king(acc,layer,[0.,0.],0.)
        disc,gnomon=acc.d[(layer,"steel_painted")][-2:]
        dv,dt=disc[:2]; gv,gt=gnomon[:2]
        expected=props.KING_FORWARD*props.KING_BLOCK_DISTANCE_M
        assert len(dt)==8 and np.allclose(dv[:,2],.758)
        assert np.allclose(dv[0,:2],expected)
        assert len(gt)==2 and np.allclose(gv[:2,2],.762) and np.isclose(gv[2,2],.96)


def test_king_cloak_has_continuous_profile_and_crowned_head():
    from streetscape import knyszyn_king_0325 as KF
    acc=Acc(); props._king(acc,"buildings",[0.,0.],0.)
    pieces=acc.d[("buildings","monument_bronze")]
    n,m=len(KF.RINGS0),len(KF.COLS0)
    z0_uv=props.KING_PLINTH_H+props.KING_CAP_M
    # the cloak loft + copies of the vertices along the UV seam at the back (ADR 0325: cylindrical UV0 in metres)
    vertices,faces,uv=max(((v,t,uv) for v,t,uv,*_ in pieces), key=lambda p: len(p[0]))
    assert n*m+n <= len(vertices) <= n*m+2*n and np.ptp(uv[:,0]) > 2*np.pi*KF.UV_RADIUS_M*.95
    # no wall triangle is stretched across the seam (the cap under the ruff is a fan and does not count)
    wall=faces[(vertices[faces][:,:,2].min(axis=1) < vertices[:,2].max()-1e-6)]
    assert (np.ptp(uv[wall][:,:,0],axis=1) < 1.0).all() and np.allclose(uv[:,1],vertices[:,2]-z0_uv)
    vertices=vertices[:n*m]
    z0=props.KING_PLINTH_H+props.KING_CAP_M
    assert np.allclose(np.unique(np.round(vertices[:,2]-z0,6)),sorted(KF.RINGS0))
    width=lambda rows: np.ptp(rows[:,:2]@props.KING_TANGENT)
    depth=lambda rows: np.ptp(rows[:,:2]@props.KING_FORWARD)
    ring=lambda k: vertices[m*k:m*(k+1)]
    hem,shoulder,neck=ring(1),ring(KF.RINGS0.index(2.30)),ring(n-1)  # noqa
    # broad cloak: wider than deep, tapering to the shoulders, a neck much narrower than the shoulders
    assert 1.1 <= width(hem) <= 1.3 and 0.85 <= depth(hem) <= 1.1
    assert width(hem) > width(shoulder) > 2*width(neck)
    # every ring is a simple closed outline around the axis (no fold crosses another)
    for k in range(n):
        rel=ring(k)[:,:2]-ring(k)[:,:2].mean(0)
        ang=np.unwrap(np.arctan2(rel@props.KING_FORWARD,rel@props.KING_TANGENT))
        assert (np.diff(ang)>0).all() and ang[-1]-ang[0] < 2*np.pi
