"""Geodezja pomocnicza (stdlib): PUWG 1992 (EPSG:2180) <-> WGS84/ETRF2000, lokalne ENU, odleglosci."""
import math
A = 6378137.0
F = 1 / 298.257222101
E2 = F * (2 - F)
K0 = 0.9993
LON0 = math.radians(19.0)
FE = 500000.0
FN = -5300000.0

def _m(phi):
    e2 = E2
    return A * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * phi
                - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * math.sin(2 * phi)
                + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * math.sin(4 * phi)
                - (35 * e2 ** 3 / 3072) * math.sin(6 * phi))

def to2180(lat, lon):
    """-> (x_east, y_north) EPSG:2180 (kolejnosc jak w region.yaml: x = wschod, y = polnoc)."""
    phi = math.radians(lat); lam = math.radians(lon)
    ep2 = E2 / (1 - E2)
    n = A / math.sqrt(1 - E2 * math.sin(phi) ** 2)
    t = math.tan(phi) ** 2; c = ep2 * math.cos(phi) ** 2
    a_ = (lam - LON0) * math.cos(phi)
    m = _m(phi)
    x = K0 * n * (a_ + (1 - t + c) * a_ ** 3 / 6 + (5 - 18 * t + t * t + 72 * c - 58 * ep2) * a_ ** 5 / 120)
    y = K0 * (m + n * math.tan(phi) * (a_ * a_ / 2 + (5 - t + 9 * c + 4 * c * c) * a_ ** 4 / 24
                                        + (61 - 58 * t + t * t + 600 * c - 330 * ep2) * a_ ** 6 / 720))
    return x + FE, y + FN

def from2180(x, y):
    """(x_east, y_north) -> (lat, lon)"""
    x = (x - FE) / K0; m = (y - FN) / K0
    ep2 = E2 / (1 - E2)
    mu = m / (A * (1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))
    p1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * math.sin(2 * mu)
          + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * math.sin(4 * mu)
          + (151 * e1 ** 3 / 96) * math.sin(6 * mu) + (1097 * e1 ** 4 / 512) * math.sin(8 * mu))
    n1 = A / math.sqrt(1 - E2 * math.sin(p1) ** 2)
    t1 = math.tan(p1) ** 2; c1 = ep2 * math.cos(p1) ** 2
    r1 = A * (1 - E2) / (1 - E2 * math.sin(p1) ** 2) ** 1.5
    d = x / n1
    lat = p1 - (n1 * math.tan(p1) / r1) * (d * d / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 * c1 - 9 * ep2) * d ** 4 / 24
                                           + (61 + 90 * t1 + 298 * c1 + 45 * t1 * t1 - 252 * ep2 - 3 * c1 * c1) * d ** 6 / 720)
    lon = LON0 + (d - (1 + 2 * t1 + c1) * d ** 3 / 6
                  + (5 - 2 * c1 + 28 * t1 - 3 * c1 * c1 + 8 * ep2 + 24 * t1 * t1) * d ** 5 / 120) / math.cos(p1)
    return math.degrees(lat), math.degrees(lon)

def haversine(lat1, lon1, lat2, lon2):
    r = 6371008.8
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1; dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))

def enu(lat, lon, lat0, lon0):
    """lokalne ENU (X = wschod, Z = polnoc) [m] wzgledem (lat0, lon0); przyblizenie plaskie (elipsoida GRS80)."""
    p0 = math.radians(lat0)
    n = A / math.sqrt(1 - E2 * math.sin(p0) ** 2)
    m = A * (1 - E2) / (1 - E2 * math.sin(p0) ** 2) ** 1.5
    return math.radians(lon - lon0) * n * math.cos(p0), math.radians(lat - lat0) * m

def bearing(lat1, lon1, lat2, lon2):
    x, z = enu(lat2, lon2, lat1, lon1)
    return math.degrees(math.atan2(x, z)) % 360
