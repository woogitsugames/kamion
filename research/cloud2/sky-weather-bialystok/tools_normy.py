#!/usr/bin/env python3
"""R7 — normy klimatyczne IMGW-PIB 1991–2020 (portal klimat.imgw.pl) dla stacji BIAŁYSTOK (12295):
pobiera strony HTML wybranych wskaźników do files/normy/ i wypisuje wiersz stacji -> out/imgw_normy_1991_2020.csv.
Źródłem pochodzenia danych jest Instytut Meteorologii i Gospodarki Wodnej – Państwowy Instytut Badawczy.
Użycie: python3 -I tools_normy.py"""
import csv
import hashlib
import html
import re
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = HERE / "files" / "normy"
CODES = ["TSR_AVE", "OPAD_SUMA", "SNIEG_0", "USL", "ZACHM", "D_POCHMURNE", "D_POGODNE"]
URL = "https://klimat.imgw.pl/pl/climate-normals/{}"


def main():
    FILES.mkdir(parents=True, exist_ok=True)
    rows, shas = [], []
    for c in CODES:
        p = FILES / f"normy_{c}.html"
        if not p.exists():
            req = urllib.request.Request(URL.format(c), headers={"User-Agent": "Mozilla/5.0 research-fetch/1.0"})
            p.write_bytes(urllib.request.urlopen(req, timeout=90).read())
            time.sleep(1)
        s = p.read_text(encoding="utf-8", errors="replace")
        shas.append((p.name, hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size))
        title = re.search(r'<option[^>]*value="%s"[^>]*>(.*?)</option>' % c, s, flags=re.S)
        t = re.sub(r"<script.*?</script>|<style.*?</style>", "", s, flags=re.S)
        x = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
        m = re.search(r"BIAŁYSTOK 12295 ((?:-?[\d,]+ ){12}-?[\d,]+)", x)
        vals = m.group(1).split() if m else [""] * 13
        rows.append([c, html.unescape(re.sub(r"\s+", " ", title.group(1))).strip() if title else ""] + vals)
        print(rows[-1])
    out = HERE / "out" / "imgw_normy_1991_2020.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["kod", "wskaznik"] + [str(i) for i in range(1, 13)] + ["rok"])
        w.writerows(rows)
    for s in shas:
        print(*s)


if __name__ == "__main__":
    main()
