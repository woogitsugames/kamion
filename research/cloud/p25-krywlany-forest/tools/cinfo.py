import json,pickle,time,re
from wm import api
from shapely import wkt
from shapely.geometry import Point
from shapely.ops import unary_union
from pyproj import Transformer
T=Transformer.from_crs(4326,2180,always_xy=True)
F=wkt.loads(pickle.load(open('F.pkl','rb')))
inv=pickle.load(open('inv.pkl','rb')); aero=wkt.loads(inv['aero'])
sel={'D303':'Dywizjonu 303','MICK':'Adama Mickiewicza','KUR':'Jacka Kuronia','CIOL':'Konstantego Ciołkowskiego'}
roads={k:unary_union([wkt.loads(l) for i,l,h in inv['roads'][v]]) for k,v in sel.items()}
geo=json.load(open('commons_geo.json'))
ids=list(geo.keys()); info={}
for i in range(0,len(ids),50):
    d=api({'action':'query','pageids':'|'.join(ids[i:i+50]),'prop':'imageinfo','iiprop':'url|sha1|size|extmetadata|mime','iiextmetadatafilter':'LicenseShortName|Artist|DateTimeOriginal|ImageDescription|Categories|GPSLatitude|GPSLongitude'})
    for pid,p in (d or {}).get('query',{}).get('pages',{}).items():
        if 'imageinfo' in p: info[pid]=dict(title=p['title'],**p['imageinfo'][0])
    time.sleep(2)
rows=[]
for pid,g in geo.items():
    if pid not in info: continue
    ii=info[pid]; em=ii.get('extmetadata',{})
    e,n=T.transform(g['lon'],g['lat']); P=Point(e,n)
    dd={k:round(P.distance(r)) for k,r in roads.items()}
    rows.append(dict(pageid=pid,title=g['title'],lat=g['lat'],lon=g['lon'],d_las=round(P.distance(F),1),d_aero=round(P.distance(aero)),**{'d_'+k:v for k,v in dd.items()},
        url=ii['url'],sha1=ii['sha1'],w=ii['width'],h=ii['height'],size=ii['size'],mime=ii['mime'],
        lic=em.get('LicenseShortName',{}).get('value'),artist=re.sub('<[^>]+>','',em.get('Artist',{}).get('value','')),date=em.get('DateTimeOriginal',{}).get('value'),
        cats=em.get('Categories',{}).get('value','')[:300],desc=re.sub('<[^>]+>','',em.get('ImageDescription',{}).get('value',''))[:200]))
json.dump(rows,open('commons_rows.json','w'),ensure_ascii=False,indent=0)
print(len(rows))
import collections
print(collections.Counter(r['lic'] for r in rows)); print(collections.Counter(r['artist'] for r in rows).most_common(8)); print(collections.Counter(r['mime'] for r in rows))
