import osmium, json, sys
PB=r"C:\Users\matma\Documents\Claude\kamion\Data\raw\osm\podlaskie-261108.osm.pbf"
NAMES={'Księdza Stanisława Suchowolca','Dojlidy Fabryczne','Nowowarszawska','Plażowa','Jacka Kuronia','Adama Mickiewicza','Konstantego Ciołkowskiego','Dywizjonu 303','Jana Klemensa Branickiego','Zwierzyniecka','Piastowska'}
class H(osmium.SimpleHandler):
    def __init__(s): super().__init__(); s.ways=[]
    def way(s,w):
        n=w.tags.get('name','')
        if n in NAMES and 'highway' in w.tags:
            if w.tags.get('highway') in('footway','cycleway','path','steps'):return
            try: pts=[(x.lat,x.lon) for x in w.nodes]; ids=[x.ref for x in w.nodes]
            except Exception: return
            s.ways.append(dict(id=w.id,name=n,hw=w.tags['highway'],ref=w.tags.get('ref',''),tags={k:v for k,v in w.tags if k.startswith(('max','hgv','goods','access','oneway'))},a=pts[0],b=pts[-1],ids=[ids[0],ids[-1]],mid=pts[len(pts)//2]))
h=H(); h.apply_file(PB,locations=True)
json.dump(h.ways,open(sys.argv[1],'w',encoding='utf-8'),ensure_ascii=False)
print(len(h.ways))
