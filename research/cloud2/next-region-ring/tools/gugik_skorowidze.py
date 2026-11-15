#!/usr/bin/env python3
"""Skorowidze GUGiK (WFS 1.0.0, EPSG:2180) dla proponowanego bboxu R9: ORTO, NMT, NMPT (lata 2018-2026).
Zapisuje gugik/skorowidze_summary.json (zbiorczo per produkt/rok) i gugik/skorowidze_sheets.csv (arkusze najnowszych rocznikow).
Surowe XML -> files/gugik_raw/ (poza gitem)."""
import subprocess, re, json, csv, pathlib, datetime, time, collections, sys
BBOX = (764683, 584959, 787211, 605439)
W = "https://mapy.geoportal.gov.pl/wss/service/PZGIK"
SVC = {"ORTO": (f"{W}/ORTO/WFS/Skorowidze", "gugik:SkorowidzOrtofomapy{y}"),
       "NMT": (f"{W}/NumerycznyModelTerenuEVRF2007/WFS/Skorowidze", "gugik:SkorowidzNMT{y}"),
       "NMPT": (f"{W}/NumerycznyModelPokryciaTerenuEVRF2007/WFS/Skorowidze", "gugik:SkorowidzNMPT{y}")}
root = pathlib.Path(__file__).resolve().parents[1]
raw = root / "files" / "gugik_raw"; raw.mkdir(parents=True, exist_ok=True)
(root / "gugik").mkdir(exist_ok=True)
summary = []; sheets = []
for prod, (ep, tmpl) in SVC.items():
    for y in range(2018, 2027):
        layer = tmpl.format(y=y)
        url = f"{ep}?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&TYPENAME={layer}&SRSNAME=EPSG:2180&BBOX={','.join(map(str, BBOX))}"
        out = raw / f"{prod}_{y}.xml"
        utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        r = subprocess.run(["curl", "-sS", "-m", "180", "-A", "research-fetch/1.0", "-o", str(out), "-w", "%{http_code}", url], capture_output=True, text=True)
        code = r.stdout.strip()
        x = out.read_text(encoding="utf-8", errors="replace") if out.exists() else ""
        feats = re.findall(r"<gml:featureMember>(.*?)</gml:featureMember>", x, flags=re.S)
        rows = []
        for f in feats:
            a = dict(re.findall(r"<gugik:(\w+)>([^<]*)</gugik:\w+>", f))
            m = re.search(r"<gml:Box[^>]*>\s*<gml:coordinates[^>]*>([^<]*)<", f)
            a["box"] = m.group(1).strip() if m else ""
            a["fid"] = re.search(r'fid="([^"]+)"', f).group(1)
            rows.append(a)
        def cnt(k): return dict(collections.Counter(a.get(k, "") for a in rows))
        s = {"produkt": prod, "rok_warstwy": y, "layer": layer, "url": url, "utc": utc, "http": code, "arkuszy": len(rows),
             "akt_data_min": min((a.get("akt_data", "") for a in rows), default=""), "akt_data_max": max((a.get("akt_data", "") for a in rows), default=""),
             "piksel": cnt("piksel") if prod == "ORTO" else None, "kolor": cnt("kolor") if prod == "ORTO" else None,
             "char_przestrz": cnt("char_przestrz") if prod != "ORTO" else None, "format": cnt("format") if prod != "ORTO" else None,
             "uklad_h": cnt("uklad_h") if prod != "ORTO" else None, "modul": cnt("modul_archiwizacji"), "nr_zglosz": cnt("nr_zglosz"),
             "suma_wlk_pliku_mb": sum(float(a.get("wlk_pliku_mb") or 0) for a in rows) if prod == "ORTO" else None}
        summary.append(s)
        for a in rows:
            sheets.append({"produkt": prod, "rok_warstwy": y, **{k: a.get(k, "") for k in ("fid", "godlo", "akt_rok", "akt_data", "piksel", "kolor", "char_przestrz", "format", "modul_archiwizacji", "nr_zglosz", "wlk_pliku_mb", "url_do_pobrania", "box")}})
        print(prod, y, code, len(rows), s["akt_data_min"], s["akt_data_max"], file=sys.stderr)
        time.sleep(1.0)
json.dump({"bbox_epsg2180": BBOX, "wyniki": summary}, open(root / "gugik" / "skorowidze_summary.json", "w"), ensure_ascii=False, indent=1)
with open(root / "files" / "gugik_raw" / "sheets_all.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(sheets[0].keys())); w.writeheader(); w.writerows(sheets)
