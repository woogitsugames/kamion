"""Compact query log of all photo-source searches. usage: querylog.py dl_dir out.json"""
import json, sys
dl = sys.argv[1]
p = json.load(open(dl + '/pano_search.json')); c = json.load(open(dl + '/commons.json')); r = json.load(open(dl + '/commons_route.json')); s = json.load(open(dl + '/csearch.json'))
log = {"panoramax": {"queried_at": p["queried_at"], "tiles": {k: {h.split('/')[2]: {"url": v.get("url"), "status": v.get("status"), "n": v.get("n"), "error": v.get("error"),
        "items": [{"id": f["id"], "lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1], "datetime": f["properties"].get("datetime"), "view:azimuth": f["properties"].get("view:azimuth")} for f in v.get("features", [])]} for h, v in t.items()} for k, t in p["tiles"].items()}},
       "commons_geosearch_tiles": {"queried_at": c["queried_at"], "tiles": {k: {"params": v["params"], "n": v["n"]} for k, v in c["geo"].items()}, "categories": {k: len(v) for k, v in c["cats"].items()}},
       "commons_geosearch_route": {"queried_at": r["queried_at"], "queries": r["queries"]},
       "commons_text_search": {"queried_at": s["queried_at"], "queries": {k: v["total"] for k, v in s["queries"].items()}},
       "openverse": {"date": "2026-11-15", "note": "api.openverse.org: page_size>20 -> error for anonymous; q=Knyszyn page_size=20 -> 20 results, all source=wikimedia (no extra Flickr CC)"},
       "kartaview": {"date": "2026-11-15", "note": "api.openstreetcam.org TLS error (curl 60, certificate name mismatch); kartaview.org page 200 but no anonymous API -> gap"},
       "mapillary": {"note": "no token (COMMON.md) - not queried"}}
json.dump(log, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
