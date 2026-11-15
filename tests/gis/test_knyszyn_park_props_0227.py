"""Park-prop placement and geometry contract, not visual acceptance."""
from pathlib import Path

import numpy as np
from shapely.geometry import MultiPoint
import yaml

from streetscape import knyszyn_park_props_0227 as props

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
    assert r["eagle"]=="omitted" and r["lighting"]=="no dynamic emission"
    assert len(r["benches"]) == 8 and len(r["lamps"]) == 5 and not r["refused"]
    assert all(1.2 <= x["distance_to_path_m"] <= 5.0 for x in r["benches"]+r["lamps"])
    assert {p[0] for p in buf.parts}==set(props.LAYERS) | {"collision"}
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
