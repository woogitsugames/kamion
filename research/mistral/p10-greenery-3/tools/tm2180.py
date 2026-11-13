"""EPSG:2180 (ETRS89 / PL-CS92, Transverse Mercator lon0=19E, k0=0.9993, FE=500000, FN=-5300000, GRS80)
<-> WGS84. ETRS89 i WGS84 rożnią się < 1 dm — pomijalne przy GSD 0.25 m.
Odtwarzalna walidacja roundtrip w test_transform().
"""
import math

A = 6378137.0
F = 1 / 298.257222101  # GRS80
E2 = F * (2 - F)
EP2 = E2 / (1 - E2)
K0 = 0.9993
LON0 = math.radians(19.0)
FE = 500000.0
FN = -5300000.0


def _meridional(phi):
    e2, e4, e6 = E2, E2 * E2, E2 ** 3
    return A * ((1 - e2 / 4 - 3 * e4 / 64 - 5 * e6 / 256) * phi
                - (3 * e2 / 8 + 3 * e4 / 32 + 45 * e6 / 1024) * math.sin(2 * phi)
                + (15 * e4 / 256 + 45 * e6 / 1024) * math.sin(4 * phi)
                - (35 * e6 / 3072) * math.sin(6 * phi))


def forward(lat_deg, lon_deg):
    """WGS84 (lat, lon) -> EPSG:2180 (easting, northing)."""
    phi = math.radians(lat_deg)
    dl = math.radians(lon_deg) - LON0
    sp, cp, tp = math.sin(phi), math.cos(phi), math.tan(phi)
    N = A / math.sqrt(1 - E2 * sp * sp)
    T = tp * tp
    C = EP2 * cp * cp
    Aa = dl * cp
    M = _meridional(phi)
    east = FE + K0 * N * (Aa + (1 - T + C) * Aa ** 3 / 6
                         + (5 - 18 * T + T * T + 72 * C - 58 * EP2) * Aa ** 5 / 120)
    north = FN + K0 * (M + N * tp * (Aa * Aa / 2
                        + (5 - T + 9 * C + 4 * C * C) * Aa ** 4 / 24
                        + (61 - 58 * T + T * T + 600 * C - 330 * EP2) * Aa ** 6 / 720))
    return east, north


def _footpoint(north_k):
    phi = north_k / (A * (1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256))
    for _ in range(8):
        phi -= (_meridional(phi) - north_k) / (
            A * (1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256)
            * (1 - E2 * math.sin(phi) ** 2) ** -1.0)
    return phi


def inverse(east, north):
    """EPSG:2180 -> WGS84 (lat, lon)."""
    phi1 = _footpoint((north - FN) / K0)
    sp1, cp1, tp1 = math.sin(phi1), math.cos(phi1), math.tan(phi1)
    N1 = A / math.sqrt(1 - E2 * sp1 * sp1)
    R1 = A * (1 - E2) / (1 - E2 * sp1 * sp1) ** 1.5
    T1 = tp1 * tp1
    C1 = EP2 * cp1 * cp1
    D = (east - FE) / (N1 * K0)
    lat = phi1 - (N1 * tp1 / R1) * (
        D * D / 2 - (5 + 3 * T1 + 10 * C1 - 4 * C1 * C1 - 9 * EP2) * D ** 4 / 24
        + (61 + 90 * T1 + 298 * C1 + 45 * T1 * T1 - 252 * EP2 - 3 * C1 * C1) * D ** 6 / 720)
    lon = LON0 + (D - (1 + 2 * T1 + C1) * D ** 3 / 6
                  + (5 - 2 * C1 + 28 * T1 - 3 * C1 * C1 + 8 * EP2 + 24 * T1 * T1) * D ** 5 / 120) / cp1
    return math.degrees(lat), math.degrees(lon)


if __name__ == '__main__':
    # walidacja: roundtrip i punkt kontrolny z kafla
    lat, lon = 53.155, 23.152222
    e, n = forward(lat, lon)
    lat2, lon2 = inverse(e, n)
    print(f'forward(53.155, 23.152222) -> E={e:.2f} N={n:.2f}')
    print(f'roundtrip err: {abs(lat - lat2):.2e} deg lat, {abs(lon - lon2):.2e} deg lon')
    # kafel [776971, 595199, 779019, 597247] — narożniki
    for e2, n2 in [(776971, 595199), (779019, 597247)]:
        la, lo = inverse(e2, n2)
        print(f'inverse({e2},{n2}) -> {la:.6f}, {lo:.6f}')
