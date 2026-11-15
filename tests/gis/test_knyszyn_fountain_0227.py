"""Dry fountain geometry contract; dynamic jets and visual QA remain open."""
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon
import yaml

from streetscape import knyszyn_fountain_0227 as fountain

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = np.array([761611., 612607.])


class Buffer:
    def __init__(self): self.parts = []
    def add(self, layer, mat, vertices, uv, triangles, src, UV1=None):
        self.parts.append((layer, mat, np.asarray(vertices), np.asarray(triangles), src))


def overrides():
    return yaml.safe_load((ROOT/"Data/Regions/knyszyn/overrides.yaml").read_text(encoding="utf8"))["overrides"]


def flat(e,n): return np.zeros_like(e)+125.


def test_dry_features_stay_inside_real_paved_plate_and_are_near_flush():
    ovs=overrides(); buf=Buffer(); report={}
    r=fountain.build(buf,"knyszyn",ORIGIN,ovs,flat,report)
    plate=next(o for o in ovs if o.get("id")==fountain.PLATE_ID)
    outline=Polygon(np.asarray(plate["polygon_epsg2180"])-ORIGIN).buffer(1e-7)
    assert r["status"]=="applied" and r["nozzle_count"]==9
    assert r["water_jets"]=="OPEN" and "dry" in r["summer_behavior"]
    assert not r["basin"] and not r["collision"] and r["triangles"]<=150
    assert {p[0] for p in buf.parts}=={"paved"}
    assert {p[1] for p in buf.parts}=={"plinth_dark","steel_painted"}
    for layer,mat,v,t,src in buf.parts:
        assert np.allclose(v[:,2],125.+fountain.OFFSET_M)
        assert np.isfinite(v).all() and t.min()>=0 and t.max()<len(v)
        for tri in t:
            assert outline.covers(Polygon(v[tri,:2]))
        assert src==fountain.ASSET_ID


def test_no_false_jet_geometry_or_wrong_region():
    buf=Buffer(); r=fountain.build(buf,"knyszyn-w",ORIGIN,overrides(),flat,{})
    assert r["status"]=="skipped" and r["water_jets"]=="OPEN" and not buf.parts
    buf=Buffer(); r=fountain.build(buf,"knyszyn",ORIGIN,[],flat,{})
    assert r["status"]=="skipped" and "plate" in r["reason"] and not buf.parts


def test_invalid_surface_heights_do_not_create_partial_geometry():
    buf=Buffer()
    r=fountain.build(buf,"knyszyn",ORIGIN,overrides(),lambda e,n:np.full_like(e,np.nan),{})
    assert r["status"]=="skipped" and "heights" in r["reason"] and not buf.parts
