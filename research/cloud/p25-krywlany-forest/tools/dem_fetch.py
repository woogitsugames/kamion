import json,urllib.request,time,os,sys
UA="kamion-research/1.0 (open-data reference collection)"
tiles=json.load(open(sys.argv[1] if len(sys.argv)>1 else 'tiles.json')); S=250
os.makedirs('dem',exist_ok=True)
def get(u,fn):
    if os.path.exists(fn) and os.path.getsize(fn)>1000: return
    for t in range(5):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=180)
            b=r.read()
            if len(b)<1000: raise Exception('small %d'%len(b))
            open(fn,'wb').write(b); return
        except Exception as e:
            print(fn,e,flush=True); time.sleep(3+3*t)
for (x,y) in tiles:
    sub=f"&SUBSET=x({x},{x+S})&SUBSET=y({y},{y+S})&SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/2180"
    get("https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=DSM_PL-KRON86-NH&FORMAT=image/x-aaigrid&SCALEFACTOR=0.5"+sub,f"dem/dsm_{x}_{y}.asc")
    get("https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=DTM_PL-KRON86-NH_TIFF&FORMAT=image/tiff"+sub,f"dem/dtm_{x}_{y}.tif")
    time.sleep(0.2)
print('done')
