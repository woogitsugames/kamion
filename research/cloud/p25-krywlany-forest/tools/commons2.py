import json,itertools,time
from wm import api
res={}
pts=[(53.1042,23.1769),(53.1065,23.1680),(53.1080,23.1600),(53.1050,23.1850),(53.1000,23.1900),(53.0960,23.1930),(53.0915,23.1965),(53.0880,23.2000),(53.1020,23.1550),(53.1010,23.1460),(53.1000,23.1730),(53.0975,23.1650),(53.1065,23.1950),(53.1075,23.2050),(53.1100,23.1620),(53.0965,23.1800)]
for la,lo in pts:
    d=api({'action':'query','list':'geosearch','gscoord':f'{la}|{lo}','gsradius':600,'gslimit':500,'gsnamespace':6,'gsprimary':'all'})
    n=0
    for g in (d or {}).get('query',{}).get('geosearch',[]): res[g['pageid']]=g; n+=1
    print(la,lo,n,len(res),flush=True)
    json.dump(res,open('commons_geo.json','w'))
    time.sleep(3)
print('done')
