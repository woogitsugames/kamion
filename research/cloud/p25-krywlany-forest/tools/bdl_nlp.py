import json,urllib.request,urllib.parse,time,os
UA="kamion-research/1.0 (open-data reference collection)"
def get(u):
    for t in range(6):
        try: return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=90).read()
        except Exception as e: print(e,flush=True); time.sleep(3)
B="https://mapserver.bdl.lasy.gov.pl/ArcGIS/rest/services/WMS_BDL_kat_wlasnosci/MapServer/6/query?"
feats=[];off=0
while True:
    q=urllib.parse.urlencode({'geometry':'23.135,53.078,23.215,53.122','geometryType':'esriGeometryEnvelope','inSR':4326,'spatialRel':'esriSpatialRelIntersects','outFields':'*','returnGeometry':'true','outSR':2180,'f':'json','resultOffset':off,'resultRecordCount':500})
    d=json.loads(get(B+q)); f=d.get('features',[]); feats+=f; print(len(f),d.get('exceededTransferLimit'),str(d)[:200] if not f else '')
    if not d.get('exceededTransferLimit') or not f: break
    off+=len(f)
json.dump(feats,open('bdl_nlp_items.json','w'),ensure_ascii=False)
print(len(feats)); print(feats[0]['attributes'] if feats else None)
os.makedirs('bdl_sd_nlp',exist_ok=True)
for f in feats:
    a=f['attributes']; fn=f"bdl_sd_nlp/{a['arodes_int_num']}.json"
    if os.path.exists(fn): continue
    q=urllib.parse.urlencode({'arodesIntNum':a['arodes_int_num'],'aYear':a['a_year'],'adressForest':a['adress_forest'],'jointOwnership':'false','label':'owner_cat_name'})
    b=get("https://www.bdl.lasy.gov.pl/portal/BULiGL.BDL.Reports/Map/StandDescriptionData?"+q)
    if b: open(fn,'wb').write(b)
    time.sleep(0.4)
print('done',len(os.listdir('bdl_sd_nlp')))
