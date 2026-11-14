import urllib.request,re,json,time
UA="kamion-research/1.0 (open-data reference collection)"
from pyproj import Transformer
T=Transformer.from_crs(4326,2180,always_xy=True)
pts={'D303_srodek':(53.1066,23.1700),'P11-056':(53.104182,23.176891),'MICK_las':(53.0960,23.1925),'MICK_pd':(53.0890,23.1995),'CIOL_zach':(53.1020,23.1500),'AERO_pd':(53.0975,23.1740),'ZWIERZ':(53.1100,23.1620)}
out=[]
for k in ['NMPT','NMT']:
    B=f"https://mapy.geoportal.gov.pl/wss/service/PZGIK/{k}/WMS/SkorowidzeUkladEVRF2007"
    L=','.join(f"Skorowidze{k}{y}" for y in ['2023iStarsze','2024','2025','2026'])
    for name,(la,lo) in pts.items():
        e,n=T.transform(lo,la)
        u=f"{B}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&LAYERS={L}&QUERY_LAYERS={L}&SRS=EPSG:2180&BBOX={e-50},{n-50},{e+50},{n+50}&WIDTH=101&HEIGHT=101&X=50&Y=50&INFO_FORMAT=text/html&FEATURE_COUNT=20&STYLES="
        s=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=60).read().decode('utf-8','replace')
        for m in re.finditer(r'push\(\{(.*?)\}\)',s):
            d=dict(re.findall(r'(\w+):"([^"]*)"',m.group(1)))
            out.append(dict(model=k,punkt=name,lat=la,lon=lo,**d)); print(k,name,d.get('godlo'),d.get('aktualnosc'),d.get('charakterystykaPrzestrzenna'),d.get('bladSredniWysokosci'),d.get('ukladWspolrzednychPionowych'),d.get('format'))
        time.sleep(0.3)
json.dump(out,open('skorowidze.json','w'),ensure_ascii=False,indent=1)
