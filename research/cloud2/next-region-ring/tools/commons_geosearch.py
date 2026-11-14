#!/usr/bin/env python3
"""Wikimedia Commons list=geosearch (gsbbox, namespace 6, gsprimary=all) kaflami 0.04x0.07 deg po bboxie R9 (podzial przy 500 wynikach).
Wynik: files/commons_raw/geosearch.jsonl + commons/search_log.json."""
import subprocess, json, pathlib, datetime, time, sys, urllib.parse
root = pathlib.Path(__file__).resolve().parents[1]
raw = root / "files/commons_raw"; raw.mkdir(parents=True, exist_ok=True); (root / "commons").mkdir(exist_ok=True)
S, W, N, E = 53.052, 22.951, 53.249, 23.306
UA = "KamionResearch/1.0 (open-data research; low volume)"
res = {}; log = []
def q(s, w, n, e, depth=0):
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "list": "geosearch", "gsbbox": f"{n:.5f}|{w:.5f}|{s:.5f}|{e:.5f}",
        "gsnamespace": 6, "gslimit": 500, "gsprimary": "all", "format": "json"})
    for a in range(6):
        r = subprocess.run(["curl", "-sS", "-m", "60", "-A", UA, "-w", "\n%{http_code}", url], capture_output=True, text=True)
        body, _, code = r.stdout.rpartition("\n")
        if code == "200": break
        time.sleep(15 * (a + 1))
    else:
        log.append({"url": url, "http": code, "n": None}); print("FAIL", code, file=sys.stderr); return
    gs = json.loads(body).get("query", {}).get("geosearch", [])
    log.append({"url": url, "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "http": code, "n": len(gs)})
    print(depth, f"{s:.3f},{w:.3f},{n:.3f},{e:.3f}", len(gs), file=sys.stderr, flush=True)
    time.sleep(2)
    if len(gs) >= 500 and depth < 6:
        ms, mw = (s + n) / 2, (w + e) / 2
        for sub in ((s, w, ms, mw), (s, mw, ms, e), (ms, w, n, mw), (ms, mw, n, e)): q(*sub, depth + 1)
    else:
        for g in gs: res[g["pageid"]] = g
la = S
while la < N - 1e-9:
    lo = W
    while lo < E - 1e-9:
        q(la, lo, min(N, la + 0.04), min(E, lo + 0.07)); lo += 0.07
    la += 0.04
with open(raw / "geosearch.jsonl", "w") as f:
    for g in res.values(): f.write(json.dumps(g, ensure_ascii=False) + "\n")
json.dump({"bbox_wgs84": [S, W, N, E], "liczba_zapytan": len(log), "http_nie_200": sum(1 for l in log if l["http"] != "200"), "liczba_plikow": len(res), "zapytania": log},
          open(root / "commons/search_log.json", "w"), indent=0)
print(len(res))
