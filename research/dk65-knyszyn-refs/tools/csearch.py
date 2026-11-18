"""Commons full-text search (ns 6), several queries, paginate; then imageinfo for all hits. args: out.json queries..."""
import json, sys, time, requests
UA = {"User-Agent": "research-client/1.0 (generic)"}
API = "https://commons.wikimedia.org/w/api.php"
def get(p):
    for a in range(6):
        try:
            r = requests.get(API, params={**p, "format": "json"}, headers=UA, timeout=60)
            if r.status_code == 200: return r.json()
        except Exception: pass
        time.sleep(4 * (a + 1))
    raise SystemExit("fail")
out = {"queried_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "queries": {}, "files": {}}
titles = set()
for q in sys.argv[2:]:
    off = 0; got = []
    while True:
        j = get({"action": "query", "list": "search", "srnamespace": 6, "srlimit": 500, "sroffset": off, "srsearch": q})
        got += [h["title"] for h in j["query"]["search"]]
        if "continue" in j and off < 1500: off = j["continue"]["sroffset"]; time.sleep(1)
        else: break
    out["queries"][q] = {"total": j["query"].get("searchinfo", {}).get("totalhits"), "titles": got}
    titles |= set(got); print(q, len(got), flush=True); time.sleep(1)
tl = sorted(titles)
for i in range(0, len(tl), 40):
    j = get({"action": "query", "titles": "|".join(tl[i:i + 40]), "prop": "imageinfo|coordinates", "iiprop": "extmetadata|url|sha1|size|mime", "iiurlwidth": 1600, "coprop": "type|dim", "coprimary": "all", "colimit": 500})
    for pg in j["query"]["pages"].values():
        ii = (pg.get("imageinfo") or [{}])[0]; em = ii.get("extmetadata", {})
        out["files"][pg["title"]] = {"coords": pg.get("coordinates"), "url": ii.get("url"), "thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"), "sha1": ii.get("sha1"), "w": ii.get("width"), "h": ii.get("height"), "mime": ii.get("mime"),
            "license": em.get("LicenseShortName", {}).get("value"), "artist": em.get("Artist", {}).get("value"), "date": em.get("DateTimeOriginal", {}).get("value"), "desc": em.get("ImageDescription", {}).get("value"), "cats": em.get("Categories", {}).get("value")}
    time.sleep(1)
json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
print("files", len(out["files"]))
