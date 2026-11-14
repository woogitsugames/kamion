import sys
sys.path.insert(0,"tools/worldgen")
from streetscape import facade_atlas as FA
from PIL import Image
import numpy as np
T="game/Assets/_Generated/World/bialystok-industrial-c/Textures/PBR/"
A=np.asarray(Image.open(T+"facade_atlas/T_facade_atlas_BaseColor.png").convert("L"),float); H,W=A.shape
for kind in ("w2","w3","w1","off","bwin","stair"):
    for var in range(FA.KINDS[kind][2]):
        u0,v0,w,h=FA.cell(kind,var)
        c=A[int(H-(v0+h)/16*H):int(H-v0/16*H), int(u0/16*W):int((u0+w)/16*W)]
        rows=c.mean(1); n=len(rows)
        print(f"{kind}{var}: mean {c.mean():.0f} p10 {np.percentile(c,10):.0f} top-half {c[:n//2].mean():.0f} bottom-half {c[n//2:].mean():.0f}")
