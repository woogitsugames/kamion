import numpy as np, glob, math
from PIL import Image
from scipy import ndimage
cx,cy=155,1048-860
yy,xx=np.mgrid[0:340,0:330]
r=np.hypot(xx-cx,yy-cy); th=np.degrees(np.arctan2(xx-cx,-(yy-cy)))
ann=(r>104)&(r<128)
out=open('track30.csv','w'); out.write('t,dot_x,dot_y,org_deg,org_n,wht_deg,wht_n\n')
def mang(m):
    if m.sum()<15: return float('nan'),int(m.sum())
    t=np.radians(th[m]); return math.degrees(math.atan2(np.sin(t).mean(),np.cos(t).mean())), int(m.sum())
for i,f in enumerate(sorted(glob.glob('f30/c_*.png'))):
    t=10+i/30
    a=np.asarray(Image.open(f).convert('RGB')).astype(int); R,G,B=a[...,0],a[...,1],a[...,2]
    m=(R>120)&(R<240)&(abs(R-G)<14)&(B>=R-6)&(B-R<35)&(xx<300)
    m=ndimage.binary_opening(m,iterations=2)
    lab,n=ndimage.label(m); best=None
    for k,sl in enumerate(ndimage.find_objects(lab),1):
        h=sl[0].stop-sl[0].start; w=sl[1].stop-sl[1].start; area=(lab[sl]==k).sum()
        if 18<=w<=36 and 18<=h<=36 and area>0.6*w*h*0.785:
            c=ndimage.center_of_mass(lab==k); best=(c[1],c[0]+860)
    # orange: marker block hue
    org=ann&(R>60)&(R-B>30)&(R-G>12)&(G-B>12)&(R<140)
    org=ndimage.binary_opening(org,iterations=1)
    lab2,n2=ndimage.label(org); 
    if n2:
        sizes=ndimage.sum(org,lab2,range(1,n2+1)); k=int(np.argmax(sizes))+1; org=lab2==k
    wht=ann&(R>200)&(G>195)&(B>175)&(R-B<50)
    o,on=mang(org); w,wn=mang(wht)
    dx,dy=(best if best else (float('nan'),float('nan')))
    out.write(f"{t:.3f},{dx:.1f},{dy:.1f},{o:.1f},{on},{w:.1f},{wn}\n")
