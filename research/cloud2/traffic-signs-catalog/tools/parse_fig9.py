"""Mapuje kody znaków na rysunki konstrukcyjne rozdz. 9 zał. 1 Dz.U. 2019 poz. 2311 (strona PDF).
Użycie: python -I parse_fig9.py <2311_p.txt> <out.json>"""
import json, re, sys
txt = open(sys.argv[1], encoding="utf-8").read()
parts = re.split(r"\n=== PDF p\.(\d+) ===\n", txt)
fig = {}
CODE = r"[ABCDFT]-\d+[a-z]?"
for i in range(1, len(parts), 2):
    p = int(parts[i])
    if not (353 <= p <= 507):
        continue
    for raw in parts[i + 1].splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        m = re.match(r"^Rys\. (9\.[1-7]\.\d+[a-z]?)\.?(?:\d+\))? ?(.*)$", line)
        if not m:
            continue
        no, cap = m.group(1), m.group(2)
        cap = cap.replace("D-21 a", "D-21a")
        codes = re.findall(CODE, cap)
        # zakresy "T-25a – T-25c" / "B-35 – B-38"
        for a, b in re.findall(r"(" + CODE + r") ?[–-] ?(" + CODE + r")", cap):
            pa, pb = re.match(r"([A-Z])-(\d+)([a-z]?)", a).groups(), re.match(r"([A-Z])-(\d+)([a-z]?)", b).groups()
            if pa[1] == pb[1] and pa[2] and pb[2]:
                codes += [f"{pa[0]}-{pa[1]}{chr(c)}" for c in range(ord(pa[2]), ord(pb[2]) + 1)]
            elif not pa[2] and not pb[2]:
                codes += [f"{pa[0]}-{n}" for n in range(int(pa[1]), int(pb[1]) + 1)]
        for c in dict.fromkeys(codes):
            fig.setdefault(c, []).append({"rys": no, "page": p, "caption": cap})
json.dump(fig, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(fig))
