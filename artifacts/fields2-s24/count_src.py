import json,glob,collections,re,sys
for t in sys.argv[1:]:
    c=collections.Counter()
    for f in glob.glob(f"Data/raw/derived/{t}/world/instances*.json"):
        d=json.load(open(f,encoding="utf8"))
        items=d if isinstance(d,list) else d.get("instances",d)
        if isinstance(items,dict): print(f, list(items.keys())[:8]); break
        for i in items:
            if not isinstance(i,dict): print(type(i), str(i)[:200]); break
            s=str(i.get("src",""))
            if not str(i.get("p","")).startswith("tree"): continue
            k=re.sub(r"\{?[0-9A-Fa-f\-]{8,}\}?|\d+","#",s)
            c[k]+=1
    print(t,c.most_common(25))
