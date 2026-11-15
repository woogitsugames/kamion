#!/usr/bin/env python3
"""Pozycja Słońca i zmierzch cywilny dla Białegostoku — obliczenie astronomiczne (stdlib).

Formuły: NOAA Solar Calculator (Global Monitoring Laboratory), oparte na J. Meeus,
"Astronomical Algorithms" (rozdz. 25 i 28): średnia długość i anomalia Słońca, równanie środka,
nachylenie ekliptyki z poprawką nutacyjną, równanie czasu, kąt godzinny.
https://gml.noaa.gov/grad/solcalc/calcdetails.html (dostęp 2026-11-14).
Deklarowana przez NOAA dokładność wschodu/zachodu: ok. 1 min dla szerokości < 72 st.
Elewacja GEOMETRYCZNA (bez refrakcji) - tak definiuje się zmierzch cywilny (-6 st.).
Zachód Słońca: środek tarczy na -0,833 st. (refrakcja 34' + półśrednica 16').

Użycie:
  python3 sun.py elev 2021-12-16T15:57:23 [lat lon]      # czas lokalny Europe/Warsaw
  python3 sun.py table                                    # tabela zmierzchu, Białystok, 15. dnia miesiąca
  python3 sun.py selftest
"""
import math, sys, datetime as dt

LAT, LON = 53.1325, 23.1688   # Białystok, Rynek Kościuszki (OSM), WGS84

def _last_sunday(year, month):
    d = dt.date(year, month, 31)
    return d - dt.timedelta(days=(d.weekday() + 1) % 7)

def warsaw_utc_offset(local):
    """Przesunięcie Europe/Warsaw [h] dla naiwnego czasu lokalnego (reguła UE od 1996 r.:
    czas letni od ostatniej niedzieli marca 02:00 do ostatniej niedzieli października 03:00)."""
    start = dt.datetime.combine(_last_sunday(local.year, 3), dt.time(2, 0))
    end = dt.datetime.combine(_last_sunday(local.year, 10), dt.time(3, 0))
    return 2 if start <= local < end else 1

def julian_day(utc):
    y, m = utc.year, utc.month
    d = utc.day + (utc.hour + (utc.minute + utc.second / 60.0) / 60.0) / 24.0
    if m <= 2:
        y -= 1; m += 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5

def _sun(utc):
    t = (julian_day(utc) - 2451545.0) / 36525.0
    l0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360.0
    m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
    e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
    mr = math.radians(m)
    c = (math.sin(mr) * (1.914602 - t * (0.004817 + 0.000014 * t))
         + math.sin(2 * mr) * (0.019993 - 0.000101 * t) + math.sin(3 * mr) * 0.000289)
    omega = math.radians(125.04 - 1934.136 * t)
    lam = math.radians(l0 + c - 0.00569 - 0.00478 * math.sin(omega))
    eps0 = 23 + (26 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60.0) / 60.0
    eps = math.radians(eps0 + 0.00256 * math.cos(omega))
    decl = math.asin(math.sin(eps) * math.sin(lam))
    y = math.tan(eps / 2) ** 2
    l0r = math.radians(l0)
    eqt = 4 * math.degrees(y * math.sin(2 * l0r) - 2 * e * math.sin(mr) + 4 * e * y * math.sin(mr) * math.cos(2 * l0r)
                           - 0.5 * y * y * math.sin(4 * l0r) - 1.25 * e * e * math.sin(2 * mr))
    return decl, eqt   # deklinacja [rad], równanie czasu [min]

def elevation_azimuth(utc, lat=LAT, lon=LON):
    """Geometryczna elewacja i azymut geograficzny Słońca [st.] dla czasu UTC (naiwny datetime)."""
    decl, eqt = _sun(utc)
    minutes = utc.hour * 60 + utc.minute + utc.second / 60.0
    tst = (minutes + eqt + 4 * lon) % 1440.0
    ha = math.radians(tst / 4.0 - 180.0)
    la = math.radians(lat)
    cz = math.sin(la) * math.sin(decl) + math.cos(la) * math.cos(decl) * math.cos(ha)
    cz = max(-1.0, min(1.0, cz))
    zen = math.acos(cz)
    az = (math.degrees(math.atan2(math.sin(ha), math.cos(ha) * math.sin(la) - math.tan(decl) * math.cos(la))) + 180.0) % 360.0
    return 90.0 - math.degrees(zen), az

