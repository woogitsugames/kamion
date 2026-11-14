import sys
sys.path.insert(0,"tools/worldgen")
from streetscape import facade_atlas as FA
from PIL import Image
import numpy as np
T="game/Assets/_Generated/World/bialystok-industrial-c/Textures/PBR/facade_far/"
def load(n): return np.asarray(Image.open(T+n).convert("RGBA"),float)
B,M,V=load("T_facade_far_BaseColor.png"),load("T_facade_far_MaskMap.png"),load("T_facade_far_Var.png")
FH,FW=B.shape[:2]
def box(img,x0,x1,v0,v1): return img[int(FH-v1/FA.FAR_M[1]*FH):int(FH-v0/FA.FAR_M[1]*FH), int(x0/FA.FAR_M[0]*FW):int(x1/FA.FAR_M[0]*FW)].reshape(-1,4).mean(0).round(0)
v=FA.far_row_v("office",1)   # row 1 bay 0 = variant 4
xc=1.5
for name,(x0,x1,a,b) in {"plain wall":(4.0,5.0,0.65,0.85),"blind (crop .36..1)":(xc-0.6,xc+0.6,v+0.9+0.6,v+2.4),"dark glass":(xc-0.6,xc+0.6,v+1.0,v+1.3),"v2 bay2 top":(7.5-0.6,7.5+0.6,v+1.8,v+2.4)}.items():
    print(f"{name:22} base {box(B,x0,x1,a,b)} mask {box(M,x0,x1,a,b)} var {box(V,x0,x1,a,b)}")
