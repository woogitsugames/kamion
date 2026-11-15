import json, requests, sys, xml.etree.ElementTree as ET
UA = {"User-Agent": "research-client/1.0 (generic)"}
R = '/workspace/kamion/.claude/worktrees/agent-ab851075007c7ffbb/'
d = json.load(open(R + 'docs/reports/map/dk65_route_plan.json'))['variants']['A_old_road']
ws = [w for w in d['ways'] if w['km_end'] >= 8.7]
ids = [w['way_id'] for w in ws]
out = {}
for k in range(0, len(ids), 50):
    r = requests.get("https://api.openstreetmap.org/api/0.6/ways", params={"ways": ",".join(map(str, ids[k:k + 50]))}, headers=UA, timeout=60)
    r.raise_for_status()
    for w in ET.fromstring(r.content).iter("way"):
        out[int(w.get("id"))] = {"version": w.get("version"), "timestamp": w.get("timestamp"), "tags": {t.get("k"): t.get("v") for t in w.iter("tag")}}
rows = []
for w in ws:
    o = out.get(w['way_id'], {})
    rows.append({"way_id": w['way_id'], "km_start": w['km_start'], "km_end": w['km_end'], "length_m": w['length_m'], **{"osm_" + k: v for k, v in o.items() if k != 'tags'}, "tags": o.get('tags', {})})
json.dump(rows, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
keys = ["highway", "ref", "name", "lanes", "width", "shoulder", "surface", "maxspeed", "lit", "sidewalk", "cycleway", "bridge", "junction", "overtaking", "est_width", "lane_markings", "smoothness"]
for r_ in rows:
    t = r_['tags']
    print(f"{r_['way_id']} km{r_['km_start']:.2f}-{r_['km_end']:.2f} v{r_.get('osm_version')} {r_.get('osm_timestamp','')[:10]} | " + "; ".join(f"{k}={t[k]}" for k in keys if k in t) + " | other: " + ",".join(k for k in t if k not in keys)[:150])
