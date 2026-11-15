"""Blender-free checks of the opt-in willow study, not visual acceptance."""
import ast
import math
from pathlib import Path
import random

import numpy as np
import pytest

SCRIPT = Path(__file__).resolve().parents[2]/"tools/blender/world/make_trees.py"


def isolated():
    tree=ast.parse(SCRIPT.read_text(encoding="utf8"))
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ("willow_leaf_atlas","willow_blueprint","grow_willow")]
    assert len(selected)==3
    module=ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[]))
    ns={"np":np,"math":math,"random":random,"Vector":lambda p:np.asarray(p,float)}
    exec(compile(module,str(SCRIPT),"exec"),ns)
    return ns


class Geometry:
    def __init__(self): self.tubes=[]; self.cards=[]
    def tube(self,mat,points,radii,seg): self.tubes.append((mat,np.asarray(points),radii,seg))
    def quad(self,mat,a,b,c,d,uvs,n): self.cards.append((mat,np.asarray([a,b,c,d]),np.asarray(n)))


def test_blueprint_is_deterministic_drooping_and_ground_clear():
    make=isolated()["willow_blueprint"]
    a=make(13.5,0); b=make(13.5,0)
    assert len(a[0])==4 and len(a[1])==12 and len(a[2])==120
    for x,y in zip(a[2],b[2]):
        assert all(np.array_equal(i,j) for i,j in zip(x,y))
    starts=np.array([s[0] for s in a[2]]); ends=np.array([s[2] for s in a[2]])
    assert np.all(ends[:,2] < starts[:,2])
    assert np.all(ends[:,2] >= .12*13.5-1e-9)
    assert np.ptp(starts[:,0])>6 and np.ptp(starts[:,1])>6
    assert np.ptp(starts[:,2]-ends[:,2])>1.0  # irregular, not a uniform curtain
    with pytest.raises(ValueError): make(float("nan"),0)


def test_low_cards_are_exact_subset_and_use_existing_materials():
    grow=isolated()["grow_willow"]
    high,low=Geometry(),Geometry()
    grow(high,13.5,0,0); grow(low,13.5,0,1)
    assert len(high.tubes)==len(low.tubes)==13
    assert len(high.cards)==480 and len(low.cards)==240
    assert {m for m,*_ in high.tubes}=={"bark_linden"}
    assert {m for m,*_ in high.cards}=={"leaves_willow"}
    high_cards={tuple(v.ravel()) for m,v,n in high.cards}
    assert all(tuple(v.ravel()) in high_cards for m,v,n in low.cards)
    for mat,v,n in high.cards+low.cards:
        assert np.isfinite(v).all() and np.isfinite(n).all()
        assert np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))>1e-8
    def triangles(g):
        return sum((len(p)-1)*seg*2 for m,p,r,seg in g.tubes)+len(g.cards)*2
    assert triangles(low)<triangles(high)


def test_willow_leaf_atlas_is_deterministic_transparent_and_sparse():
    make=isolated()["willow_leaf_atlas"]
    a=make(); b=make()
    assert a.shape==(256,256,4) and a.dtype==np.uint8 and np.array_equal(a,b)
    alpha=a[:,:,3]
    assert (alpha[:,:8]==0).all() and (alpha[:,-8:]==0).all()
    assert .04 < np.count_nonzero(alpha)/alpha.size < .30
    with pytest.raises(ValueError): make(32)


def test_export_registration_is_explicitly_opt_in():
    source=SCRIPT.read_text(encoding="utf8")
    tree=ast.parse(source)
    assigned={target.id:ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign)
              for target in node.targets if isinstance(target,ast.Name) and target.id in ("HREF","NVAR","NEW_SPECIES")}
    assert assigned["HREF"]["willow"]==13.5 and assigned["NVAR"]["willow"]==1
    assert "willow" not in assigned["NEW_SPECIES"]
    assert '"--include-willow" in argv or quick == "tree_willow_0"' in source
    assert 'NEW_SPECIES + experimental' in source
    assert 'sp not in NEW_SPECIES and sp != "willow"' in source
