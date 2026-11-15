"""ADR 0216: sun at Bialystok (53.13 N, 23.16 E) on summer evenings; NOAA-style low-precision ephemeris (~0.1 deg)."""
import math, json, datetime as dt
LAT, LON = 53.13, 23.16
def sun(t_utc):
    n = (t_utc - dt.datetime(2000,1,1,12)).total_seconds()/86400
    L = (280.460 + 0.9856474*n) % 360; g = math.radians((357.528 + 0.9856003*n) % 360)
    lam = math.radians(L + 1.915*math.sin(g) + 0.020*math.sin(2*g)); eps = math.radians(23.439 - 4e-7*n)
    ra = math.atan2(math.cos(eps)*math.sin(lam), math.cos(lam)); dec = math.asin(math.sin(eps)*math.sin(lam))
    gmst = (18.697374558 + 24.06570982441908*n) % 24
    ha = math.radians((gmst*15 + LON) % 360) - ra
    phi = math.radians(LAT)
    el = math.asin(math.sin(phi)*math.sin(dec) + math.cos(phi)*math.cos(dec)*math.cos(ha))
    az = math.atan2(-math.sin(ha), math.tan(dec)*math.cos(phi) - math.sin(phi)*math.cos(ha))
    return math.degrees(el), math.degrees(az) % 360
def solar_clock(e, a):  # port of Game.UI.CabDisplays.SolarClock.LocalMinutes
    D = math.pi/180; phi = LAT*D
    sd = math.sin(phi)*math.sin(e*D) + math.cos(phi)*math.cos(e*D)*math.cos(a*D)
    sd = max(math.sin(-23.44*D), min(math.sin(23.44*D), sd)); dec = math.asin(sd)
    h = math.degrees(math.acos(max(-1, min(1, (math.sin(e*D) - math.sin(phi)*sd)/(math.cos(phi)*math.cos(dec))))))
    if a % 360 < 180: h = -h
    m = round((12 + h/15 - LON/15 + (2 if dec > 0 else 1))*60) % 1440
    return f"{m//60:02d}:{m%60:02d}", math.degrees(dec)
out = {}
for d in ("2026-07-01", "2026-07-15", "2026-07-31", "2026-08-15"):
    day = dt.datetime.fromisoformat(d); row = {}
    for name, target in (("sunset_-0.83", -0.833), ("civil_end_-6", -6.0)):
        t = day + dt.timedelta(hours=16)
        while sun(t)[0] > target: t += dt.timedelta(seconds=30)
        el, az = sun(t); row[name] = {"cest": (t + dt.timedelta(hours=2)).strftime("%H:%M"), "az": round(az, 1)}
    el, az = sun(day + dt.timedelta(hours=19)); row["21:00_cest"] = {"el": round(el, 1), "az": round(az, 1)}
    out[d] = row
out["solar_clock_el-6_az300"] = solar_clock(-6, 300)
out["solar_clock_el-8_az300"] = solar_clock(-8, 300)
print(json.dumps(out, indent=1))
