"""Actual gate decal footprint, source preservation and pair-atomicity guards."""
from pathlib import Path
import importlib.util
import sys
from types import SimpleNamespace
import numpy as np
from shapely.geometry import box
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/worldgen'))
from streetscape import gate_wear as G

def part(layer,mat,v,t):return SimpleNamespace(layer=layer,mat=mat,V=np.asarray(v,float),T=np.asarray(t,int))
class Buffer:
 def __init__(self,tyre=True):
  self.parts=[part('road','road_asphalt',[(0,-20,0),(20,-20,.2),(0,0,0),(20,0,.2)],[(0,1,2),(1,3,2)])]
  if tyre:self.parts.append(part('markings','decal_tyre',[(2,-3,0),(3,-3,0),(2,-2,0)],[(0,1,2)]))
 def add(self,layer,mat,v,uv,t,UV1=None,src=None):
  p=part(layer,mat,v,t);p.UV=np.asarray(uv);p.UV1=np.asarray(UV1);p.src=src;self.parts.append(p)
class Line:
 def __init__(self,n=-10):self.n=n
 def frame(self,s):return np.array([1.,0.]),np.array([0.,1.])
 def offset_point(self,s,lat):return np.array([s,self.n+lat])
def cases(n=-10):return [dict(chain=SimpleNamespace(line=Line(n)),station=10.,travel=np.array([1.,0.]),name='entry',src='gate:verified-source')]

def test_supported_pair_is_deterministic_and_draped_without_road_changes():
 a,b=Buffer(),Buffer();road=a.parts[0].V.copy();x=G.emit(a,cases(),1024,[],{});y=G.emit(b,cases(),1024,[],{})
 assert x==y and len(x['applied'])==1 and not x['rejected']
 assert np.array_equal(a.parts[0].V,road)
 assert sum(len(p.T) for p in a.parts[2:])==32
 assert sum(len(p.V) for p in a.parts[2:])==36
 for p in a.parts[2:]:
  assert p.mat=='decal_tyre' and np.allclose(p.V[:,2],p.V[:,0]*.01+.005)
  assert np.isfinite(p.UV).all() and np.all(p.UV1[:,1]==.9)
  assert np.all(np.cross(p.V[p.T[:,1]]-p.V[p.T[:,0]],p.V[p.T[:,2]]-p.V[p.T[:,0]])[:,2]>0)
 assert x['applied'][0]['new_source_material_groups']==0

def test_island_clearance_rejects_entire_pair():
 b=Buffer();x=G.emit(b,cases(),1024,[box(6,-11,7,-10.7)],{})
 assert not x['applied'] and x['rejected'][0]['reason']=='kerb_island_clearance' and len(b.parts)==2

def test_full_footprint_support_not_only_center_is_required():
 b=Buffer();b.parts[0].V[:,0]=np.where(b.parts[0].V[:,0]==0,8,20)
 x=G.emit(b,cases(),1024,[],{})
 assert not x['applied'] and x['rejected'][0]['reason']=='whole_footprint_outside_asphalt' and len(b.parts)==2

def test_no_new_material_group_is_enforced():
 b=Buffer(tyre=False);x=G.emit(b,cases(),1024,[],{})
 assert not x['applied'] and x['rejected'][0]['reason']=='would_add_material_group' and len(b.parts)==1

def test_multiple_road_levels_are_not_silently_flattened():
 b=Buffer();b.parts.append(part('road','road_asphalt',b.parts[0].V+[0,0,2],b.parts[0].T))
 x=G.emit(b,cases(),1024,[],{})
 assert not x['applied'] and x['rejected'][0]['reason']=='ambiguous_road_levels' and len(b.parts)==3

def test_existing_paint_is_preserved():
 b=Buffer();b.parts.append(part('markings','marking_white',[(6,-11,0),(7,-11,0),(6,-10,0)],[(0,1,2)]))
 x=G.emit(b,cases(),1024,[],{})
 assert not x['applied'] and x['rejected'][0]['reason']=='paint_overlap' and len(b.parts)==3

def test_chunk_crossing_pair_is_rejected_atomically():
 b=Buffer();b.parts[0].V[:,1]=np.where(b.parts[0].V[:,1]==0,20,-20)
 x=G.emit(b,cases(n=-.05),1024,[],{})
 assert not x['applied'] and x['rejected'][0]['reason']=='cross_chunk_pair' and len(b.parts)==2
