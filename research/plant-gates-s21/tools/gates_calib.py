"""Kalibracja kamery P11-094 (20230903_135016, miniatura 1600 px) na dwóch narożnikach ściany NNE hali A i rzut
pikseli (krawędzie bram, lampy, uskok) na linię ściany. Model otworkowy: azymut(x) = θc + atan((x − 800)/f).
Kamera (EXIF Commons → EPSG:2180): E 780819,6 N 590466,2. Narożnik E i N z OSM way 471492583 (węzły 4656499194, 4656499193).
Piksele odczytane z wycinków z linijką (x w obrazie 1600 px): narożnik E 363, koniec części A3 1440."""
import math
cam = (780819.6, 590466.2)
Ec = (780790.8, 590434.2)
Nc = (780714.2, 590468.3)


def brg(p):
    return math.degrees(math.atan2(p[0] - cam[0], p[1] - cam[1])) % 360


b1, b2 = brg(Ec), brg(Nc)
x1, x2 = 363, 1440
best = None
for f10 in range(3000, 40000):
    f = f10 / 10
    tc = b1 - math.degrees(math.atan((x1 - 800) / f))
    err = tc + math.degrees(math.atan((x2 - 800) / f)) - b2
    if best is None or abs(err) < abs(best[0]):
        best = (err, f, tc)
err, f, tc = best
print('f', f, 'HFOV', round(2 * math.degrees(math.atan(800 / f)), 1), 'heading', round(tc, 1))


def along(x):
    th = math.radians(tc + math.degrees(math.atan((x - 800) / f))); d = (math.sin(th), math.cos(th))
    ux, uy = Nc[0] - Ec[0], Nc[1] - Ec[1]; L = math.hypot(ux, uy); ux /= L; uy /= L
    det = d[0] * (-uy) - d[1] * (-ux); rx, ry = Ec[0] - cam[0], Ec[1] - cam[1]
    return (d[0] * ry - d[1] * rx) / det


for n, x in (('brama1 L', 660), ('brama1 P', 760), ('brama2 L', 1205), ('brama2 P', 1263), ('uskok A1/A3', 1325),
             ('lampa1', 567), ('lampa2', 887), ('lampa3', 1097), ('lampa4', 1263)):
    print(n, round(along(x), 1), 'm od narożnika E')
