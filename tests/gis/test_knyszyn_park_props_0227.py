"""Park-prop placement and geometry contract, not visual acceptance."""
from pathlib import Path

import numpy as np
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
    assert r["benches"] and r["lamps"]
    assert all(1.2 <= x["distance_to_path_m"] <= 5.0 for x in r["benches"]+r["lamps"])
    assert {p[0] for p in buf.parts}==set(props.LAYERS)
    for layer,mat,v,t,src in buf.parts:
        assert np.isfinite(v).all() and t.min()>=0 and t.max()<len(v)
        assert (np.linalg.norm(np.cross(v[t[:,1]]-v[t[:,0]],v[t[:,2]]-v[t[:,0]]),axis=1)>1e-9).all()
        assert src==props.ASSET_ID


def test_terrain_nan_drops_objects_without_writing_invalid_mesh():
    buf=Buffer()
    r=props.build(buf,"knyszyn",ORIGIN,[],lambda e,n: np.full_like(e,np.nan),{})
    assert not buf.parts and len(r["refused"])==3+len(props.BENCHES)+len(props.LAMPS)
