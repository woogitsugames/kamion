#!/usr/bin/env python3
"""R7 — zachmurzenie i widzialność w porze zachodu słońca i końca zmierzchu cywilnego (stacja BIAŁYSTOK, 2014–2023).
Dla każdej doby: godzina zachodu (wys. −0,833°) i końca zmierzchu cywilnego (−6°) z tools_sun (NOAA) -> najbliższy
pełny termin UTC -> obserwacja (N oktanty, widzialność). Wynik: out/imgw_sunset_cloud.csv (udziały per miesiąc).
Dane Instytutu Meteorologii i Gospodarki Wodnej – Państwowego Instytutu Badawczego zostały przetworzone.
Użycie: python3 -I tools_twilight.py"""
import csv
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tools_imgw as ti  # noqa: E402
import tools_sun as ts  # noqa: E402


def nearest_hour(t):
    t = t.astimezone(timezone.utc) + timedelta(minutes=30)
    return t.replace(minute=0, second=0, microsecond=0)


def main():
    acc = defaultdict(lambda: defaultdict(list))
    for y in ti.HOURLY_YEARS:
        d = datetime(y, 1, 1, 10, 0, tzinfo=timezone.utc)  # ok. południa słonecznego (λ=23°E → 10:27 UTC ± EoT)
        while d.year == y:
            for name, target in (("zachod", -0.833), ("koniec_zm_cyw", -6.0)):
                t = ts.crossing(d, d + timedelta(hours=13), target)
                if t is None:
                    continue
                h = nearest_hour(t)
                o = ti.obs_at(h.year, h.month, h.day, h.hour) if h.year in ti.HOURLY_YEARS else None
                if not o:
                    continue
                n = ti.fnum(o["N_okt"])
                v = ti.fnum(o["wid_m"])
                if n is not None and n <= 8:
                    acc[(name, d.month)]["n"].append(n)
                if v is not None:
                    acc[(name, d.month)]["v"].append(v)
            d += timedelta(days=1)
    with open(HERE / "out" / "imgw_sunset_cloud.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["pora", "miesiac", "n_dni", "udzial_N<=2_pct", "udzial_N3-6_pct", "udzial_N>=7_pct", "udzial_N=8_pct",
                    "wid_mediana_m", "udzial_wid_lt4km_pct"])
        for name in ("zachod", "koniec_zm_cyw"):
            allm_n, allm_v = [], []
            for m in list(range(1, 13)) + ["rok"]:
                if m == "rok":
                    ns, vs = allm_n, allm_v
                else:
                    ns, vs = acc[(name, m)]["n"], acc[(name, m)]["v"]
                    allm_n += ns
                    allm_v += vs
                sv = sorted(vs)
                w.writerow([name, m, len(ns),
                            round(100 * sum(1 for x in ns if x <= 2) / len(ns), 1),
                            round(100 * sum(1 for x in ns if 3 <= x <= 6) / len(ns), 1),
                            round(100 * sum(1 for x in ns if x >= 7) / len(ns), 1),
                            round(100 * sum(1 for x in ns if x == 8) / len(ns), 1),
                            round(ti.pctl(sv, .5)), round(100 * sum(1 for x in sv if x < 4000) / len(sv), 1)])
    print(open(HERE / "out" / "imgw_sunset_cloud.csv").read())


if __name__ == "__main__":
    main()
