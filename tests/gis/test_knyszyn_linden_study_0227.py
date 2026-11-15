"""Blender-free checks of isolated linden study; not visual acceptance."""
import ast
import math
from pathlib import Path
import random

import numpy as np
import pytest

from streetscape.foliage_policy import leaf_lod_indices

SCRIPT = Path(__file__).resolve().parents[2] / "tools/blender/world/make_trees.py"


def isolated():
    source=ast.parse(SCRIPT.read_text(encoding="utf8"))
    nodes=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in
           ("park_linden_blueprint","grow_park_linden", "park_linden_blueprint_r2", "grow_park_linden_r2")]
    assert len(nodes)==4
    ns={"np":np,"math":math,"random":random,"Vector":lambda p:np.asarray(p,float),
        "leaf_lod_indices":leaf_lod_indices}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(SCRIPT),"exec"),ns)
    return ns


class Geometry:
    def __init__(self): self.tubes=[]; self.cards=[]
    def tube(self,mat,points,radii,seg): self.tubes.append((mat,np.asarray(points),radii,seg))
    def card(self,mat,p,normal,up,size,crown): self.cards.append((mat,p,normal,up,size,crown))


def test_blueprint_is_deterministic_and_three_dimensional():
    make=isolated()["park_linden_blueprint"]
    a=make(13.5); b=make(13.5)
    assert len(a[1])==12 and len(a[2])==384
    assert all(np.array_equal(x[0],y[0]) and np.array_equal(x[1],y[1]) and x[2]==y[2]
               for x,y in zip(a[2],b[2]))
    centers=np.asarray([c[0] for c in a[2]])
    assert np.ptp(centers[:,0])>4 and np.ptp(centers[:,1])>4 and np.ptp(centers[:,2])>4
    with pytest.raises(ValueError): make(float("nan"))


def test_lod1_is_exact_subset_and_materials_are_existing():
    grow=isolated()["grow_park_linden"]; high=Geometry(); low=Geometry()
    grow(high,13.5,0,0); grow(low,13.5,0,1)
    assert len(high.cards)==384 and len(low.cards)==172
    assert {x[0] for x in high.cards+low.cards}=={"leaves_linden"}
    assert {x[0] for x in high.tubes+low.tubes}=={"bark_linden"}
    keys={(tuple(p),tuple(n),s) for _,p,n,up,s,c in high.cards}
    assert all((tuple(p),tuple(n),s) in keys for _,p,n,up,s,c in low.cards)
    def tris(g): return sum((len(p)-1)*seg*2 for _,p,_,seg in g.tubes)+2*len(g.cards)
    assert tris(high)==1056 and tris(low)==518


def test_study_is_opt_in_and_artifact_only():
    text=SCRIPT.read_text(encoding="utf8")
    assert '"--park-linden-study" in ARGV or "--park-linden-study-r2" in ARGV' in text
    assert 'study_dir.is_relative_to((REPO / "artifacts").resolve())' in text
    assert '"tree_linden_park_study_r2" if r2 else "tree_linden_park_study"' in text


def test_r2_lod1_preserves_all_sectors_and_height_bands():
    ns=isolated(); make=ns["park_linden_blueprint_r2"]; grow=ns["grow_park_linden_r2"]
    first=make(13.5); second=make(13.5)
    assert len(first[2])==12*6*8
    assert all(np.array_equal(a[0],b[0]) for a,b in zip(first[2],second[2]))
    high=Geometry(); low=Geometry(); grow(high,13.5,0,0); grow(low,13.5,0,1)
    assert len(high.cards)==576 and len(low.cards)==288
    for s in range(12):
        for band in range(6):
            block=first[2][(s*6+band)*8:(s*6+band+1)*8]
            low_keys={(tuple(p),tuple(n),size) for _,p,n,_,size,_ in low.cards}
            assert sum((tuple(p),tuple(n),size) in low_keys for p,n,size in block)==4
    points=np.asarray([p for p,_,_ in first[2]])
    assert np.ptp(points[:,0])>7 and np.ptp(points[:,1])>7 and np.ptp(points[:,2])>7
    def tris(g): return sum((len(p)-1)*seg*2 for _,p,_,seg in g.tubes)+2*len(g.cards)
    assert tris(high)==1440 and tris(low)==750
