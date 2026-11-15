#!/usr/bin/env python3
"""Commons geosearch po siatce (radius 500 m) + imageinfo; oznacza pliki juz uzyte w research/ (dowolny manifest)."""
import json, time, pathlib, requests, datetime, re, urllib.parse, glob
ROOT = pathlib.Path(__file__).resolve().parent.parent; REPO = ROOT.parents[2]
AREAS = {"trasa_c": (53.1455, 23.1437, 53.1680, 23.1885), "dojlidy": (53.0937, 23.1640, 53.1110, 23.2110)}
API = "https://commons.wikimedia.org/w/api.php"; H = {"User-Agent": "research-script/1.0 (generic client)"}
used = set()
for f in glob.glob(str(REPO / "research/**/manifest*.csv"), recursive=True):
    if "cloud2/bialystok-building-typology" in f: continue
    for m in re.findall(r"File:([^\s\",]+)", open(f, encoding="utf-8", errors="ignore").read()):
        used.add(urllib.parse.unquote(m).replace("_", " "))
print("used", len(used))
def get(params):
    for i in range(5):
        try:
            r = requests.get(API, params=params, headers=H, timeout=60)
            if r.status_code == 200: return r.json()
        except Exception: pass
        time.sleep(2 * 2**i)
    return {}
for name, (s, w, n, e) in AREAS.items():
    pages = {}; lat = s + 0.003
    while lat < n + 0.002:
        lon = w + 0.004
        while lon < e + 0.003:
            d = get({"action": "query", "list": "geosearch", "gscoord": f"{lat}|{lon}", "gsradius": 500, "gslimit": 500, "gsnamespace": 6, "format": "json"})
            for p in d.get("query", {}).get("geosearch", []): pages[p["pageid"]] = p
            lon += 0.007; time.sleep(0.2)
        lat += 0.0055
    ids = sorted(pages); info = {}
    for i in range(0, len(ids), 50):
        d = get({"action": "query", "pageids": "|".join(map(str, ids[i:i+50])), "prop": "imageinfo", "iiprop": "url|size|sha1|extmetadata|mime", "iiextmetadatafilter": "LicenseShortName|Artist|DateTimeOriginal|ImageDescription|Categories", "format": "json"})
        info.update(d.get("query", {}).get("pages", {}))
    out = []
    for pid in ids:
        p = pages[pid]; ii = (info.get(str(pid), {}).get("imageinfo") or [{}])[0]; em = ii.get("extmetadata", {})
        t = p["title"][5:]
        out.append({"title": t, "lat": p["lat"], "lon": p["lon"], "url": ii.get("url"), "w": ii.get("width"), "h": ii.get("height"), "mime": ii.get("mime"),
                    "license": em.get("LicenseShortName", {}).get("value"), "artist": re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", "")).strip(),
                    "date": em.get("DateTimeOriginal", {}).get("value"), "desc": re.sub("<[^>]+>", "", em.get("ImageDescription", {}).get("value", ""))[:200],
                    "cats": em.get("Categories", {}).get("value", "")[:300], "used_in_repo": t in used})
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    json.dump({"fetched_utc": ts, "files": out}, open(ROOT / "data" / f"commons_{name}.json", "w"), ensure_ascii=False, indent=0)
    print(name, len(out), "new", sum(not o["used_in_repo"] for o in out), ts)
