#!/usr/bin/env python3
"""R7 — dwa przeliczenia pomocnicze do rekomendacji (wynik: out/checks.csv):
1) udział terminów dziennych (06–15 UTC, 2014–2023) z widzialnością < 2400 m (odpowiednik mgiełki ADR 0080),
2) daty i godziny 2026 r., gdy słońce ma wysokość 42° i azymut 200° (preset LP_Clear z ADR 0010).
Użycie: python3 -I tools_checks.py"""
import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tools_imgw as ti  # noqa: E402
import tools_sun as ts  # noqa: E402

c = {"XI-II": [0, 0], "V-VIII": [0, 0], "rok": [0, 0]}
for y in ti.HOURLY_YEARS:
    for r in ti.read_zip_csv(ti.FILES / f"t_{y}_{ti.ST_SHORT}_s.zip", "s_t"):
        if not r or r[0] != ti.STATION:
            continue
        row = dict(zip(ti.S_T_HEADER, r))
        m, g = int(row["MC"]), int(row["GG"])
        if not 6 <= g <= 15:
            continue
        v = ti.fnum(row["WIDO"]) if row["WWIDO"].strip() != "8" else ti.fnum(row["WIDA"])
        if v is None:
            continue
        for k, ok in (("XI-II", m in (11, 12, 1, 2)), ("V-VIII", m in (5, 6, 7, 8)), ("rok", True)):
            if ok:
                c[k][0] += 1
                c[k][1] += v < 2400
hits = []
d = datetime(2026, 1, 1, tzinfo=ts.TZ)
while d.year == 2026:
    for mnt in range(11 * 60, 16 * 60, 2):
        t = d + timedelta(minutes=mnt)
        _, ha, az, _, _ = ts.sun(t)
        if abs(ha - 42) < 0.4 and abs(az - 200) < 0.8:
            hits.append(t.strftime("%m-%d %H:%M %Z"))
    d += timedelta(days=1)
with open(HERE / "out" / "checks.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["co", "wartosc"])
    for k, (a, b) in c.items():
        w.writerow([f"udzial_wid_lt2400m_dzien_pct_{k}", round(100 * b / a, 1)])
    w.writerow(["LP_Clear_42deg_az200_terminy_2026", "; ".join(hits)])
print(open(HERE / "out" / "checks.csv").read())
