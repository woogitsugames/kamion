"""ADR 0216b: sun position over Bialystok with the NOAA solar calculator equations (NOAA Global Monitoring
Laboratory, "General Solar Position Calculations" / NOAA_Solar_Calculations_day spreadsheet; Meeus, Astronomical
Algorithms, 1991 - accuracy about 1 minute for sunrise / sunset between latitudes +/-72 deg).

Pure Python, no data. Used to check the summer dusk of the lighting profiles (owner D65 p.7 / D68: dusk about 21:00,
sun azimuth about 300 deg):

    uv run --project tools/worldgen python tools/worldgen/qa/sun_noaa.py            # table of summer dates
    uv run --project tools/worldgen python tools/worldgen/qa/sun_noaa.py --json out.json

Civil dusk = geometric centre of the sun at -6 deg (no refraction); sunset = apparent upper limb at the horizon,
i.e. geometric centre at -0.833 deg (standard refraction 34' + semi-diameter 16'). Clock = CEST (UTC+2) from the last
Sunday of March to the last Sunday of October (EU summer time), CET (UTC+1) otherwise.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math

BIALYSTOK_LAT, BIALYSTOK_LON = 53.13, 23.16     # city centre, WGS84 (same point as game SolarClock.cs)
CIVIL_DUSK_DEG, SUNSET_DEG = -6.0, -0.833


def _julian_day(t: dt.datetime) -> float:
    """Julian day of a UTC datetime (naive = UTC)."""
    return t.toordinal() + 1721424.5 + (t.hour + (t.minute + (t.second + t.microsecond / 1e6) / 60.0) / 60.0) / 24.0


def sun_position(t_utc: dt.datetime, lat: float = BIALYSTOK_LAT, lon: float = BIALYSTOK_LON, refraction: bool = False):
    """(elevation deg, azimuth deg from north clockwise) of the sun centre at UTC time t_utc. Geometric elevation unless
    refraction=True (NOAA spreadsheet refraction model)."""
    jc = (_julian_day(t_utc) - 2451545.0) / 36525.0
    l0 = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360.0
    m = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    mr = math.radians(m)
    c = (math.sin(mr) * (1.914602 - jc * (0.004817 + 0.000014 * jc)) + math.sin(2 * mr) * (0.019993 - 0.000101 * jc)
         + math.sin(3 * mr) * 0.000289)
    true_long = l0 + c
    omega = 125.04 - 1934.136 * jc
    app_long = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))
    eps0 = 23.0 + (26.0 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60.0) / 60.0
    eps = eps0 + 0.00256 * math.cos(math.radians(omega))
    decl = math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(app_long))))
    y = math.tan(math.radians(eps / 2.0)) ** 2
    l0r = math.radians(l0)
    eot = 4.0 * math.degrees(y * math.sin(2 * l0r) - 2 * e * math.sin(mr) + 4 * e * y * math.sin(mr) * math.cos(2 * l0r)
                             - 0.5 * y * y * math.sin(4 * l0r) - 1.25 * e * e * math.sin(2 * mr))   # minutes
    minutes_utc = t_utc.hour * 60.0 + t_utc.minute + (t_utc.second + t_utc.microsecond / 1e6) / 60.0
    tst = (minutes_utc + eot + 4.0 * lon) % 1440.0
    ha = tst / 4.0 - 180.0 if tst / 4.0 >= 0 else tst / 4.0 + 180.0
    latr, dr, har = math.radians(lat), math.radians(decl), math.radians(ha)
    cosz = max(-1.0, min(1.0, math.sin(latr) * math.sin(dr) + math.cos(latr) * math.cos(dr) * math.cos(har)))
    zen = math.degrees(math.acos(cosz))
    elev = 90.0 - zen
    if refraction:
        te = math.tan(math.radians(elev))
        if elev > 85.0:
            r = 0.0
        elif elev > 5.0:
            r = 58.1 / te - 0.07 / te ** 3 + 0.000086 / te ** 5
        elif elev > -0.575:
            r = 1735.0 + elev * (-518.2 + elev * (103.4 + elev * (-12.79 + elev * 0.711)))
        else:
            r = -20.772 / te
        elev += r / 3600.0
    zr = math.radians(zen)
    den = math.cos(latr) * math.sin(zr)
    if abs(den) < 1e-12:
        az = 180.0
    else:
        ca = max(-1.0, min(1.0, (math.sin(latr) * math.cos(zr) - math.sin(dr)) / den))
        az = (math.degrees(math.acos(ca)) + 180.0) % 360.0 if ha > 0 else (540.0 - math.degrees(math.acos(ca))) % 360.0
    return elev, az


def utc_offset_h(day: dt.date) -> int:
    """EU summer time: CEST (2) from the last Sunday of March to the last Sunday of October, else CET (1)."""
    def last_sunday(y, mo):
        d = dt.date(y, mo, 31)
        return d - dt.timedelta(days=(d.weekday() + 1) % 7)
    return 2 if last_sunday(day.year, 3) <= day < last_sunday(day.year, 10) else 1


def evening_crossing(day: dt.date, elev_deg: float, lat: float = BIALYSTOK_LAT, lon: float = BIALYSTOK_LON):
    """Local clock time (datetime, naive local) and azimuth when the geometric sun centre sinks through elev_deg in
    the evening of `day` (bisection to 1 s). None when it does not (white nights)."""
    off = utc_offset_h(day)
    noon = dt.datetime(day.year, day.month, day.day, 12 - off, 0)           # 12:00 local
    f = lambda t: sun_position(t, lat, lon)[0] - elev_deg
    a, b = noon, noon + dt.timedelta(hours=12)
    if f(a) < 0 or f(b) > 0:
        return None
    while (b - a).total_seconds() > 1.0:
        mid = a + (b - a) / 2
        a, b = (mid, b) if f(mid) > 0 else (a, mid)
    return a + dt.timedelta(hours=off), sun_position(a, lat, lon)[1]


def table(year: int = 2026, days=None):
    days = days or [(6, 21), (7, 1), (7, 15), (7, 31), (8, 1), (8, 10), (8, 15), (8, 20), (8, 31)]
    rows = []
    for mo, d in days:
        day = dt.date(year, mo, d)
        dusk, ss = evening_crossing(day, CIVIL_DUSK_DEG), evening_crossing(day, SUNSET_DEG)
        rows.append({"date": day.isoformat(), "utc_offset_h": utc_offset_h(day),
                     "sunset_local": ss[0].strftime("%H:%M"), "sunset_azimuth_deg": round(ss[1], 1),
                     "civil_dusk_local": dusk[0].strftime("%H:%M"), "civil_dusk_azimuth_deg": round(dusk[1], 1)})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--json")
    a = ap.parse_args()
    rows = table(a.year)
    print(f"Bialystok {BIALYSTOK_LAT} N {BIALYSTOK_LON} E, NOAA equations, year {a.year}")
    print("date        sunset  az     civil dusk (-6)  az")
    for r in rows:
        print(f"{r['date']}  {r['sunset_local']}  {r['sunset_azimuth_deg']:5.1f}  {r['civil_dusk_local']}            "
              f"{r['civil_dusk_azimuth_deg']:5.1f}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"lat": BIALYSTOK_LAT, "lon": BIALYSTOK_LON, "method": "NOAA solar calculator equations",
                       "rows": rows}, fh, indent=1)


if __name__ == "__main__":
    main()
