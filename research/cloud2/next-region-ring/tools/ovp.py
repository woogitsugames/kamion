#!/usr/bin/env python3
"""Uruchamia zapytanie Overpass (mirror maps.mail.ru — overpass-api.de niedostepny przez proxy sesji),
zapisuje surowy wynik i dopisuje wpis do overpass/_log.jsonl (zapytanie, UTC, timestamp_osm_base, liczba elementow)."""
import sys, json, time, datetime, subprocess, pathlib, hashlib
URL = "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
def run(name, query, outdir):
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{name}.json"
    for attempt in range(5):
        t = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        r = subprocess.run(["curl", "-sS", "-m", "300", "-A", "kamion-research/1.0", "-o", str(out), "-w", "%{http_code}",
                            "--data-urlencode", f"data={query}", URL], capture_output=True, text=True)
        code = r.stdout.strip()
        try:
            d = json.loads(out.read_text())
            if code == "200" and "elements" in d and not d.get("remark"):
                break
            print("remark:", d.get("remark"), file=sys.stderr)
        except Exception as e:
            print("attempt", attempt, code, r.stderr[:200], e, file=sys.stderr)
        time.sleep(10 * (attempt + 1))
    else:
        raise SystemExit(f"FAILED {name}")
    rec = {"name": name, "utc": t, "endpoint": URL, "http": code, "timestamp_osm_base": d["osm3s"]["timestamp_osm_base"],
           "elements": len(d["elements"]), "bytes": out.stat().st_size,
           "sha256": hashlib.sha256(out.read_bytes()).hexdigest(), "query": query}
    return rec, d
if __name__ == "__main__":
    name, qfile, outdir, log = sys.argv[1:5]
    rec, _ = run(name, open(qfile).read().strip(), outdir)
    with open(log, "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print({k: rec[k] for k in ("name", "utc", "elements", "bytes", "timestamp_osm_base")})
