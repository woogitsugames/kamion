"""Temporary prototype check; promoted to GIS tests after baseline."""
import sys,hashlib
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'tools/worldgen'))
from streetscape import plots as PLT
from roads.meshing import MeshBuf
from streetscape.plantings import front_gardens
from streetscape.vegetation import garden_canopies

def fixture():
 key=next(f'qa-{i}' for i in range(1000) if PLT.hfloat(f'qa-{i}','hedge')>.60 and PLT.hfloat(f'qa-{i}','adr0154-front')<.70)
 buf=MeshBuf()
 for layer in (PLT.KIT_LAYER,PLT.KIT_LAYER_LOW):
  kit=PLT.Kit()
  for x in (-10,10):
   for y in (-10,10):kit.box(np.array([x,y]),np.array([1.,0.]),10.,10.,139.8,146.,[0.,0.])
  o=kit.out();buf.add(layer,'plot_kit',o[0],o[1],o[2],COL=o[3])
 gate={'m':np.array([0.,-20.]),'n':np.array([0.,-1.]),'t':np.array([1.,0.]),'w':4.}
 plot={'id':'test','key':key,'age':'old','front_style':'picket','front_h':1.3,'house_h':10.,'poly':Polygon([(-20,-20),(20,-20),(20,20),(-20,20)]),'foot':Polygon([(-5,0),(5,0),(5,10),(-5,10)]),'hard':Polygon([(-2.5,-20),(2.5,-20),(2.5,0),(-2.5,0)]),'lay':{'runs':[{'a':np.array([-20.,-20.]),'b':np.array([20.,-20.]),'n':np.array([0.,-1.]),'front':True}],'gate':gate,'wicket':None,'wickets':[]}}
 return buf,{'plots':[plot]}

buf,rp=fixture();protected=[x.V.tobytes()+x.T.tobytes() for x in buf.parts];report={};out=front_gardens(buf,rp,lambda q:140.,report)
assert out['segments']==2 and out['tris_low']>0,out
assert protected==[x.V.tobytes()+x.T.tobytes() for x in buf.parts[:2]]
for part in buf.parts[2:]:
 assert part.layer in ('plots','plots_low') and part.mat=='plot_kit'
 assert not np.any((np.abs(part.V[:,0])<2.5)&(part.V[:,1]<-15.)), 'Gate blocked'
buf2,rp2=fixture();out2=front_gardens(buf2,rp2,lambda q:140.,{})
assert out==out2
assert [p.V.tobytes() for p in buf.parts]==[p.V.tobytes() for p in buf2.parts]
buf3,rp3=fixture();out3=front_gardens(buf3,rp3,lambda q:140.,{},triangle_limit=0);assert out3['segments']==0
high={'p':'tree_maple','v':2,'h':11.,'e':0.,'n':0.,'z':140.,'src':'plot:test:canopy','tier':'high'}
low={**high,'tier':'low'};forest={**high,'src':'forest:sample','tier':'high'}
result=garden_canopies([high,low,forest],rp,{})
assert len(result)==3 and result[0]['h']==13.5 and result[0]['garden_canopy_width']==1.35
assert result[1]==low and result[2]==forest and 'garden_canopy_width' not in high
print({'prototype_segments':out['segments'],'meters':out['m'],'tris_low':out['tris_low'],'gate_clear':True,'deterministic':True,'non_high_unchanged':True})
