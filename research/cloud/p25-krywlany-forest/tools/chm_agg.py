import pickle,collections,csv,json
import numpy as np
st=pickle.load(open('stations.pkl','rb'))
print(len(st),collections.Counter(s['obiekt'] for s in st))
def odz(s):
    if s['bdl']: return 'BDL '+' '.join(x.strip() for x in s['bdl'].replace('   -',' ').split() if x.strip('-'))
    return 'PTLZ '+s['ptlz'][:13]
groups=collections.defaultdict(list)
for s in st: groups[(s['obiekt'],s['strona'],odz(s))].append(s)
rows=[]
P=lambda a,q: float(np.percentile(a,q))
for (ob,side,lab),ss in sorted(groups.items(),key=lambda kv:(kv[0][0],-len(kv[1]))):
    if len(ss)<3: continue
    r30=np.concatenate([s['raw30'] for s in ss]); r5=np.concatenate([s['raw5'] for s in ss])
    mw=np.array([s['plaszcz_szer_m'] for s in ss]); mh=np.array([s['plaszcz_h90'] for s in ss if s['plaszcz_szer_m']>=1])
    off50=[s['h30off_p50'] for s in ss if s['h30off_p50']!='']
    off90=[s['h30off_p90'] for s in ss if s['h30off_p90']!='']
    rows.append(dict(obiekt=ob,strona_drogi=side,wydzielenie=lab,osm=collections.Counter(s['osm'] for s in ss).most_common(1)[0][0],ptlz_id=collections.Counter(s['ptlz'] for s in ss).most_common(1)[0][0],ptlz_kat=ss[0]['ptlz_kat'],
        n_stacji=len(ss),dlugosc_m=len(ss)*10,lat=round(float(np.mean([s['lat'] for s in ss])),6),lon=round(float(np.mean([s['lon'] for s in ss])),6),azymut_normalnej=round(float(np.degrees(np.arctan2(np.mean([np.sin(np.radians(s['azymut_normalnej'])) for s in ss]),np.mean([np.cos(np.radians(s['azymut_normalnej'])) for s in ss])))%360)),
        d_sciany_p50=P([s['d_sciany_m'] for s in ss],50),d_sciany_p10=P([s['d_sciany_m'] for s in ss],10),d_sciany_p90=P([s['d_sciany_m'] for s in ss],90),
        h30_p50=round(P(r30,50),1),h30_p90=round(P(r30,90),1),h30_max=round(float(r30.max()),1),h30_p10=round(P(r30,10),1),
        h5_p50=round(P(r5,50),1),h5_p90=round(P(r5,90),1),
        plaszcz_szer_p50=P(mw,50),plaszcz_szer_p75=P(mw,75),plaszcz_udzial_ge2m=round(float((mw>=2).mean()),2),plaszcz_h90_p50=round(P(mh,50),1) if len(mh) else '',
        narastanie_p50=P([s['narastanie_m'] for s in ss],50),narastanie_p90=P([s['narastanie_m'] for s in ss],90),
        h30_bezlistny_p50=round(float(np.median(off50)),1) if off50 else '',h30_bezlistny_p90=round(float(np.median(off90)),1) if off90 else ''))
w=csv.DictWriter(open('chm_edges.csv','w',newline='',encoding='utf-8'),fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
for r in rows: print(r['obiekt'],r['strona_drogi'],r['wydzielenie'],r['dlugosc_m'],'d',r['d_sciany_p50'],'H30',r['h30_p50'],r['h30_p90'],r['h30_max'],'H5',r['h5_p50'],r['h5_p90'],'pl',r['plaszcz_szer_p50'],r['plaszcz_szer_p75'],r['plaszcz_udzial_ge2m'],r['plaszcz_h90_p50'],'nar',r['narastanie_p50'],r['narastanie_p90'],'off',r['h30_bezlistny_p50'],r['h30_bezlistny_p90'])
# stacje csv
keys=[k for k in st[0].keys() if k not in('prof','raw30','raw5')]
w=csv.DictWriter(open('chm_stations.csv','w',newline='',encoding='utf-8'),fieldnames=keys); w.writeheader()
for s in st: w.writerow({k:(round(s[k],1) if isinstance(s[k],float) and k not in('lat','lon') else s[k]) for k in keys})
# profil średni względem ściany
for ob in ['D303','MICK','CIOL','AERO','ALL']:
    pr=np.array([s['prof'] for s in st if s['prof'] and len(s['prof'])==120 and not np.isnan(s['prof'][20]) and (ob=='ALL' or s['obiekt']==ob)])
    if len(pr)<5: continue
    print(ob,len(pr),'d_rel:p25/p50/p75')
    for d in (-15,-10,-6,-4,-2,-1,0,1,2,3,5,8,12,20,30):
        i=int((d+20)/0.5); print('  ',d,[round(float(np.nanpercentile(pr[:,i],q)),1) for q in (25,50,75)])
pr=np.array([s['prof'] for s in st if s['prof'] and len(s['prof'])==120 and not np.isnan(s['prof'][20])])
json.dump({'d_rel_m':[round(-20+0.5*i,1) for i in range(120)],'p25':np.nanpercentile(pr,25,axis=0).round(1).tolist(),'p50':np.nanpercentile(pr,50,axis=0).round(1).tolist(),'p75':np.nanpercentile(pr,75,axis=0).round(1).tolist(),'n':len(pr)},open('chm_profile_mean.json','w'))
