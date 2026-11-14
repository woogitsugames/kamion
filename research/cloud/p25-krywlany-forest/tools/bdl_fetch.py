import json,urllib.request,urllib.parse,time,os
UA="kamion-research/1.0 (open-data reference collection)"
d=json.load(open('bdl_items.json'))
os.makedirs('bdl_sd',exist_ok=True)
for f in d['features']:
    p=f['properties']; fn=f"bdl_sd/{p['a_i_num']}.json"
    if os.path.exists(fn): continue
    q=urllib.parse.urlencode({'arodesIntNum':p['a_i_num'],'aYear':p['a_year'],'adressForest':p['adr_for'],'jointOwnership':'false','label':'owner_cat_name'})
    for t in range(4):
        try:
            r=urllib.request.urlopen(urllib.request.Request("https://www.bdl.lasy.gov.pl/portal/BULiGL.BDL.Reports/Map/StandDescriptionData?"+q,headers={'User-Agent':UA}),timeout=60)
            open(fn,'wb').write(r.read()); break
        except Exception as e:
            print(p['a_i_num'],e); time.sleep(3)
    time.sleep(0.4)
print('done',len(os.listdir('bdl_sd')))
