#!/usr/bin/env python3
"""R7 — położenie słońca dla Białegostoku (53.13 N, 23.16 E) algorytmem NOAA Solar Calculator
(równania arkusza NOAA GML "NOAA_Solar_Calculations_day.xls", oparte na J. Meeus, Astronomical Algorithms).
https://gml.noaa.gov/grad/solcalc/calcdetails.html  — deklarowana dokładność: ok. 1 min dla wschodu/zachodu
w szerokościach ±72°. Wszystkie wyniki = ESTIMATED (obliczone), nie pomiar.

Wzory (T = stulecia juliańskie od J2000.0, JD = dzień juliański UTC):
  L0 = 280.46646 + T(36000.76983 + 0.0003032 T)            średnia długość Słońca [°]
  M  = 357.52911 + T(35999.05029 − 0.0001537 T)            anomalia średnia [°]
  e  = 0.016708634 − T(0.000042037 + 0.0000001267 T)       mimośród orbity
  C  = sinM(1.914602 − T(0.004817 + 0.000014 T)) + sin2M(0.019993 − 0.000101 T) + sin3M·0.000289
  λ  = L0 + C − 0.00569 − 0.00478 sin(125.04 − 1934.136 T) długość pozorna
  ε  = 23 + (26 + (21.448 − T(46.815 + T(0.00059 − 0.001813 T)))/60)/60 + 0.00256 cos(125.04 − 1934.136 T)
  δ  = asin(sin ε sin λ)                                   deklinacja
  y  = tan²(ε/2);  EoT = 4·deg( y sin2L0 − 2e sinM + 4e y sinM cos2L0 − 0.5y² sin4L0 − 1.25e² sin2M ) [min]
  czas słoneczny prawdziwy [min] = (minuty UTC + EoT + 4·λ_geo) mod 1440;  kąt godzinny H = tst/4 − 180
  cos z = sin φ sin δ + cos φ cos δ cos H;  wysokość h = 90 − z
  azymut (od N przez E) = (deg(acos((sin φ cos z − sin δ)/(cos φ sin z))) + 180) mod 360 dla H>0, inaczej (540 − …) mod 360
  refrakcja NOAA: h>85: 0; h>5: 58.1/tan h − 0.07/tan³h + 0.000086/tan⁵h; h>−0.575: 1735 + h(−518.2 + h(103.4 +
  h(−12.79 + 0.711 h))); niżej: −20.772/tan h  [sekundy łuku]
Zdarzenia: wschód/zachód = wysokość geometryczna środka tarczy −0.833°; zmierzch cywilny −6°, żeglarski −12°,
astronomiczny −18° (bez refrakcji). Czas zdarzeń znajdowany bisekcją funkcji wysokości (1 s).
Czas lokalny: strefa Europe/Warsaw (zoneinfo: CET/CEST wg obowiązujących reguł), rok 2026.
"""
from __future__ import annotations

import csv
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

LAT, LON = 53.13, 23.16
TZ = ZoneInfo("Europe/Warsaw")
YEAR = 2026
OUT = Path(__file__).resolve().parent / "out"
rad, deg = math.radians, math.degrees


def julian_day(t: datetime) -> float:
    t = t.astimezone(timezone.utc)
    return 2440587.5 + t.timestamp() / 86400.0


def sun(t: datetime, lat: float = LAT, lon: float = LON):
    """-> (wysokość geometryczna °, wysokość z refrakcją °, azymut ° od N przez E, deklinacja °, EoT min)"""
    jd = julian_day(t)
    T = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + T * (36000.76983 + 0.0003032 * T)) % 360
    M = 357.52911 + T * (35999.05029 - 0.0001537 * T)
    e = 0.016708634 - T * (0.000042037 + 0.0000001267 * T)
    C = (math.sin(rad(M)) * (1.914602 - T * (0.004817 + 0.000014 * T))
         + math.sin(rad(2 * M)) * (0.019993 - 0.000101 * T) + math.sin(rad(3 * M)) * 0.000289)
    om = 125.04 - 1934.136 * T
    lam = L0 + C - 0.00569 - 0.00478 * math.sin(rad(om))
    eps0 = 23 + (26 + (21.448 - T * (46.815 + T * (0.00059 - T * 0.001813))) / 60) / 60
    eps = eps0 + 0.00256 * math.cos(rad(om))
    decl = deg(math.asin(math.sin(rad(eps)) * math.sin(rad(lam))))
    y = math.tan(rad(eps / 2)) ** 2
    eot = 4 * deg(y * math.sin(2 * rad(L0)) - 2 * e * math.sin(rad(M)) + 4 * e * y * math.sin(rad(M)) * math.cos(2 * rad(L0))
                  - 0.5 * y * y * math.sin(4 * rad(L0)) - 1.25 * e * e * math.sin(2 * rad(M)))
    u = t.astimezone(timezone.utc)
    minutes = u.hour * 60 + u.minute + u.second / 60
    tst = (minutes + eot + 4 * lon) % 1440
    H = tst / 4 - 180
    cz = math.sin(rad(lat)) * math.sin(rad(decl)) + math.cos(rad(lat)) * math.cos(rad(decl)) * math.cos(rad(H))
    cz = max(-1.0, min(1.0, cz))
    z = deg(math.acos(cz))
    h = 90 - z
    ca = (math.sin(rad(lat)) * cz - math.sin(rad(decl))) / (math.cos(rad(lat)) * math.sin(rad(z)))
    ca = max(-1.0, min(1.0, ca))
    az = (deg(math.acos(ca)) + 180) % 360 if H > 0 else (540 - deg(math.acos(ca))) % 360
    if h > 85:
        r = 0.0
    elif h > 5:
        tn = math.tan(rad(h))
        r = 58.1 / tn - 0.07 / tn ** 3 + 0.000086 / tn ** 5
    elif h > -0.575:
        r = 1735 + h * (-518.2 + h * (103.4 + h * (-12.79 + h * 0.711)))
    else:
        r = -20.772 / math.tan(rad(h))
    return h, h + r / 3600, az, decl, eot


