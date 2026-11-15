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
    selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in
              ("willow_leaf_tile","willow_leaf_atlas","willow_card_uv","willow_blueprint","grow_willow","willow_open_radius")]
    assert len(selected)==6
    module=ast.fix_missing_locations(ast.Module(body=selected,type_ignores=[]))
    ns={"np":np,"math":math,"random":random,"Vector":lambda p:np.asarray(p,float)}
    exec(compile(module,str(SCRIPT),"exec"),ns)
    return ns


class Geometry:
    def __init__(self): self.tubes=[]; self.cards=[]
    def tube(self,mat,points,radii,seg): self.tubes.append((mat,np.asarray(points),radii,seg))
    def quad(self,mat,a,b,c,d,uvs,n): self.cards.append((mat,np.asarray([a,b,c,d]),np.asarray(n),np.asarray(uvs)))


def test_blueprint_is_deterministic_drooping_and_ground_clear():
    make=isolated()["willow_blueprint"]
    a=make(13.5,0); b=make(13.5,0)
    assert len(a[0])==4 and len(a[1])==12 and len(a[2])==120
    for x,y in zip(a[2],b[2]):
        assert all(np.array_equal(i,j) for i,j in zip(x,y))
    starts=np.array([s[0] for s in a[2]]); ends=np.array([s[2] for s in a[2]])
    assert np.all(ends[:,2] < starts[:,2])
    assert np.all(ends[:,2] >= .09*13.5-1e-9)
    assert len(np.unique(np.round(ends[:,2],4)))>110  # no repeated flat hem
    assert np.ptp(starts[:,0])>6 and np.ptp(starts[:,1])>6
    assert np.ptp(starts[:,2]-ends[:,2])>1.0  # irregular, not a uniform curtain
    with pytest.raises(ValueError): make(float("nan"),0)


def test_low_cards_are_exact_subset_and_use_existing_materials():
    grow=isolated()["grow_willow"]
    high,low=Geometry(),Geometry()
    grow(high,13.5,0,0); grow(low,13.5,0,1)
    assert len(high.tubes)==len(low.tubes)==13
    assert len(high.cards)==528 and len(low.cards)==264
    assert {m for m,*_ in high.tubes}=={"bark_linden"}
    assert {m for m,*_ in high.cards}=={"leaves_willow"}
    high_cards={(tuple(v.ravel()),tuple(uv.ravel())) for m,v,n,uv in high.cards}
    assert all((tuple(v.ravel()),tuple(uv.ravel())) in high_cards for m,v,n,uv in low.cards)
    for mat,v,n,uv in high.cards+low.cards:
        assert np.isfinite(v).all() and np.isfinite(n).all()
        assert np.linalg.norm(np.cross(v[1]-v[0],v[2]-v[0]))>1e-8
    def triangles(g):
        return sum((len(p)-1)*seg*2 for m,p,r,seg in g.tubes)+len(g.cards)*2
    assert triangles(low)<triangles(high)


def test_willow_leaf_atlas_is_deterministic_transparent_and_sparse():
    make=isolated()["willow_leaf_atlas"]
    a=make(); b=make()
    assert a.shape==(512,512,4) and a.dtype==np.uint8 and np.array_equal(a,b)
    alpha=a[:,:,3]
    tiles=[alpha[y:y+256,x:x+256] for y in (0,256) for x in (0,256)]
    assert all((q[:,:8]==0).all() and (q[:,-8:]==0).all() for q in tiles)
    assert all((q[:8,:]==0).all() and (q[-8:,:]==0).all() for q in tiles)
    assert .15 < np.count_nonzero(alpha>=128)/alpha.size < .32
    assert all(not np.array_equal(tiles[0],q) for q in tiles[1:])
    with pytest.raises(ValueError): make(32)


def test_upper_foliage_follows_branches_and_opening_is_willow_only():
    ns=isolated(); high=Geometry(); ns["grow_willow"](high,13.5,0,0)
    # First 48 foliage cards follow the 12 arching structural limbs; they are
    # not additional vertical tubes or independent circular crown puffs.
    upper=high.cards[:48]
    assert len(upper)==48
    directions=np.array([v[2]-v[1] for _,v,_,_ in upper])
    assert (np.linalg.norm(directions[:,:2],axis=1)>1.0).all()
    uv_sets={tuple(uv.ravel()) for _,_,_,uv in high.cards}
    assert len(uv_sets)>=8  # four tiles plus mirrored orientations, no new materials
    assert ns["willow_open_radius"]([])==1
    assert ns["willow_open_radius"](["--willow-open-radius","0"])==0
    assert ns["willow_open_radius"](["--willow-open-radius","1"])==1
    with pytest.raises(ValueError): ns["willow_open_radius"](["--willow-open-radius","2"])
    source=SCRIPT.read_text(encoding="utf8")
    assert 'willow_open if sp == "willow" else (0 if sp in ("pine", "spruce", "pineyoung") else 1)' in source


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
