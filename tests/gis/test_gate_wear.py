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
  assert np.all(p.UV1[:,0]==-G.LENGTH_M)
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


def _shader_ends(u,length):
 """Evaluate the actual shader expressions, checking both signed branches."""
 import re
 source=(ROOT/'game/Assets/_Project/Environment/Shaders/WorldPBR.shader').read_text()
 match=re.search(r'if \(i\.uv\.z < 0\.0\)\s*ends = (.*?);\s*else\s*ends = (.*?);',source)
 assert match,'Signed tyre contract is missing'
 expression=match.group(1 if length<0 else 2)
 expression=expression.replace('i.uv.x','u').replace('i.uv.z','length')
 return eval(expression,{'__builtins__':{}},{'u':u,'length':length,'abs':abs,'saturate':lambda x:np.clip(x,0,1)})


def test_signed_approach_fade_is_bounded_and_zero_at_both_physical_ends():
 u=np.array([-.1,0,.325,.65,2.1,3.3,3.75,4.2,4.3])
 actual=_shader_ends(u,-4.2)
 np.testing.assert_allclose(actual,[0,0,.5,1,1,1,.5,0,0],atol=1e-12)
 assert np.all((actual>=0)&(actual<=1))


def test_nonnegative_lengths_keep_literal_legacy_fade_including_zero():
 source=(ROOT/'game/Assets/_Project/Environment/Shaders/WorldPBR.shader').read_text()
 assert 'else\n                        ends = saturate(i.uv.x / 2.5) * saturate((i.uv.z - i.uv.x) / 4.0);' in source
 u=np.linspace(-1,30,1001)
 for length in [0.,.2,4.2,12.,25.]:
  np.testing.assert_array_equal(_shader_ends(u,length),np.clip(u/2.5,0,1)*np.clip((length-u)/4.,0,1))
