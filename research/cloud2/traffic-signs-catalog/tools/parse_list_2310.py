"""Wyciąga spis znaków A/B/C/D/F/T z załącznika Dz.U. 2019 poz. 2310 (tekst z pdftotext -layout, strony 29-40).
Użycie: python -I parse_list_2310.py <2310_p.txt> <out.json>"""
import json, re, sys
src, out = sys.argv[1], sys.argv[2]
txt = open(src, encoding="utf-8").read()
pages = re.split(r"\n=== PDF p\.(\d+) ===\n", txt)
items = []  # (code, name, page)
buf = None
for i in range(1, len(pages), 2):
    p = int(pages[i]); body = pages[i + 1]
    if p < 29 or p > 40:
        continue
    for raw in body.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        m = re.match(r"^(\d+[a-z]?)\) ([A-Z]-\d+[a-z]?(?:/\d+)*) (.*)$", line)
        if m:
            if buf: items.append(buf)
            buf = {"lp": m.group(1), "code": m.group(2), "name": m.group(3), "page_2310": p}
            continue
        if buf and line and not line.startswith("Dziennik") and not re.match(r"^\d+\)$", line) \
                and not line.startswith("Znaki") and not line.startswith("Tabliczki") and not line.isupper() \
                and not re.match(r"^\d+\)? ", line) and "rozporządzenia" not in line and "Ze zmian" not in line:
            if not buf["name"].rstrip().endswith((";", ".")):
                buf["name"] += " " + line
    # page boundary keeps buf
if buf: items.append(buf)
res = []
for it in items:
    if it["code"][0] in "ABCDFT":
        name = it["name"].strip().rstrip(";.").strip()
        name = name.strip("„”\"")
        name = re.sub(r"- ", "", name) if False else name
        res.append({**it, "name": name})
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
from collections import Counter
print(Counter(r["code"][0] for r in res))
