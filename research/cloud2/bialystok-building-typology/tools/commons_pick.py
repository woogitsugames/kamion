#!/usr/bin/env python3
"""Wybor kandydatow Commons (lista prefiksow tytulow), kontrola uzycia w repo (grep znacznika czasu), pobranie miniatur 1280 px do files/commons, widok 960 px do files/_view."""
import json, re, pathlib, subprocess, hashlib, time, urllib.parse, requests, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent; REPO = ROOT.parents[2]
PICK = {"trasa_c": """20210425 094546|20210425 094553|20210425 100541|20210425 100732|20210425 101337|20221203 101344|20221203 111658|20221203 111716|20230729 105658|20241222 122132|7203 May 2021|20201102 152422|20210130 123816|20210130 123955|20220725 124141|20240401 110629|20240530 122451|20240530 122602|7193 May 2021|20230729 105151|20200711 065242|20200710 170619|20200710 181400|20231029 122554|20231029 122726|20241026 161641|20241026 161717|20221016 155847|20241026 134211|20210816 160646|20240401 110057|20240401 110713|20240401 110048|Andersa, Maczka streets in Białystok 3""",
        "dojlidy": """20230903 133850|20230903 133947|20230903 134050|20230903 134158|20230903 134232|20230903 134349|20230903 134445|20230903 134540|20230903 134854|20230910 151311|20221103 151248|20221103 151306|20221103 151859|20230903 135728|8855 November 2022|20230903 135629|20240623 130316|20240623 130359|20240623 130441|20240623 130552|20240623 130631|20240623 130803|20240623 131406|20240623 134421|20210629 092231|20240623 141702|8861 November 2022|20210215 160546|20230903 135712|8858 November 2022"""}
corpus = ""
for f in list(REPO.glob("research/**/*.csv")) + list(REPO.glob("research/**/*.md")) + list(REPO.glob("research/**/*.json")):
    if "cloud2/bialystok-building-typology" in str(f): continue
    try: corpus += urllib.parse.unquote(f.read_text(errors="ignore")).replace("_", " ")
    except Exception: pass
H = {"User-Agent": "research-script/1.0 (generic client)"}
out = []
for area, s in PICK.items():
    files = json.load(open(ROOT / "data" / f"commons_{area}.json"))["files"]
    for pref in s.split("|"):
        m = [f for f in files if f["title"].startswith(pref)]
        if not m: print("MISSING", pref); continue
        f = m[0]; tok = re.match(r"\d{8} \d{6,7}|\d{4} \w+ \d{4}", f["title"]); tok = tok.group(0) if tok else f["title"][:-4]
        used = tok in corpus
        name = f["url"].rsplit("/", 1)[1]
        thumb = f["url"].replace("/commons/", "/commons/thumb/") + "/1280px-" + name
        safe = re.sub(r"[^A-Za-z0-9]+", "_", f["title"][:-4])[:60] + ".jpg"
        dst = ROOT / "files" / "commons" / safe
        if not dst.exists():
            for i in range(5):
                r = requests.get(thumb, headers=H, timeout=90)
                if r.status_code == 200: dst.write_bytes(r.content); break
                time.sleep(3 * 2**i)
            else: print("FAIL", thumb, r.status_code); continue
            time.sleep(1.0)
        subprocess.run(["convert", str(dst), "-resize", "960x960>", str(ROOT / "files" / "_view" / ("c_" + safe))], check=True)
        out.append({"area": area, "title": f["title"], "file": "commons/" + safe, "thumb": thumb, "page": "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(f["title"].replace(" ", "_")),
                    "lat": f["lat"], "lon": f["lon"], "license": f["license"], "artist": f["artist"], "date": f["date"], "cats": f["cats"], "used_in_repo_token": used,
                    "sha256": hashlib.sha256(dst.read_bytes()).hexdigest(), "bytes": dst.stat().st_size})
        print(area, safe, "USED" if used else "new", dst.stat().st_size)
json.dump(out, open(ROOT / "data" / "commons_picked.json", "w"), ensure_ascii=False, indent=1)
