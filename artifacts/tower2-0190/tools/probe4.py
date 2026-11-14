import sys
sys.path.insert(0,"tools/worldgen")
from streetscape import facade_atlas as FA
from PIL import Image
import numpy as np
T="game/Assets/_Generated/World/bialystok-industrial-c/Textures/PBR/"
Ai=Image.open(T+"facade_atlas/T_facade_atlas_BaseColor.png").convert("RGB"); A=np.asarray(Ai.convert("L"),float); H,W=A.shape
ims=[]
for kind,var in (("balf",1),("balf",6),("balf",3),("balg",0),("balg",1),("balg",2),("off",4),("off",2)):
    u0,v0,w,h=FA.cell(kind,var)
    bx=(int(u0/16*W),int(H-(v0+h)/16*H),int((u0+w)/16*W),int(H-v0/16*H))
    c=A[bx[1]:bx[3],bx[0]:bx[2]]
    print(kind,var,(u0,v0,w,h),"mean",round(c.mean()),"p50",round(np.percentile(c,50)),"rows",[round(x) for x in c.mean(1)[::max(1,len(c)//10)]])
    ims.append(Ai.crop(bx).resize((int(w*120),int(h*120))))
out=Image.new("RGB",(sum(i.width for i in ims)+10*len(ims),max(i.height for i in ims)),(255,0,255))
x=0
for i in ims: out.paste(i,(x,0)); x+=i.width+10
out.save(sys.argv[1])
F=np.asarray(Image.open(T+"facade_far/T_facade_far_BaseColor.png").convert("L"),float); FH,FW=F.shape
v=FA.far_row_v("balcony_1",0)
def far(x0,x1,v0,v1): return F[int(FH-v1/FA.FAR_M[1]*FH):int(FH-v0/FA.FAR_M[1]*FH), int(x0/FA.FAR_M[0]*FW):int(x1/FA.FAR_M[0]*FW)]
b=far(1.5-1.2,1.5+1.2,v+0.1,v+1.0); print("far balcony_1 front: mean",round(b.mean()),"rows",[round(x) for x in b.mean(1)[::4]])
