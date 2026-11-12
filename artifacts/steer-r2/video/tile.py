import sys
from PIL import Image, ImageDraw
t0,t1,step=float(sys.argv[1]),float(sys.argv[2]),float(sys.argv[3]); out=sys.argv[4]
ts=[]; t=t0
while t<=t1+1e-6: ts.append(round(t,1)); t+=step
cols=6; w,h=320,330
img=Image.new('RGB',(cols*w,((len(ts)+cols-1)//cols)*h))
for k,t in enumerate(ts):
    i=int(round(t*10))+1
    a=Image.open(f'fr/f_{i:04d}.png').convert('RGB').crop((0,870,320,1200))
    d=ImageDraw.Draw(a); d.text((230,5),f"{t:.1f}s",fill=(255,255,0))
    sp=Image.open(f'fr/f_{i:04d}.png').convert('RGB').crop((440,20,600,70)).resize((80,25))
    a.paste(sp,(235,20))
    img.paste(a,((k%cols)*w,(k//cols)*h))
img.save(out)
