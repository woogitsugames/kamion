"""Re-query ortho sheet index (per-feature parse) for points in meta.json files; updates 'sheets' and prints newest."""
import json, sys, re, time, requests
UA = {"User-Agent": "research-client/1.0 (generic)"}
WFS = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WFS/Skorowidze"
for mf in sys.argv[1:]:
    m = json.load(open(mf))
    for pid, v in m.items():
        x, y = v["x"], v["y"]; sh = []
        for yr in range(2021, 2027):
            p = {"SERVICE": "WFS", "VERSION": "1.0.0", "REQUEST": "GetFeature", "TYPENAME": f"gugik:SkorowidzOrtofomapy{yr}", "SRSNAME": "EPSG:2180", "BBOX": f"{x-2},{y-2},{x+2},{y+2}"}
            try: t = requests.get(WFS, params=p, headers=UA, timeout=60).text
            except Exception: continue
            for feat in re.split(r"<gml:featureMember>", t)[1:]:
                g = lambda k: (re.search(f"<gugik:{k}>([^<]*)</gugik:{k}>", feat) or [None, None])[1]
                sh.append([g("akt_data"), g("piksel"), g("godlo"), g("url_do_pobrania")])
            time.sleep(0.3)
        sh = sorted({tuple(s) for s in sh})
        v["sheets"] = [list(s) for s in sh]
        print(mf.split('/')[-2], pid, sh[-1][:3] if sh else None, flush=True)
    json.dump(m, open(mf, "w"), indent=1)
