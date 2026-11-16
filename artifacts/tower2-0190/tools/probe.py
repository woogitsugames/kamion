import sys
sys.path.insert(0,"tools/worldgen")
from streetscape import facade_atlas as FA
from PIL import Image
import numpy as np
T="game/Assets/_Generated/World/bialystok-industrial-c/Textures/PBR/"
A=np.asarray(Image.open(T+"facade_atlas/T_facade_atlas_BaseColor.png").convert("L"),float); H,W=A.shape
for var in (4,2,0):
    u0,v0,w,h=FA.cell("off",var)
    print("atlas off",var,"luma by v-fraction (0=bottom):")
    for f in np.arange(0,1.0,0.05):
        y=int(H-(v0+h*(f+0.025))/16*H); x0=int((u0+0.3)/16*W); x1=int((u0+0.6)/16*W)
        print(f" {f:.2f}:{A[y,x0:x1].mean():.0f}",end="")
    print()
F=np.asarray(Image.open(T+"facade_far/T_facade_far_BaseColor.png").convert("L"),float); FH,FW=F.shape
def far(x0,x1,v0,v1):
    return F[int(FH-v1/FA.FAR_M[1]*FH):int(FH-v0/FA.FAR_M[1]*FH), int(x0/FA.FAR_M[0]*FW):int(x1/FA.FAR_M[0]*FW)]
for g,row in (("office",0),("office",1)):
    v=FA.far_row_v(g,row)
    for bay,e in enumerate(FA.FAR_ROWS[g][row]):
        xc=(bay+0.5)*3
        prof=[far(xc-0.45,xc-0.15,v+0.9+1.6*f,v+0.9+1.6*(f+0.05)).mean() for f in np.arange(0,1,0.1)]
        print(g,row,bay,e,[int(p) for p in prof])
v=FA.far_row_v("ribbon",0)
print("ribbon row0 bay1 pane", far(3.45,3.95,v+1.5,v+1.9).mean(), far(3.45,3.95,v+1.5,v+1.9).max(), "plain", far(4.0,5.0,0.65,0.85).mean())
print("ribbon head zone", [int(far(3.45,3.95,v+0.9+1.6*f,v+0.9+1.6*(f+0.05)).mean()) for f in np.arange(0,1,0.1)])
