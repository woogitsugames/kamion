import sys, yaml, numpy as np, rasterio
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw
sys.path.insert(0,"tools/worldgen"); sys.path.insert(0,"tools/worldgen/roads")
from streetscape import runway_paint as R
out=sys.argv[1]
ov=yaml.safe_load(open('Data/Regions/bialystok-dojlidy/overrides.yaml',encoding='utf8'))['overrides']
class B:
    def __init__(s): s.tr=[]
    def add(s,layer,mat,V,UV,T,src=None,UV1=None): s.tr+= [V[t,:2] for t in T]
b=B(); R.build(b,ov,lambda e,n: np.zeros(len(e)),{})
def crop(name,e0,n0,e1,n1,sc):
    with rasterio.open('Data/raw/derived/bialystok-dojlidy/ortho_0p25m.tif') as ds:
        a=ds.read([1,2,3],window=from_bounds(e0+780043,n0+590079,e1+780043,n1+590079,ds.transform))
    im=Image.fromarray(np.moveaxis(a,0,2)); px=im.size[0]/(e1-e0)*sc
    im=im.resize((int(im.size[0]*sc),int(im.size[1]*sc)),Image.LANCZOS)
    top=im.copy(); dr=ImageDraw.Draw(top)
    for t in b.tr:
        dr.polygon([((x-e0)*px,(n1-y)*px) for x,y in t],fill=(255,0,255))
    w,h=im.size
    sheet=Image.new('RGB',(w,2*h+4),(0,0,0)); sheet.paste(im,(0,0)); sheet.paste(top,(0,h+4)); sheet.save(out+'/'+name,quality=90); print(name,sheet.size)
crop('paint_w.jpg',-1024,-245,-760,-185,0.9)
crop('paint_mid.jpg',-640,-230,-400,-175,1.0)
crop('paint_e.jpg',-300,-225,-95,-145,1.15)
crop('paint_27L.jpg',-200,-215,-140,-170,4)
crop('paint_09R.jpg',-1024,-235,-985,-200,6)
crop('paint_27thr.jpg',-830,-232,-790,-197,6)
