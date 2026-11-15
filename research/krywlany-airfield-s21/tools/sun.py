"""Solar position (NOAA simplified). sun.py YYYY-MM-DD lat lon -> table of UTC time, azimuth, elevation; or find elevation for given azimuth."""
import sys, math, datetime as dt


def sunpos(t, lat, lon):
    jd = t.timestamp() / 86400 + 2440587.5
    n = jd - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439 - 0.0000004 * n)
    ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
    dec = math.asin(math.sin(eps) * math.sin(lam))
    gmst = (18.697374558 + 24.06570982441908 * n) % 24
    lst = math.radians((gmst * 15 + lon) % 360)
    H = lst - ra
    la = math.radians(lat)
    el = math.asin(math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(H))
    az = math.atan2(-math.sin(H), math.tan(dec) * math.cos(la) - math.sin(la) * math.cos(H))
    return (math.degrees(az) % 360, math.degrees(el))


if __name__ == '__main__':
    d = dt.datetime.fromisoformat(sys.argv[1]).replace(tzinfo=dt.timezone.utc)
    lat, lon = float(sys.argv[2]), float(sys.argv[3])
    target = float(sys.argv[4]) if len(sys.argv) > 4 else None
    best = None
    for m in range(4 * 60, 18 * 60, 5):
        t = d + dt.timedelta(minutes=m)
        az, el = sunpos(t, lat, lon)
        if target is None and m % 30 == 0:
            print(t.strftime('%H:%M UTC'), round(az, 1), round(el, 1))
        if target is not None and (best is None or abs(az - target) < best[0]):
            best = (abs(az - target), t, az, el)
    if best:
        print('sun az', target, '->', best[1].strftime('%H:%M UTC'), 'az', round(best[2], 1), 'el', round(best[3], 1))
