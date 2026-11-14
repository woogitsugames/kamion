# Rozstaw latarni z węzłów OSM highway=street_lamp wzdłuż ulic trasy (ESTIMATED).
# Metoda: lokalny ENU (X=wschód, Z=północ) od punktu odniesienia; lampa przypisana do najbliższej
# osi ulicy (<= 30 m); "następna lampa w rzędzie" = najbliższa lampa tej samej ulicy w kierunku osi
# (|odchyłka poprzeczna| <= 6 m, odległość wzdłuż 10..90 m). Statystyki: n, p10, p50, p90.
import json,math,sys,collections,statistics
src=sys.argv[1]
d=json.load(open(src))
LAT0,LON0=53.1560,23.1500
def enu(lat,lon):
    return ((lon-LON0)*math.cos(math.radians(LAT0))*111320.0,(lat-LAT0)*110574.0)
ways=[e for e in d['elements'] if e['type']=='way']
lamps=[e for e in d['elements'] if e['type']=='node']
segs=[]
for w in ways:
    pts=[enu(p['lat'],p['lon']) for p in w['geometry']]
    nm=w['tags'].get('name')
    for a,b in zip(pts,pts[1:]):
        segs.append((nm,a,b,w['tags'].get('highway')))
def segdist(p,a,b):
    ax,az=a;bx,bz=b;px,pz=p
    dx,dz=bx-ax,bz-az;L2=dx*dx+dz*dz
    t=0 if L2==0 else max(0,min(1,((px-ax)*dx+(pz-az)*dz)/L2))
    qx,qz=ax+t*dx,az+t*dz
    return math.hypot(px-qx,pz-qz),math.atan2(dx,dz)
by=collections.defaultdict(list)
for n in lamps:
    p=enu(n['lat'],n['lon'])
    best=None
    for nm,a,b,hw in segs:
        dist,brg=segdist(p,a,b)
        if best is None or dist<best[0]: best=(dist,nm,brg,hw)
    if best and best[0]<=30: by[best[1]].append((p,best[2],best[0],n))
out={}
for nm,L in sorted(by.items()):
    sp=[]
    for (p,brg,dist,n) in L:
        ux,uz=math.sin(brg),math.cos(brg)
        cand=[]
        for (q,_,_,m) in L:
            if m is n: continue
            dx,dz=q[0]-p[0],q[1]-p[1]
            al=dx*ux+dz*uz; la=abs(-dx*uz+dz*ux)
            if 10<=al<=90 and la<=6: cand.append(al if la<1 else math.hypot(al,la))
        if cand: sp.append(min(cand))
    tags=collections.Counter()
    for (_,_,_,n) in L:
        t=n.get('tags',{})
        tags[('lamp_type',t.get('lamp_type'))]+=1; tags[('lamp_mount',t.get('lamp_mount'))]+=1; tags[('light:count',t.get('light:count'))]+=1
    dd=sorted(x[2] for x in L)
    r={'lamps':len(L),'pairs':len(sp)}
    if len(sp)>=3:
        s=sorted(sp); q=lambda f:s[min(len(s)-1,int(f*len(s)))]
        r.update(p10=round(q(.1),1),p50=round(statistics.median(s),1),p90=round(q(.9),1),mean=round(statistics.mean(s),1))
    r['offset_from_axis_p50']=round(statistics.median(dd),1)
    r['tags']={f'{k[0]}={k[1]}':v for k,v in tags.most_common()}
    out[nm]=r
json.dump(out,sys.stdout,ensure_ascii=False,indent=1)