def crossing(t0: datetime, t1: datetime, target: float):
    f0 = sun(t0)[0] - target
    f1 = sun(t1)[0] - target
    if f0 * f1 > 0:
        return None
    while (t1 - t0).total_seconds() > 1:
        tm = t0 + (t1 - t0) / 2
        fm = sun(tm)[0] - target
        if f0 * fm <= 0:
            t1 = tm
        else:
            t0, f0 = tm, fm
    return t0


def hm(t):
    if t is None:
        return "brak (noc biała)"
    t = (t + timedelta(seconds=30)).astimezone(TZ)
    return t.strftime("%H:%M")


def main():
    OUT.mkdir(exist_ok=True)
    rows = []
    for m in range(1, 13):
        d0 = datetime(YEAR, m, 21, 0, 0, tzinfo=TZ)
        # południe słoneczne = maksimum wysokości (przeszukanie co 10 s wokół 12:00 UTC−λ)
        best = max((d0 + timedelta(seconds=s) for s in range(9 * 3600, 15 * 3600, 10)), key=lambda t: sun(t)[0])
        row = {"data": d0.strftime("%Y-%m-%d"), "strefa": d0.tzname(), "deklinacja_deg": round(sun(best)[3], 2),
               "poludnie_sloneczne": hm(best), "wys_poludnie_deg": round(sun(best)[1], 1)}
        for hh in (8, 12, 16, 20):
            t = d0.replace(hour=hh)
            hgeo, happ, az, _, _ = sun(t)
            row[f"wys_{hh:02d}_deg"] = round(happ if hgeo > -0.833 else hgeo, 1)
            row[f"az_{hh:02d}_deg"] = round(az, 1)
        midnight_before = best - timedelta(hours=12)
        midnight_after = best + timedelta(hours=12)
        for name, target in (("wschod", -0.833), ("swit_cywilny", -6.0), ("swit_zeglarski", -12.0), ("swit_astronomiczny", -18.0)):
            row[name] = hm(crossing(midnight_before, best, target))
        for name, target in (("zachod", -0.833), ("koniec_zm_cywilnego", -6.0), ("koniec_zm_zeglarskiego", -12.0),
                             ("koniec_zm_astronomicznego", -18.0)):
            row[name] = hm(crossing(best, midnight_after, target))
        sr, ss = crossing(midnight_before, best, -0.833), crossing(best, midnight_after, -0.833)
        row["dlugosc_dnia_h"] = round((ss - sr).total_seconds() / 3600, 2)
        row["az_wschodu_deg"] = round(sun(sr)[2], 1)
        row["az_zachodu_deg"] = round(sun(ss)[2], 1)
        ce = crossing(best, midnight_after, -6.0)
        row["az_konca_zm_cywilnego_deg"] = round(sun(ce)[2], 1) if ce else ""
        row["zm_cywilny_wieczorny_min"] = round((ce - ss).total_seconds() / 60) if ce else ""
        # czas ze słońcem nisko (0–10° wysokości pozornej) — pora "ciepłego" światła
        low = sum(1 for s in range(0, 86400, 60) if 0 < sun(d0 + timedelta(seconds=s))[1] <= 10)
        row["minuty_slonce_0_10deg"] = low
        row["min_wys_noc_deg"] = round(min(sun(d0 + timedelta(seconds=s))[0] for s in range(0, 86400, 300)), 1)
        rows.append(row)
    with open(OUT / "sun_table.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
