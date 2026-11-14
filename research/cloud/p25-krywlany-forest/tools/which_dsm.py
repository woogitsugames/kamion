import json,urllib.request,numpy as np
UA="kamion-research/1.0 (open-data reference collection)"
urls={'2025-04-18':('https://opendata.geoportal.gov.pl/NumDaneWys/NMPT/83270/83270_1746279_N-34-107-C-b-4-3.asc',4453,4875,780194.5-0.25,587972.5-0.25),
      '2023-09-15':('https://opendata.geoportal.gov.pl/NumDaneWys/NMPT/78825/78825_1436515_N-34-107-C-b-4-3.asc',4454,4877,780194.0-0.25,587972.0-0.25)}
res={}
for d,(u,nc,nr,xll,yll) in urls.items():
    h=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA,'Range':'bytes=0-10'}),timeout=60)
    size=int(h.headers['Content-Range'].split('/')[1])
    off=int(size*0.45)
    b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA,'Range':f'bytes={off}-{off+250000}'}),timeout=120).read().decode('ascii','replace')
    lines=[l.split() for l in b.split('\n')[1:-1]]
    lines=[np.array(l,dtype=float) for l in lines if len(l)==nc]
    row_est=off/size*nr
    print(d,size,len(lines),'row_est',row_est)
    res[d]=(lines,row_est,nc,nr,xll,yll)
# WCS block
lines,row_est,nc,nr,xll,yll=res['2023-09-15']
top=yll+nr*0.5
ymid=top-row_est*0.5
x0=round(xll+800); n=600
u=f"https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=DSM_PL-EVRF2007-NH&FORMAT=image/x-aaigrid&SUBSET=x({x0},{x0+n*0.5})&SUBSET=y({ymid-60},{ymid+60})&SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/2180"
b=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=180).read().decode('latin1')
print(b[b.find('ncols'):b.find('ncols')+150].replace('\n',' | '))
body=b.split('cellsize')[1].split('\n',1)[1]
W=np.array([l.split() for l in body.split('\n') if len(l.split())==n],dtype=float)
print(W.shape)
for d,(lines,row_est,nc,nr,xll,yll) in res.items():
    i0=int(round((x0-xll)/0.5))
    best=(1e9,None)
    for li,l in enumerate(lines[:3]):
        a=l[i0:i0+n]
        for sh in (-1,0,1):
            a2=l[i0+sh:i0+sh+n]
            for wi in range(W.shape[0]):
                m=np.abs(a2-W[wi])
                v=np.median(m)
                if v<best[0]: best=(v,(li,sh,wi,float(m.mean()),float(np.percentile(m,90))))
    print(d,'best median abs diff',best)
