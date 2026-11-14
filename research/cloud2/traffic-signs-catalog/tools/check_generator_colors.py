"""Sprawdza, czy barwy sRGB z tools/worldgen/streetscape/signs.py (stan main 81c9bae) mieszczą się w polach tolerancji
tab. 1.3 zał. 1 Dz.U. 2019 poz. 2311 (folia typu 1/2) i czy luminancja Y >= beta_min. Użycie: python -I tools/check_generator_colors.py"""
GEN = {"czerwona": (196, 30, 36), "żółta": (250, 196, 0), "niebieska": (0, 84, 160), "biała": (245, 245, 242), "zielona": (0, 112, 72), "szara": (150, 152, 152)}
T13 = {"biała": [(0.355, 0.355), (0.305, 0.305), (0.285, 0.325), (0.335, 0.375), 0.35, 0.27],
       "żółta": [(0.545, 0.454), (0.487, 0.423), (0.427, 0.483), (0.465, 0.534), 0.27, 0.16],
       "czerwona": [(0.735, 0.265), (0.674, 0.236), (0.569, 0.341), (0.655, 0.345), 0.05, 0.03],
       "zielona": [(0.007, 0.703), (0.248, 0.409), (0.177, 0.362), (0.026, 0.399), 0.04, 0.03],
       "niebieska": [(0.078, 0.171), (0.150, 0.220), (0.210, 0.160), (0.137, 0.038), 0.01, 0.01],
       "szara": [(0.350, 0.360), (0.300, 0.310), (0.285, 0.325), (0.335, 0.375), 0.12, 0.12]}
def lin(c):
    c /= 255; return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
def xyY(rgb):
    r, g, b = map(lin, rgb)
    X = 0.4124 * r + 0.3576 * g + 0.1805 * b; Y = 0.2126 * r + 0.7152 * g + 0.0722 * b; Z = 0.0193 * r + 0.1192 * g + 0.9505 * b
    s = X + Y + Z; return X / s, Y / s, Y
def inside(pt, poly):
    x, y = pt; n = len(poly); c = False
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: c = not c
    return c
print("barwa | sRGB generatora | x | y | Y | w polu tolerancji | Y >= β_min typ1 / typ2")
for k, rgb in GEN.items():
    x, y, Y = xyY(rgb); poly = T13[k][:4]
    print(f"{k} | {rgb} | {x:.3f} | {y:.3f} | {Y:.3f} | {'TAK' if inside((x, y), poly) else 'NIE'} | {Y >= T13[k][4]} / {Y >= T13[k][5]}")
