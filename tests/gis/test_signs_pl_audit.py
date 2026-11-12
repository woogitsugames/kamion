"""Audit M9: dane znaków pionowych w repo wobec tabeli wymagań z polskich przepisów
(raport: docs/reports/AUDIT-SIGNS-PL-2026-11-12-mistral.md). Test działa tylko na danych
źródłowych (bez Data/raw); test assetów generated pomija się przez pytest.skip przy wskaźniku LFS.

Każde wymaganie ma cytat (paragraf/załącznik, strona Dz.U.). Wartość z repo albo zgadza się
z przepisem, albo musi być jawnie wymieniona w KNOWN_DEVIATIONS z uzasadnieniem — wtedy test
ten dokumentuje rozbieżność zamiast jej ukrywać. Wątpliwe pozycje są oznaczone UNVERIFIED.

Źródła:
  [ZNAKI]    rozporządzenie w sprawie znaków i sygnałów drogowych, t.j. Dz.U. 2019 poz. 2310
  [ZNAKI-Z1] Załącznik nr 1 do rozporządzenia MI z 2003-07-03 (szczegółowe warunki techniczne dla
             znaków drogowych pionowych), t.j. Dz.U. 2019 poz. 2311, zm. Dz.U. 2021 poz. 2066
             (Tabela 1.11). Numery stron = strony wydrukowane Dz.U. (strona PDF ELI − 5).
"""
from __future__ import annotations

import math

import pytest

from roads import standards as S
from streetscape import gate3_landmarks as G3
from streetscape import signs as SG

pytestmark = pytest.mark.unit

# --- Tabela wymagań [ZNAKI-Z1], grupa wielkości "średnie" (S) ---------------------------
# pkt 1.2.1 (str. 2-3): średnie m.in. na jednojezdniowych drogach krajowych/wojewódzkich i drogach
# dwujezdniowych w obszarze zabudowanym z V <= 60 km/h; A-7/B-20 nie mniejsze niż średnie (pkt 1.2.1).
SIZE_MEDIUM_M = {
    "triangle": 0.900,  # Tabela 1.1 (str. 4): A, długość boku, średnie 900 mm
    "disc": 0.800,      # Tabele 3.1 (str. 92) i 4.1 (str. 152): B i C, średnica, średnie 800 mm
    "square": 0.600,    # Tabela 5.1 (str. 173): D, długość podstawy, średnie 600 mm
    "diamond": 0.600,   # Tabela 5.1 (str. 173) + pkt 5.2.1.1 (str. 180): D-1 bok 600 mm (powtórzenia 400 mm)
}
# B-20 (ośmiokąt): pkt 3.1.1 (str. 91) + Tabela 3.1 (str. 92) — wymiar 800 mm (średnie) to średnica
# koła WPISANEGO w ośmiokąt, czyli płyta 800/cos(pi/8) mm między narożnikami.
OCTAGON_INSCRIBED_M = 0.800
# Tabela 1.11 (str. 32, brzmienie po Dz.U. 2021 poz. 2066), obszar zabudowany:
HEIGHTS_M = {"min": 2.00, "sidewalk": 2.20, "overhead": 5.00}
# pkt 1.5.3 (str. 25-27): na ulicach krawędź tarczy 0,50-2,00 m od krawędzi jezdni (wystający
# krawężnik wlicza się do chodnika); na drogach z poboczem >= 0,50 m od krawędzi korony/jezdni.
LATERAL_RANGE_M = (0.50, 2.00)
# Tabela 1.3 (str. 6): pola tolerancji barw (współrzędne chromatyczności x, y, CIE 1931, D65)
# dla folii odblaskowych typu 1 i 2.
COLOUR_FIELDS = {
    "RED": ("czerwona", [(0.735, 0.265), (0.674, 0.236), (0.569, 0.341), (0.655, 0.345)]),
    "YELLOW": ("żółta", [(0.545, 0.454), (0.487, 0.423), (0.427, 0.483), (0.465, 0.534)]),
    "BLUE": ("niebieska", [(0.078, 0.171), (0.150, 0.220), (0.210, 0.160), (0.137, 0.038)]),
    "GREEN": ("zielona", [(0.007, 0.703), (0.248, 0.409), (0.177, 0.362), (0.026, 0.399)]),
    "WHITE": ("biała", [(0.355, 0.355), (0.305, 0.305), (0.285, 0.325), (0.335, 0.375)]),
    "GREY_BACK": ("szara", [(0.350, 0.360), (0.300, 0.310), (0.285, 0.325), (0.335, 0.375)]),
}
# pkt 1.4.1-1.4.3 (str. 9-10, 16-19): litery wg wzorów "do kopiowania" (krój "Drogowskaz");
# tablice E grupa średnie: wysokość liter dużych d = 210 mm, cyfr numeru drogi d1 = 162 mm
# (Tabela 9.5.1, str. 445; grupy liter Tabela 1.8, str. 11). Repo: schematyczny DejaVu Sans Bold.

