#!/usr/bin/env python3
"""Duze zapytania Overpass kaflami (mirror maps.mail.ru ma limit bramy ~60 s): bbox dzielony na NxM, wyniki scalane po (type,id).
Uzycie: ovp_tiled.py <name> <nx> <ny> '<statement z {bb}>' '<out>'   -> files/overpass_raw/<name>.json + wpis w overpass/_log.jsonl"""
import sys, json, pathlib, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from ovp import run
root = pathlib.Path(__file__).resolve().parents[1]
name, nx, ny, stmt, outs = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
S, W, N, E = 53.052, 22.951, 53.249, 23.306
els = {}; recs = []
tmp = root / "files/overpass_raw/_tiles"
for i in range(nx):
    for j in range(ny):
        bb = f"{S + (N - S) * j / ny:.5f},{W + (E - W) * i / nx:.5f},{S + (N - S) * (j + 1) / ny:.5f},{W + (E - W) * (i + 1) / nx:.5f}"
        q = f"[out:json][timeout:55];\n({stmt.replace('{bb}', bb)});\n{outs}"
        rec, d = run(f"{name}_{i}_{j}", q, tmp)
        for e in d["elements"]: els[(e["type"], e["id"])] = e
        recs.append(rec); print(rec["name"], rec["utc"], rec["elements"], rec["bytes"], flush=True)
out = root / "files/overpass_raw" / f"{name}.json"
json.dump({"osm3s": {"timestamp_osm_base": min(r["timestamp_osm_base"] for r in recs)}, "elements": list(els.values())}, open(out, "w"), ensure_ascii=False)
rec = {"name": name, "utc": recs[0]["utc"], "utc_end": recs[-1]["utc"], "endpoint": recs[0]["endpoint"], "http": "200", "timestamp_osm_base": min(r["timestamp_osm_base"] for r in recs),
       "timestamp_osm_base_max": max(r["timestamp_osm_base"] for r in recs), "elements": len(els), "bytes": out.stat().st_size, "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
       "tiles": f"{nx}x{ny} (rowny podzial bboxu WGS84 {S},{W},{N},{E}); scalone po (type,id)", "query": f"[out:json][timeout:55];\n({stmt});\n{outs}   # {{bb}} = kafel"}
with open(root / "overpass/_log.jsonl", "a") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print(rec["name"], rec["elements"], rec["bytes"])
