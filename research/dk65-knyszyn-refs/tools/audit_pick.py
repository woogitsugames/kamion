"""Audit 20 %: random.seed(20261115); pick ceil(0.2*N) rows; re-hash local files, re-check source URLs (HTTP)."""
import csv, random, math, hashlib, json, sys, time, requests
OUT = sys.argv[1]
UA = {"User-Agent": "research-client/1.0 (generic)"}
rows = list(csv.DictReader(open(OUT + "manifest.csv", encoding="utf-8")))
random.seed(20261115)
k = math.ceil(0.2 * len(rows)); pick = sorted(random.sample(range(len(rows)), k))
res = []
for i in pick:
    r = rows[i]; chk = {"id": r["id"], "temat": r["temat"], "element": r["element"], "plik": r["plik_lokalny"]}
    if r["plik_lokalny"]:
        chk["sha_ok"] = hashlib.sha256(open(OUT + r["plik_lokalny"], "rb").read()).hexdigest() == r["sha256"]
    u = r["url_źródła"]
    if u.startswith("http"):
        try:
            if "geoportal" in u:
                q = requests.get(u, headers=UA, timeout=90); chk["url_status"] = q.status_code; chk["url_ct"] = q.headers.get("content-type")
            else:
                q = requests.get(u, headers=UA, timeout=60, stream=True); chk["url_status"] = q.status_code
        except Exception as e:
            chk["url_status"] = f"ERR {type(e).__name__}"
        time.sleep(1)
    res.append(chk); print(chk, flush=True)
json.dump({"seed": 20261115, "n_rows": len(rows), "n_pick": k, "picked": res}, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
