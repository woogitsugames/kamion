#!/usr/bin/env python3
"""Wybor kadrow do obejrzenia (rozstawione wzdluz ulic) + pobranie do files/frames/ + widoki <=960 px i wycinki 3x w files/_view/.
Wynik: frames_selected.json (id, zrodlo, url_pliku, sha256, lat, lon, azymut, data, ulica, way)."""
import json, math, hashlib, pathlib, urllib.request, urllib.parse, time, sys
from PIL import Image
D = pathlib.Path(__file__).parent
F = D / "files" / "frames"; V = D / "files" / "_view"; F.mkdir(parents=True, exist_ok=True); V.mkdir(parents=True, exist_ok=True)
def dist(a, b):
    return math.hypot((a[0] - b[0]) * 111320, (a[1] - b[1]) * 111320 * math.cos(math.radians(a[0])))
cand = json.load(open(D / "files" / "candidates.json")); kv = json.load(open(D / "files" / "kv_seq.json"))
sel = []
def spaced(items, n, mind):
    out = []
    for it in items:
        if all(dist((it["lat"], it["lon"]), (o["lat"], o["lon"])) > mind for o in out): out.append(it)
    step = max(1, len(out) // n)
    return out[::step][:n]
pm = sorted([c for c in cand.values() if c["src"] == "panoramax"], key=lambda c: c["datetime"])
for st, n in (("Generała Stanisława Maczka", 5), ("Aleja Tysiąclecia Państwa Polskiego", 3), ("Rondo Krzysztofa Jakuba Putry Wicemarszałka Sejmu RP", 2), ("Generała Władysława Andersa", 1)):
    sel += spaced([c for c in pm if c["street"] == st and c["d_axis_m"] < 30], n, 150)
def kvs(seq, st, n, mind=250):
    it = sorted([k for k in kv if k["seq"] == seq and k["street"] == st], key=lambda k: int(k["seq_index"]))
    return spaced(it, n, mind)
sel += kvs("3686129", "Generała Władysława Andersa", 10)
sel += kvs("3686129", "Generała Stanisława Maczka", 2, 600)
sel += kvs("1155711", "Aleja Tysiąclecia Państwa Polskiego", 8, 300)
sel += kvs("2769366", "Generała Władysława Andersa", 2, 1200)
P11 = {"P11-001": "20240623_142113_June_2024_in_Białystok.jpg", "P11-007": "20230903_134647_September_2023_in_Białystok.jpg",
       "P11-010": "20230903_134534_September_2023_in_Białystok.jpg", "P11-012": "8869_November_2022_in_Białystok.jpg",
       "P11-097": "20230903_134802_September_2023_in_Białystok.jpg", "P11-023": "20240623_140411_June_2024_in_Białystok.jpg",
       "P11-024": "20240623_140200_June_2024_in_Białystok.jpg", "P11-063": "20240623_124644_June_2024_in_Białystok.jpg",
       "P11-056": "20230814_175724_August_2023_in_Białystok.jpg", "P11-079": "20230814_174936_August_2023_in_Białystok.jpg"}
import csv
p11 = {x["id"]: x for x in csv.DictReader(open(D.parents[1] / "mistral" / "p11-dojlidy-photos" / "manifest.csv", encoding="utf-8"))}
for pid, fn in P11.items():
    h = hashlib.md5(fn.encode()).hexdigest(); q = urllib.parse.quote(fn)
    x = p11[pid]
    sel.append({"src": "commons", "id": pid, "lat": float(x["lat"]), "lon": float(x["lon"]), "datetime": x["data_zdjęcia"], "azimuth": None,
                "file": f"https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/1280px-{q}", "page": x["url_źródła"],
                "street": x["ulica"], "way": "", "license": x["licencja"], "author": x["autor"]})
out = []
for i, s in enumerate(sel, 1):
    url = s.get("sd") or s.get("file")
    name = f"F{i:02d}_{s['src']}_{str(s['id'])[:8]}.jpg"; p = F / name
    if not p.exists():
        for a in range(4):
            try:
                p.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-client/1.0"}), timeout=90).read()); break
            except Exception as ex:
                print("ERR", url, ex, file=sys.stderr); time.sleep(4 * (a + 1))
    if not p.exists(): continue
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    im = Image.open(p).convert("RGB"); w, h = im.size
    im.resize((960, round(h * 960 / w)), Image.LANCZOS).save(V / f"F{i:02d}_view.jpg", quality=88)
    # wycinki 3x: lewy-dolny i prawy-dolny (1/3 szerokosci, pas 42-80 % wysokosci) -> 960 px szerokosci kazdy, jeden nad drugim
    cw = w // 3; y0, y1 = int(h * 0.42), int(h * 0.80)
    L = im.crop((0, y0, cw, y1)); R = im.crop((w - cw, y0, w, y1))
    ch = round((y1 - y0) * 960 / cw)
    m = Image.new("RGB", (960, ch * 2 + 6), "white"); m.paste(L.resize((960, ch), Image.LANCZOS), (0, 0)); m.paste(R.resize((960, ch), Image.LANCZOS), (0, ch + 6))
    m.save(V / f"F{i:02d}_crop3x.jpg", quality=88)
    out.append({"n": i, "file_local": name, "src": s["src"], "src_id": s["id"], "url_pliku": url, "url_zrodla": s.get("self") or s.get("page") or (f"https://kartaview.org/details/{s.get('seq')}/{s.get('seq_index')}" if s["src"] == "kartaview" else ""),
                "sha256": sha, "bytes": p.stat().st_size, "px": [w, h], "lat": round(s["lat"], 6), "lon": round(s["lon"], 6), "azimuth": s.get("azimuth"),
                "datetime": s.get("datetime"), "street": s["street"], "way": s.get("way"), "seq": s.get("seq"), "seq_index": s.get("seq_index"),
                "license": s.get("license") or ("CC-BY-SA-4.0" if s["src"] != "commons" else ""), "author": s.get("author") or (",".join(s.get("producer") or []) if s["src"] == "panoramax" else "UNVERIFIED (API nie zwraca autora)")})
    print(i, name, s["street"][:20], s.get("datetime"), s.get("azimuth"), w, h)
json.dump(out, open(D / "frames_selected.json", "w"), ensure_ascii=False, indent=1)
print(len(out), sum(o["bytes"] for o in out) / 1e6, "MB")
