"""Położenie Słońca (NOAA Solar Calculator, równania z Meeus — wersja „General Solar Position Calculations”).

Użycie jako moduł: sun(lat, lon, dt_utc) -> (azymut_deg od N zgodnie ze wsk. zegara, elewacja_deg z refrakcją)
Uruchom bez argumentów: tabela dla 2025-04-18 (data nalotu ortofoto/LIDAR arkuszy K67) w Białymstoku.
"""
import math, datetime


def sun(lat, lon, dt):
    jd = (dt - datetime.datetime(2000, 1, 1, 12)).total_seconds() / 86400.0 + 2451545.0
    jc = (jd - 2451545.0) / 36525.0
    L0 = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360
    M = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    C = (math.sin(math.radians(M)) * (1.914602 - jc * (0.004817 + 0.000014 * jc))
         + math.sin(math.radians(2 * M)) * (0.019993 - 0.000101 * jc) + math.sin(math.radians(3 * M)) * 0.000289)
    tl = L0 + C
    om = 125.04 - 1934.136 * jc
    lam = tl - 0.00569 - 0.00478 * math.sin(math.radians(om))
    eps0 = 23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60) / 60
    eps = eps0 + 0.00256 * math.cos(math.radians(om))
    dec = math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(lam))))
    y = math.tan(math.radians(eps / 2)) ** 2
    eot = 4 * math.degrees(y * math.sin(2 * math.radians(L0)) - 2 * e * math.sin(math.radians(M))
                           + 4 * e * y * math.sin(math.radians(M)) * math.cos(2 * math.radians(L0))
                           - 0.5 * y * y * math.sin(4 * math.radians(L0)) - 1.25 * e * e * math.sin(2 * math.radians(M)))
    mins = dt.hour * 60 + dt.minute + dt.second / 60
    tst = (mins + eot + 4 * lon) % 1440
    ha = tst / 4 - 180 if tst / 4 >= 0 else tst / 4 + 180
    la, d_, h_ = math.radians(lat), math.radians(dec), math.radians(ha)
    cz = math.sin(la) * math.sin(d_) + math.cos(la) * math.cos(d_) * math.cos(h_)
    zen = math.degrees(math.acos(max(-1, min(1, cz))))
    el = 90 - zen
    # refrakcja (NOAA)
    te = math.tan(math.radians(el))
    if el > 85:
        rf = 0
    elif el > 5:
        rf = 58.1 / te - 0.07 / te ** 3 + 0.000086 / te ** 5
    else:
        rf = 1735 + el * (-518.2 + el * (103.4 + el * (-12.79 + el * 0.711)))
    el += rf / 3600
    az = math.degrees(math.acos(max(-1, min(1, ((math.sin(la) * math.cos(math.radians(zen))) - math.sin(d_))
                                            / (math.cos(la) * math.sin(math.radians(zen)))))))
    az = (az + 180) % 360 if ha > 0 else (540 - az) % 360
    return az, el


def time_for_azimuth(lat, lon, date, az_target):
    best = None
    t = datetime.datetime(date.year, date.month, date.day, 3, 0)
    while t.hour < 17:
        a, e = sun(lat, lon, t)
        if best is None or abs(a - az_target) < best[0]:
            best = (abs(a - az_target), t, a, e)
        t += datetime.timedelta(minutes=1)
    return best[1:]


if __name__ == '__main__':
    for hh in range(7, 12):
        for mm in (0, 30):
            t = datetime.datetime(2025, 4, 18, hh, mm)
            a, e = sun(53.134, 23.181, t)
            print('2025-04-18 %02d:%02d UTC  az %.1f  el %.1f' % (hh, mm, a, e))
    print('kontrola M64 (lot 2025-04-18, el 44,4°):', time_for_azimuth(53.134, 23.181, datetime.date(2025, 4, 18), 160))
