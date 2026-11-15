#!/usr/bin/env python3
"""Panoramax (meta-katalog api.panoramax.xyz): wszystkie zdjecia w bboxie R9 przez /api/search z podzialem bboxu na kafle (limit 1000/zapytanie;
kafel z >=1000 wynikow jest dzielony na 4). Wynik: files/panoramax_raw/items.jsonl + panoramax/summary.json."""
import subprocess, json, pathlib, datetime, time, sys
root = pathlib.Path(__file__).resolve().parents[1]
raw = root / "files/panoramax_raw"; raw.mkdir(parents=True, exist_ok=True); (root / "panoramax").mkdir(exist_ok=True)
BB = (22.951, 53.052, 23.306, 53.249)
items = {}; log = []
def q(bb, depth=0):
    url = f"https://api.panoramax.xyz/api/search?bbox={bb[0]:.6f},{bb[1]:.6f},{bb[2]:.6f},{bb[3]:.6f}&limit=1000"
    for a in range(4):
        r = subprocess.run(["curl", "-sS", "-m", "120", "-A", "research-fetch/1.0", "-w", "\n%{http_code}", url], capture_output=True, text=True)
        body, _, code = r.stdout.rpartition("\n")
        if code == "200": break
        time.sleep(5 * (a + 1))
    else:
        log.append({"url": url, "http": code, "n": None}); return
    fs = json.loads(body).get("features", [])
    log.append({"url": url, "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "http": code, "n": len(fs)})
    print(depth, url, len(fs), file=sys.stderr)
    if len(fs) >= 1000 and depth < 8:
        mx, my = (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2
        for sub in ((bb[0], bb[1], mx, my), (mx, bb[1], bb[2], my), (bb[0], my, mx, bb[3]), (mx, my, bb[2], bb[3])): q(sub, depth + 1)
    else:
        for f in fs: items[f["id"]] = f
    time.sleep(0.5)
q(BB)
with open(raw / "items.jsonl", "w") as f:
    for it in items.values():
        p = it["properties"]; a = it.get("assets", {})
        f.write(json.dumps({"id": it["id"], "collection": it.get("collection"), "lon": it["geometry"]["coordinates"][0], "lat": it["geometry"]["coordinates"][1],
            "datetime": p.get("datetime"), "azimuth": p.get("view:azimuth"), "fov": (p.get("pers:interior_orientation") or {}).get("field_of_view"),
            "license": p.get("license"), "producer": [x.get("name") for x in it.get("providers", [])], "original_file:name": p.get("original_file:name"),
            "model": (p.get("pers:interior_orientation") or {}).get("camera_model"),
            "hd": (a.get("hd") or {}).get("href"), "sd": (a.get("sd") or {}).get("href"), "thumb": (a.get("thumb") or {}).get("href")}, ensure_ascii=False) + "\n")
json.dump({"bbox_wgs84": BB, "zapytania": log, "liczba_zdjec": len(items)}, open(root / "panoramax/search_log.json", "w"), indent=1)
print(len(items))
