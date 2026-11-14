# Pas ortofoto wzdłuż odcinka ulicy: kafel GUGiK WMS HighResolution 0,1 m/px, obrót tak, by oś była pozioma,
# pas +-half_w m, cięty na kawałki 960 px (96 m), układane po 2 na obraz 960x960 do oglądania.
# Współrzędna wzdłuż osi s[m] = (nr_kawałka*960 + x_px)*0.1 ; poprzeczna t[m] = (y_px - 240)*0.1 (dodatnie = w dół obrazu).
import sys,math,json,io,urllib.request,urllib.parse
from PIL import Image
UA='kamion-research/1.0 (open-data reference collection)'
def run(name,lat1,lon1,lat2,lon2,half_w=24.0,outdir='ortho'):
    latc=(lat1+lat2)/2; lonc=(lon1+lon2)/2
    kx=111320.0*math.cos(math.radians(latc)); kz=110574.0
    dx=(lon2-lon1)*kx; dz=(lat2-lat1)*kz; L=math.hypot(dx,dz)
    half=L/2+half_w+10; mpp=0.1; px=int(round(2*half/mpp))
    px=min(px,4096); mpp=2*half/px
    bbox=(latc-half/kz,lonc-half/kx,latc+half/kz,lonc+half/kx)
    p={'SERVICE':'WMS','VERSION':'1.3.0','REQUEST':'GetMap','LAYERS':'Raster','STYLES':'','CRS':'EPSG:4326',
       'BBOX':'%.7f,%.7f,%.7f,%.7f'%bbox,'WIDTH':px,'HEIGHT':px,'FORMAT':'image/jpeg'}
    u='https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution?'+urllib.parse.urlencode(p)
    data=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=180).read()
    im=Image.open(io.BytesIO(data)).convert('RGB')
    th=math.degrees(math.atan2(-dz,dx))  # kąt osi w układzie obrazu (y w dół)
    r=im.rotate(th,resample=Image.BICUBIC,expand=False)
    c=px/2; hw=int(half_w/mpp); Lp=int(L/mpp)
    band=r.crop((int(c-Lp/2),int(c-hw),int(c+Lp/2),int(c+hw)))
    band=band.resize((int(band.width*mpp/0.1),int(band.height*mpp/0.1)))
    n=math.ceil(band.width/960); files=[]
    for i in range(0,n,2):
        sheet=Image.new('RGB',(960,band.height*2+4),(255,0,255))
        for j in (0,1):
            if i+j<n: sheet.paste(band.crop(((i+j)*960,0,min(band.width,(i+j+1)*960),band.height)),(0,j*(band.height+4)))
        fn='%s/%s_s%d.jpg'%(outdir,name,i//2); sheet.save(fn,quality=90); files.append(fn)
    band.save('%s/%s_band.png'%(outdir,name))
    json.dump({'name':name,'url':u,'A':[lat1,lon1],'B':[lat2,lon2],'length_m':L,'m_per_px_src':mpp,'band_px':[band.width,band.height],'half_w_m':half_w,'sheets':files},open('%s/%s_strip.json'%(outdir,name),'w'),indent=1)
    print(name,'L=%.0f m'%L,'src mpp %.3f'%mpp,files)
if __name__=='__main__':
    a=sys.argv; run(a[1],float(a[2]),float(a[3]),float(a[4]),float(a[5]),float(a[6]) if len(a)>6 else 24.0)
