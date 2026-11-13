import osmium, json, sys, re
PB=r"C:\Users\matma\Documents\Claude\kamion\Data\raw\osm\podlaskie-261108.osm.pbf"
W,S,E,N=22.95,53.03,23.35,53.25
rx=re.compile(r'(weight|height|length|width|axle|hgv|goods|conditional|maxgv|truck|lorry|vehicle|motor_vehicle|access|delivery|destination)')
class H(osmium.SimpleHandler):
    def __init__(s): super().__init__(); s.rows=[]
    def way(s,w):
        t=w.tags
        if 'highway' not in t: return
        d={k:v for k,v in t if rx.search(k) and not k.startswith(('destination:','destination','source','note','fixme'))}
        if not d: return
        try: lo=[(n.lon,n.lat) for n in w.nodes if n.location.valid()]
        except Exception: return
        if not lo: return
        la=sum(p[1] for p in lo)/len(lo); lon=sum(p[0] for p in lo)/len(lo)
        if not(W<=lon<=E and S<=la<=N): return
        s.rows.append(dict(id=w.id,hw=t['highway'],name=t.get('name',''),ref=t.get('ref',''),lat=round(la,6),lon=round(lon,6),bridge=t.get('bridge',''),tags=d,ts=w.timestamp.isoformat(),ver=w.version))
h=H(); h.apply_file(PB,locations=True)
json.dump(h.rows,open(sys.argv[1],'w',encoding='utf-8'),ensure_ascii=False)
print(len(h.rows))
