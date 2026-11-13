import math
# EPSG:2180 = ETRS89 / Poland CS92 (Transverse Mercator, GRS80)
# k0=0.9993, lon0=19E, FE=500000, FN=-5300000
a = 6378137.0
f = 1 / 298.257222101
b = a * (1 - f)
e2 = (a*a - b*b) / (a*a)
k0 = 0.9993
lon0 = math.radians(19.0)
FE = 500000.0
FN = -5300000.0

def tm_forward(lat_deg, lon_deg):
    lat = math.radians(lat_deg); lon = math.radians(lon_deg)
    e = math.sqrt(e2); ep = math.sqrt(e2 / (1 - e2))
    N = a / math.sqrt(1 - e2 * math.sin(lat)**2)
    T = math.tan(lat)**2
    C = ep**2 * math.cos(lat)**2
    A_ = (lon - lon0) * math.cos(lat)
    M = a * ((1 - e2/4 - 3*e2**2/64 - 5*e2**3/256) * lat
             - (3*e2/8 + 3*e2**2/32 + 45*e2**3/1024) * math.sin(2*lat)
             + (15*e2**2/256 + 45*e2**3/1024) * math.sin(4*lat)
             - (35*e2**3/3072) * math.sin(6*lat))
    x = FE + k0 * N * (A_ + (1-T+C) * A_**3/6 + (5-18*T+T*T+72*C-58*ep**2) * A_**5/120)
    y = FN + k0 * (M + N * math.tan(lat) * (A_**2/2 + (5-T+9*C+4*C*C) * A_**4/24
        + (61-58*T+T*T+600*C-330*ep**2) * A_**6/720))
    return x, y

def tm_inverse(x, y):
    e = math.sqrt(e2); ep = math.sqrt(e2/(1-e2))
    x = x - FE; y = y - FN
    M = y / k0
    mu = M / (a * (1 - e2/4 - 3*e2**2/64 - 5*e2**3/256))
    e1 = (1 - math.sqrt(1-e2)) / (1 + math.sqrt(1-e2))
    phi1 = mu + (3*e1/2 - 27*e1**3/32) * math.sin(2*mu)
    phi1 += (21*e1**2/16 - 55*e1**4/32) * math.sin(4*mu)
    phi1 += (151*e1**3/96) * math.sin(6*mu)
    phi1 += (1097*e1**4/512) * math.sin(8*mu)
    C1 = ep**2 * math.cos(phi1)**2
    T1 = math.tan(phi1)**2
    N1 = a / math.sqrt(1 - e2*math.sin(phi1)**2)
    R1 = a * (1-e2) / (1 - e2*math.sin(phi1)**2)**1.5
    D = x / (N1 * k0)
    lat = phi1 - (N1*math.tan(phi1)/R1) * (D**2/2 - (5+3*T1+10*C1-4*C1*C1-9*ep**2)*D**4/24
          + (61+90*T1+298*C1+45*T1*T1-252*ep**2-3*C1*C1)*D**6/720)
    lon = lon0 + (D - (1+2*T1+C1)*D**3/6 + (5-2*C1+28*T1-3*C1*C1+8*ep**2+24*T1*T1)*D**5/120) / math.cos(phi1)
    return math.degrees(lat), math.degrees(lon)

if __name__ == "__main__":
    # kalibracja: srodek bialystok-industrial-c 53.158550,23.159877 -> ~ (777995, 596223)
    print(tm_forward(53.158550, 23.159877))
    # rogi istniejacego kafla [776971,595199,779019,597247]
    print(tm_inverse(776971, 595199), tm_inverse(779019, 597247))
