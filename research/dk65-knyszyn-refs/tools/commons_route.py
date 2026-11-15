"""Commons geosearch along route (every 400 m, r=300 m) km 8.6-28.44 + Rynek r=450; distance of each file to route polyline."""
import json, math, sys, time, requests
from pyproj import Transformer
UA = {"User-Agent": "research-client/1.0 (generic)"}
API = "https://commons.wikimedia.org/w/api.php"
R = '/workspace/kamion/.claude/worktrees/agent-ab851075007c7ffbb/'
pl = json.load(open(R + 'docs/reports/map/dk65_route_plan.json'))['variants']['A_old_road']['polyline']
bw = Transformer.from_crs('EPSG:2180', 'EPSG:4326', always_xy=True); fw = Transformer.from_crs('EPSG:4326', 'EPSG:2180', always_xy=True)
cum = [0]
for i in range(1, len(pl)): cum.append(cum[-1] + math.dist(pl[i - 1], pl[i]))
def at(s):
    i = next(i for i in range(1, len(cum)) if cum[i] >= s); f = (s - cum[i - 1]) / (cum[i] - cum[i - 1])
    return pl[i - 1][0] + f * (pl[i][0] - pl[i - 1][0]), pl[i - 1][1] + f * (pl[i][1] - pl[i - 1][1])
def get(p):
    for a in range(5):
        r = requests.get(API, params={**p, "format": "json"}, headers=UA, timeout=60)
        if r.status_code == 200: return r.json()
        time.sleep(5 * (a + 1))
    raise SystemExit(r.status_code)
centres = [at(s) for s in range(8600, 28400, 400)] + [(761040.0, 612380.0)]
titles = set(); log = []
for (x, y) in centres:
    lon, lat = bw.transform(x, y)
    r_ = 450 if (x, y) == (761040.0, 612380.0) else 300
    p = {"action": "query", "list": "geosearch", "gscoord": f"{lat:.6f}|{lon:.6f}", "gsradius": r_, "gslimit": 500, "gsnamespace": 6}
    j = get(p); h = j.get("query", {}).get("geosearch", [])
    log.append({"lat": round(lat, 6), "lon": round(lon, 6), "r": r_, "n": len(h)})
    titles |= {e["title"] for e in h}; time.sleep(0.5)
print("titles", len(titles))
files = {}
tl = sorted(titles)
for i in range(0, len(tl), 40):
    p = {"action": "query", "titles": "|".join(tl[i:i + 40]), "prop": "imageinfo|coordinates", "iiprop": "extmetadata|url|sha1|size|mime", "iiurlwidth": 1600, "coprop": "type|name|dim|country|region|globe", "coprimary": "all", "colimit": 500}
    j = get(p)
    for pg in j["query"]["pages"].values():
        ii = (pg.get("imageinfo") or [{}])[0]; em = ii.get("extmetadata", {})
        co = pg.get("coordinates") or []
        files[pg["title"]] = {"coords": co, "url": ii.get("url"), "thumb": ii.get("thumburl"), "page": ii.get("descriptionurl"), "sha1": ii.get("sha1"), "w": ii.get("width"), "h": ii.get("height"), "mime": ii.get("mime"),
            "license": em.get("LicenseShortName", {}).get("value"), "artist": em.get("Artist", {}).get("value"), "date": em.get("DateTimeOriginal", {}).get("value"), "desc": em.get("ImageDescription", {}).get("value"),
            "gps_heading": em.get("GPSImgDirection", {}).get("value") if em.get("GPSImgDirection") else None}
        if co:
            c = co[0]; X, Y = fw.transform(c["lon"], c["lat"])
            best = (1e9, 0)
            for k in range(1, len(pl)):
                ax, ay = pl[k - 1]; bx, by = pl[k]; dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
                t = max(0, min(1, ((X - ax) * dx + (Y - ay) * dy) / L2)) if L2 else 0
                d = math.dist((X, Y), (ax + t * dx, ay + t * dy))
                if d < best[0]: best = (d, (cum[k - 1] + t * math.sqrt(L2)) / 1000)
            files[pg["title"]].update({"x": round(X, 1), "y": round(Y, 1), "dist_route_m": round(best[0], 1), "km": round(best[1], 3)})
    time.sleep(1)
json.dump({"queried_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "queries": log, "files": files}, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