def elevation_local(local, lat=LAT, lon=LON):
    utc = local - dt.timedelta(hours=warsaw_utc_offset(local))
    return elevation_azimuth(utc, lat, lon)

def evening_crossing(date, target_deg, lat=LAT, lon=LON):
    """Czas UTC wieczornego przejścia elewacji przez target_deg (bisekcja między górowaniem a dołowaniem)."""
    noon = dt.datetime.combine(date, dt.time(12, 0)) - dt.timedelta(minutes=4 * lon)
    lo, hi = noon, noon + dt.timedelta(hours=12)
    if elevation_azimuth(lo, lat, lon)[0] < target_deg or elevation_azimuth(hi, lat, lon)[0] > target_deg:
        return None
    for _ in range(40):
        mid = lo + (hi - lo) / 2
        if elevation_azimuth(mid, lat, lon)[0] > target_deg: lo = mid
        else: hi = mid
    return lo

def _fmt_local(utc):
    if utc is None: return "brak"
    for off in (1, 2):
        loc = utc + dt.timedelta(hours=off)
        if warsaw_utc_offset(loc) == off:
            return (loc + dt.timedelta(seconds=30)).strftime("%H:%M")
    return "?"

def table(year=2026):
    rows = []
    for month in range(1, 13):
        d = dt.date(year, month, 15)
        ss = evening_crossing(d, -0.833); c3 = evening_crossing(d, -3.0)
        c6 = evening_crossing(d, -6.0); c8 = evening_crossing(d, -8.0)
        dur = None if (ss is None or c6 is None) else (c6 - ss).total_seconds() / 60.0
        az6 = elevation_azimuth(c6)[1] if c6 else None
        rows.append((d.isoformat(), _fmt_local(ss), _fmt_local(c3), _fmt_local(c6), _fmt_local(c8),
                     "brak" if dur is None else "%.0f" % dur, "brak" if az6 is None else "%.0f" % az6))
    return rows

def selftest():
    # 1) równonoc: deklinacja ~0, 2) przesilenia: +-23,44, 3) zmierzch cywilny trwa dłużej latem
    e, _ = elevation_azimuth(dt.datetime(2026, 6, 21, 10, 27), LAT, LON)   # górowanie ok. 10:27 UTC
    assert abs(e - (90 - LAT + 23.44)) < 0.1, e
    e, _ = elevation_azimuth(dt.datetime(2026, 12, 21, 10, 26), LAT, LON)
    assert abs(e - (90 - LAT - 23.44)) < 0.1, e
    t = {r[0]: r for r in table(2026)}
    assert int(t["2026-06-15"][5]) > int(t["2026-03-15"][5])
    # 4) czas letni/zimowy
    assert warsaw_utc_offset(dt.datetime(2026, 7, 1, 12)) == 2 and warsaw_utc_offset(dt.datetime(2026, 12, 1, 12)) == 1
    print("selftest OK")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "table":
        print("data;zachód(-0,833°);Słońce -3°;koniec zm. cywilnego(-6°);Słońce -8°;zachód→-6° [min];azymut Słońca przy -6° [°]")
        for r in table(int(a[1]) if len(a) > 1 else 2026): print(";".join(r))
    elif a[0] == "elev":
        loc = dt.datetime.fromisoformat(a[1])
        lat = float(a[2]) if len(a) > 3 else LAT; lon = float(a[3]) if len(a) > 3 else LON
        e, az = elevation_local(loc, lat, lon)
        print("%.2f %.1f" % (e, az))
    elif a[0] == "selftest":
        selftest()
