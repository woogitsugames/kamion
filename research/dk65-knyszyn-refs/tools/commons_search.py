"""Commons geosearch (namespace 6) per tile centre r=1450 m + category members; then imageinfo. out json."""
import json, sys, time, requests
UA = {"User-Agent": "research-client/1.0 (generic)"}
API = "https://commons.wikimedia.org/w/api.php"
tiles = json.load(open(sys.argv[1]))
def get(p):
    for a in range(5):
        r = requests.get(API, params={**p, "format": "json"}, headers=UA, timeout=60)
        if r.status_code == 200: return r.json()
        time.sleep(5 * (a + 1))
    raise SystemExit(r.status_code)
out = {"queried_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "geo": {}, "cats": {}, "files": {}}
titles = set()
for k, b in tiles.items():
    lat = (b[1] + b[3]) / 2; lon = (b[0] + b[2]) / 2
    p = {"action": "query", "list": "geosearch", "gscoord": f"{lat}|{lon}", "gsradius": 1450, "gslimit": 500, "gsnamespace": 6}
    j = get(p); hits = j.get("query", {}).get("geosearch", [])
    out["geo"][k] = {"params": p, "n": len(hits), "titles": [h["title"] for h in hits]}
    titles |= {h["title"] for h in hits}
    print(k, len(hits), flush=True); time.sleep(1)
for cat in sys.argv[3:]:
    p = {"action": "query", "list": "categorymembers", "cmtitle": cat, "cmtype": "file|subcat", "cmlimit": 500}
    j = get(p); mem = j.get("query", {}).get("categorymembers", [])
    out["cats"][cat] = [m["title"] for m in mem]
    titles |= {m["title"] for m in mem if m["title"].startswith("File:")}
    print(cat, len(mem), flush=True); time.sleep(1)
tl = sorted(titles)
for i in range(0, len(tl), 40):
    p = {"action": "query", "titles": "|".join(tl[i:i + 40]), "prop": "imageinfo|coordinates", "iiprop": "extmetadata|url|sha1|size|mime", "iiurlwidth": 1600, "colimit": 500}
    j = get(p)
    for pg in j["query"]["pages"].values():
        ii = (pg.get("imageinfo") or [{}])[0]; em = ii.get("extmetadata", {})
        out["files"][pg["title"]] = {"coords": pg.get("coordinates"), "url": ii.get("url"), "thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"), "sha1": ii.get("sha1"),
            "w": ii.get("width"), "h": ii.get("height"), "mime": ii.get("mime"),
            "license": em.get("LicenseShortName", {}).get("value"), "artist": em.get("Artist", {}).get("value"), "date": em.get("DateTimeOriginal", {}).get("value"),
            "desc": em.get("ImageDescription", {}).get("value"), "cats": em.get("Categories", {}).get("value")}
    time.sleep(1)
json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
print("files", len(out["files"]))