# Udokumentowane rozbieżności repo vs przepis (bez poprawiania generatorów w tym PR):
# klucz = nazwa sprawdzenia, wartość = uzasadnienie z cytatem.
KNOWN_DEVIATIONS = {
    "SIGN_SIZE.square": "repo 0,80 m vs Tabela 5.1 (str. 173) D średnie 600 mm — rozbieżność, do poprawy",
    "SIGN_SIZE.diamond": "repo 0,80 m vs Tabela 5.1 (str. 173) + pkt 5.2.1.1 (str. 180) D-1 bok 600 mm — do poprawy",
    "SIGN_SIZE.octagon": "repo 0,80 m między narożnikami (koło wpisane 0,739 m) vs pkt 3.1.1 (str. 91) 800 mm koła wpisanego — do poprawy",
    "GREEN": "xy (0,257; 0,445) poza polem 'zielona' Tabeli 1.3 (str. 6); in-gamut część pola to klin przy narożniku — UNVERIFIED jako wartość nominalna",
    "font": "DejaVu Sans Bold zamiast wzorów liter pkt 1.4.3 [ZNAKI-Z1] — schematyczny stand-in, UNVERIFIED",
}


def _srgb_to_xy(rgb):
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb)
    X = 0.4124 * r + 0.3576 * g + 0.1805 * b
    Y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    Z = 0.0193 * r + 0.1192 * g + 0.9505 * b
    s = X + Y + Z
    return (X / s, Y / s)


def _inside(pt, poly):
    x, y = pt
    n = len(poly)
    j = n - 1
    odd = False
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            odd = not odd
        j = i
    return odd


def _dist_to_poly(pt, poly):
    x, y = pt
    best = 1e9
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        dx, dy = x2 - x1, y2 - y1
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        best = min(best, math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)))
    return best


def test_mounting_heights_match_table_1_11():
    assert S.SIGN_H_MIN == HEIGHTS_M["min"]
    assert S.SIGN_H_SIDEWALK == HEIGHTS_M["sidewalk"]
    assert S.SIGN_H_OVERHEAD == HEIGHTS_M["overhead"]


@pytest.mark.parametrize("shape", sorted(SIZE_MEDIUM_M))
def test_sign_size_vs_medium_group(shape):
    expected = SIZE_MEDIUM_M[shape]
    actual = S.SIGN_SIZE[shape]
    if math.isclose(actual, expected, abs_tol=1e-9):
        return
    assert f"SIGN_SIZE.{shape}" in KNOWN_DEVIATIONS, \
        f"SIGN_SIZE[{shape!r}] = {actual} != przepis {expected} (i nie ma w KNOWN_DEVIATIONS)"


def test_b20_octagon_inscribed_circle():
    inscribed = S.SIGN_SIZE["octagon"] * math.cos(math.pi / 8)
    if math.isclose(inscribed, OCTAGON_INSCRIBED_M, abs_tol=1e-9):
        return
    assert "SIGN_SIZE.octagon" in KNOWN_DEVIATIONS, \
        f"B-20 koło wpisane {inscribed:.3f} m != 0,800 m (pkt 3.1.1, Tabela 3.1, str. 91-92)"


def test_lateral_distance_within_pkt_1_5_3_range():
    lo, hi = LATERAL_RANGE_M
    assert lo <= S.SIGN_LATERAL <= hi


@pytest.mark.parametrize("name", sorted(COLOUR_FIELDS))
def test_palette_colour_vs_table_1_3(name):
    field_name, poly = COLOUR_FIELDS[name]
    xy = _srgb_to_xy(getattr(SG, name))
    if _inside(xy, poly):
        return
    if name in KNOWN_DEVIATIONS:
        assert _dist_to_poly(xy, poly) < 0.05, (name, xy)
        return
    raise AssertionError(f"{name} xy={xy} poza polem '{field_name}' Tabeli 1.3 (str. 6)")


def test_face_codes_map_to_regulated_shapes():
    expected = {"A-7": "triangle", "B-20": "octagon", "C-12": "disc", "C-9": "disc",
                "D-1": "diamond", "D-6": "square", "D-15": "square",
                "B-1": "disc", "B-2": "disc", "B-36": "disc"}
    for code, shape in expected.items():
        assert SG.FACES[code][0] == shape, code
    assert SG.face("B-33_40")[0] == "disc"


def test_gate3_face_dims():
    # A-30 = bok trójkąta grupy średniej (Tabela 1.1, str. 4)
    assert G3.FACE_DIM["A-30"][1] == S.SIGN_SIZE["triangle"]
    # D-3/D-6 0,60 m — zgodne z Tabelą 5.1 (str. 173); D-1 idzie przez SIGN_SIZE["diamond"] (rozbieżność jw.)
    assert G3.FACE_DIM["D-3"][1:] == (0.60, 0.60)
    assert G3.FACE_DIM["D-6"][1:] == (0.60, 0.60)
    # U-4a 0,75 x 1,35 m: załącznik nr 4 (poza zał. 1) — UNVERIFIED
    assert G3.FACE_DIM["U-4a"][1:] == (0.75, 1.35)


def test_direction_boards_return_physical_size():
    im, w_m, h_m = SG.direction_board(["Białystok"], ["8"], green=True)
    assert w_m > 0.5 and h_m > 0.1
    im, w_m, h_m = SG.overhead_board([(["E67"], "Białystok"), (["19"], "Wasilków")])
    assert w_m > 1.0 and h_m > 0.5

