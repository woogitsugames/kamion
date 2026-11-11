import json,glob,math,collections,sys
root = sys.argv[1] if len(sys.argv)>1 else "Data/raw/derived/bialystok-industrial-c/world"
cars=[]
for f in glob.glob(root+"/instances_*.json"):
    for i in json.load(open(f,encoding="utf-8"))["instances"]:
        p=i["p"]
        if p.startswith(("car_","van_")) or "car" in p.split("_")[0]: cars.append(i)
print("vehicles", len(cars), collections.Counter(c["p"].split("_")[0] for c in cars).most_common(6))
grid=collections.defaultdict(list)
for c in cars: grid[(int(c["e"]//4),int(c["n"]//4))].append(c)
bad=[]
for c in cars:
    gx,gy=int(c["e"]//4),int(c["n"]//4)
    for dx in(-1,0,1):
        for dy in(-1,0,1):
            for o in grid[(gx+dx,gy+dy)]:
                if o is c or id(o)<id(c): continue
                d=math.hypot(c["e"]-o["e"],c["n"]-o["n"])
                if d<1.9: bad.append((round(d,2),c["p"],o["p"],round(c["e"],1),round(c["n"],1),c["src"][:40],o["src"][:40]))
bad.sort()
print("pairs closer than 1.9 m:",len(bad))
for b in bad[:25]: print(b)
rs=json.load(open("Data/Regions/bialystok-industrial-c/route_start.json",encoding="utf-8"))
print({k:(v if not isinstance(v,(list,dict)) else type(v).__name__) for k,v in rs.items()})
