"""Numbers of the Polish sign regulation used by the direction-sign generator (znaki kierunku i miejscowości, E).

Source [ZNAKI-Z1]: Załącznik nr 1 do rozporządzenia Ministra Infrastruktury z 3 lipca 2003 r. w sprawie
szczegółowych warunków technicznych dla znaków i sygnałów drogowych oraz urządzeń bezpieczeństwa ruchu drogowego i
warunków ich umieszczania na drogach, tekst jednolity Dz.U. 2019 poz. 2311
(https://api.sejm.gov.pl/eli/acts/DU/2019/2311/text/O/D20192311-c1.pdf, sha256 f94925ec…b550543, read 2026-11-15).
Amendments after the consolidated text (ELI `references`, checked by research R1 on 2026-11-14): Dz.U. 2021 poz. 438,
2021 poz. 2066, 2022 poz. 2377, 2026 poz. 132 - none of them changes the tables copied here (438 and 132 touch
pkt 6.3.7 / 6.x wording and E-15 variants; Tabela 1.11 is quoted in its 2022 poz. 2377 wording). There is no newer
consolidated text. Page numbers = page of the PDF file (= the printed "Dziennik Ustaw - n -" page).

Every constant names its table / point. Tables 1.9, 9.5.1 - 9.5.6 are raster images in the PDF: read off the page
rendered at 110 dpi (ADR 0236); 1.10 has a text layer (pdftotext). Values that are ours are marked WORKING_VALUE.
"""

from __future__ import annotations

# --- Tabela 1.8 (s. 16): wysokość liter dużych i cyfr d [mm] wg grupy wielkości liter (transcribed by research R1
# par. 3.5; the E values reappear in Tabela 9.5.1 / 9.5.3 / 9.5.4, read here)
LETTER_D_MM = {"I": 42, "II": 72, "III": 102, "IV": 132, "V": 162, "VI": 210, "VII": 282, "VIII": 348, "IX": 420}

# --- pkt 1.4.1 (s. 15): d = 6 gr, m = 4 gr, wiersz w = 8 gr, interlinia i = 2 gr, pas pisma p = w + i = 10 gr
GR_PER_D = 6.0
ROW_GR = 8.0
INTERLINE_GR = 2.0
BAND_GR = ROW_GR + INTERLINE_GR
# pkt 1.4.2 (s. 15): odstęp między literami o = 1,5 gr, między wyrazami h = 3 o = 4,5 gr, napis - obwódka >= 2 gr
LETTER_GAP_GR = 1.5
WORD_GAP_GR = 4.5
EDGE_GAP_GR = 2.0

# --- Tabela 1.9 (s. 17): grupy wielkości liter na znakach E wg grupy wielkości znaków (None = nie stosuje się)
E_LETTER_GROUPS = {
    "E-1": {"wielkie": ("IX", "VIII", "VII"), "duze": ("VII", "VI", "V", "IV"), "srednie": ("VI", "V", "IV"), "male": None},
    "E-2": {"wielkie": ("IX", "VIII", "VII"), "duze": ("VII", "VI"), "srednie": ("VI", "V"), "male": ("IV", "III")},
    "E-4": {"wielkie": None, "duze": ("VI",), "srednie": ("V",), "male": ("V",)},
    "E-13": {"wielkie": None, "duze": ("V",), "srednie": ("V",), "male": ("IV",)},
    "E-14": {"wielkie": ("VIII", "VII"), "duze": ("VI", "V"), "srednie": ("V", "IV"), "male": None},
    "E-15": {"wielkie": None, "duze": ("VIII", "VII"), "srednie": ("VI", "V"), "male": ("V",)},
    "E-17a": {"wielkie": None, "duze": ("V",), "srednie": ("V",), "male": ("V",)},
}

# --- Tabela 1.10 a-c (s. 18): szerokości liter, cyfr i znaków specjalnych między punktami odmierzania [gr]
LETTER_W_GR = {
    "A": 4.34, "B": 3.87, "C": 4.00, "D": 4.50, "E": 3.00, "F": 2.50, "G": 4.80, "H": 4.50, "I": 1.00, "J": 2.37,
    "K": 3.75, "L": 2.75, "Ł": 2.75, "M": 5.85, "N": 4.75, "O": 5.00, "P": 3.00, "R": 3.87, "S": 3.50, "T": 2.00,
    "U": 3.50, "V": 3.00, "W": 5.50, "Y": 2.50, "Z": 3.00,
    "a": 3.75, "b": 3.75, "c": 2.87, "d": 3.75, "e": 3.40, "f": 1.50, "g": 3.75, "h": 3.50, "i": 1.00, "j": 1.00,
    "k": 2.87, "l": 1.00, "ł": 1.75, "m": 5.50, "n": 3.50, "o": 3.75, "p": 3.75, "r": 1.50, "s": 2.00, "t": 1.75,
    "u": 3.25, "v": 2.50, "w": 4.50, "y": 2.50, "z": 2.25,
    "1": 1.50, "2": 3.25, "3": 3.50, "4": 3.25, "5": 3.37, "6": 3.50, "7": 2.25, "8": 4.00, "9": 3.25, "0": 3.40,
    "-": 2.0, "(": 0.5, ")": 0.5, ",": 1.0, ".": 1.0, "!": 1.5,
}
# letters with diacritics have the width of the base letter (the table lists only Ł / ł apart; the worked example
# "Łącko" in Tabela 1.10 e uses 3,75 for "ą" = "a")
_BASE = str.maketrans("ĄĆĘŃÓŚŹŻąćęńóśźż", "ACENOSZZacenoszz")
UNKNOWN_W_GR = 3.5      # WORKING_VALUE: characters the table does not list (Q, X, q, x, ...)


def text_len_gr(text: str) -> float:
    """Length of an inscription in gr between the outer measuring points (Tabela 1.10; "Łącko" = 21,99 gr)."""
    total = 0.0
    for wi, word in enumerate(text.split()):
        if wi:
            total += WORD_GAP_GR
        for ci, ch in enumerate(word):
            if ci:
                total += LETTER_GAP_GR
            total += LETTER_W_GR.get(ch, LETTER_W_GR.get(ch.translate(_BASE), UNKNOWN_W_GR))
    return total


def text_len_m(text: str, d_m: float) -> float:
    return text_len_gr(text) * d_m / GR_PER_D


# --- Tabela 9.5.1 (s. 450): wymiary do konstrukcji znaków E [mm]: a / a1 = szerokość linii kierunku z pierwszeństwem /
# podporządkowanego na E-1 (pkt 6.3.1.2, s. 264: 15 cm i 7,5 cm; drogi ekspresowe 20 i 10 cm), d ... d4 = litery
E_CONSTRUCTION_MM = {
    "wielkie": {"a": 300, "a1": 125, "d": 420, "d1": 348, "d2": 420, "d3": 348, "d4": 282},
    "duze": {"a": 200, "a1": 100, "d": 282, "d1": 210, "d2": 210, "d3": 162, "d4": 132},
    "srednie": {"a": 150, "a1": 75, "d": 210, "d1": 162, "d2": 162, "d3": 132, "d4": None},
}
# --- Tabela 9.5.2 (s. 451): r = promień naroża, c = szerokość obwódki, e = szerokość ramki [mm]
E_FRAME_MM = {"wielkie": {"r": 100, "c": 5, "e": 30}, "duze": {"r": 100, "c": 5, "e": 30},
              "srednie": {"r": 50, "c": 5, "e": 20}}
# --- Tabela 9.5.3 (s. 452): znaki z numerami dróg umieszczane na znakach kierunku wg wysokości liter d nazwy
# miejscowości [mm]: d1 cyfry, h wysokość znaku, b margines pionowy, o obwódka, r naroże, m margines boczny,
# P odstęp litera - liczba (E-15c/d, E-16). Wartości w nawiasie w wierszu d = 210 (300 / 49 / 20) = znaki E-15
# stosowane samodzielnie (pkt 6.3.7.8, s. 290: wysokość 300 mm).
ROUTE_NO_MM = {
    132: {"d1": 102, "h": 180, "b": 30, "o": 9, "r": 30, "m": 80, "P": 51},
    162: {"d1": 132, "h": 220, "b": 35, "o": 9, "r": 30, "m": 100, "P": 66},
    210: {"d1": 162, "h": 270, "b": 45, "o": 9, "r": 30, "m": 122, "P": 81},
    282: {"d1": 210, "h": 350, "b": 55, "o": 15, "r": 30, "m": 158, "P": 105},
    348: {"d1": 282, "h": 470, "b": 74, "o": 20, "r": 30, "m": 212, "P": 141},
    420: {"d1": 348, "h": 580, "b": 91, "o": 25, "r": 30, "m": 261, "P": 174},
}
ROUTE_NO_STANDALONE_MM = {"d1": 162, "h": 300, "b": 49, "o": 20, "r": 30, "m": 122, "P": 81}
NO_GAP_MM = 80          # pkt 6.3.1.2 (s. 266): odstęp numer krajowy - międzynarodowy 8 cm (autostrady 16 cm)
NO_NAME_GAP_GR = 2.0    # pkt 6.3.1.2 (s. 266): numer drogi - nazwa miejscowości min. 2 gr
# --- Tabela 9.5.4 (s. 457) + rys. 9.5.20 (s. 458): drogowskazy tablicowe [mm]: b = wysokość tablicy o trzech
# kierunkach, b1 = pierwszy kierunek, kolejne po (b - b1) / 2; d litery, d1 cyfry numeru, o, r
E2_BOARD_MM = {
    "wielkie": {"b": 2170, "b1": 950, "h": 580, "d": 420, "d1": 348, "o": 30, "r": 100},
    "duze": {"b": 1500, "b1": 600, "h": 350, "d": 282, "d1": 210, "o": 20, "r": 100},
    "srednie": {"b": 1200, "b1": 500, "h": 270, "d": 210, "d1": 162, "o": 20, "r": 50},
    "male": {"b": 760, "b1": 320, "h": 220, "d": 132, "d1": 102, "o": 15, "r": 35},
}
# --- Tabela 9.5.5 (s. 457): wyróżnik państwa (owal "PL"): he x we [mm] wg d
COUNTRY_OVAL_MM = {420: (500, 734), 348: (400, 587), 282: (321, 471), 210: (240, 352), 162: (180, 264),
                   132: (160, 235), 102: (120, 176)}
# --- Tabela 9.5.6 (s. 458) + rys. 9.5.18: strzałka na drogowskazach tablicowych [mm]: a szerokość grotu, a1 trzonu,
# c długość, c1 długość grotu
E2_ARROW_MM = {"duze": {"a": 200, "a1": 80, "c": 360, "c1": 160}, "srednie": {"a": 150, "a1": 60, "c": 270, "c1": 120},
               "male": {"a": 100, "a1": 40, "c": 180, "c1": 80}}

# --- placement
E1_BEFORE_CITY_M = 100.0        # pkt 6.3.1.4 (s. 267): 100 m przed skrzyżowaniem w miastach (bliżej, gdy warunki lokalne)
E1_BEFORE_RURAL_M = (150.0, 300.0)
E2_MAX_FROM_JUNCTION_M = 50.0   # pkt 6.3.2.2 (s. 270): drogowskazy tablicowe do 50 m od skrzyżowania
E14_AFTER_JUNCTION_M = 200.0    # pkt 6.3.6.4 (s. 286): około 200 m za skrzyżowaniem (drogi ogólnodostępne)
E14_MAX_ROWS = 4                # pkt 6.3.6.2 (s. 284)
E15_MAX_FROM_JUNCTION_M = 50.0  # pkt 6.3.7.8 lit. a (s. 290): samodzielnie, do 50 m za skrzyżowaniem
E2A_MAX_NAMES = 6               # pkt 6.3.2.2 (s. 271)
OVERHEAD_MIN_M = 5.00           # Tabela 1.11 (brzmienie Dz.U. 2022 poz. 2377): znaki nad jezdnią
LATERAL_MIN_M = 0.50            # pkt 1.5.3 (s. 25-27): krawędź znaku 0,50 - 2,00 m od krawędzi jezdni na ulicach


def size_group(dual: bool, built_up: bool, v_kmh: float, cls: str = "") -> str:
    """Grupa wielkości znaków wg pkt 1.2.1 (s. 7-8) for the roads this generator signs. `cls`: "A" motorway main
    carriageway, "S" expressway main carriageway, "link" (łącznice A / S), "gminna" municipal road."""
    if cls == "A":
        return "wielkie"
    if cls == "S":
        return "duze"
    if cls == "gminna":
        return "male"
    if cls == "link":
        return "srednie"
    if dual and (not built_up or v_kmh > 60.0):
        return "duze"
    return "srednie"


def letter_d_m(sign: str, group: str, rank: int = 0) -> float:
    """Height of capital letters (m) of `sign` (key of E_LETTER_GROUPS) in a size group; rank 0 = the largest."""
    g = E_LETTER_GROUPS[sign][group]
    if g is None:
        raise ValueError(f"{sign} is not used in group {group!r} (Tabela 1.9)")
    return LETTER_D_MM[g[min(rank, len(g) - 1)]] / 1000.0


def allowed_d_mm(sign: str) -> set[int]:
    """Every letter height Tabela 1.9 allows for this sign in any size group."""
    return {LETTER_D_MM[x] for g in E_LETTER_GROUPS[sign].values() if g for x in g}


def route_no(d_m: float) -> dict:
    """Tabela 9.5.3 row for a destination letter height (nearest row, scaled to d): values in metres."""
    key = min(ROUTE_NO_MM, key=lambda k: abs(k / 1000.0 - d_m))
    k = d_m / (key / 1000.0)
    return {n: v / 1000.0 * k for n, v in ROUTE_NO_MM[key].items()}


def route_no_width_m(ref: str, dims: dict) -> float:
    """Width of a route-number sign (rys. 9.5.46 / 9.5.47): 2 m + digits; E-roads: letter + P + digits."""
    r = ref.strip().upper().replace(" ", "")
    gr = dims["d1"] / GR_PER_D
    if r[:1].isalpha():
        return 2 * dims["m"] + text_len_gr(r[0]) * gr + dims["P"] + text_len_gr(r[1:]) * gr
    return 2 * dims["m"] + text_len_gr(r) * gr


def e2_rows_h_m(n_rows: int, d_m: float) -> float:
    """Height of a drogowskaz tablicowy of n rows at letter height d (Tabela 9.5.4 / rys. 9.5.20: b1 for the first
    direction, (b - b1) / 2 for every further one; the 'średnie' proportions 500 / 350 mm at d = 210 mm scale with d;
    'duże' 600 / 450 at 282 and 'małe' 320 / 220 at 132 give the same ratios within 12 %)."""
    k = d_m / 0.210
    return (0.500 + 0.350 * (max(int(n_rows), 1) - 1)) * k


E2_ROW_PITCH_PER_D = 350.0 / 210.0      # = 10 gr / 6 gr: one pas pisma per further row
E2_FIRST_EXTRA_PER_D = 150.0 / 210.0    # b1 - (b - b1) / 2
# Default letter height of rule-built overhead boards: group VI = 210 mm. Tabela 1.9 allows VI for E-1 / E-2 in both
# 'średnie' and 'duże'; the 2019 frontal frame of the Andersa portal (ADR 0139: boards 0.82 m / 1.2 m high with 2 / 3
# rows) gives 0.85 m / 1.20 m by Tabela 9.5.4 'średnie', i.e. the real boards of route C use d = 210 mm.
E_OVERHEAD_D_M = 0.210
E_OVERHEAD_ROW_M = E_OVERHEAD_D_M * E2_ROW_PITCH_PER_D       # 0.35 m (was WORKING_VALUE 0.62 m until ADR 0236)
# Rule boards without photo evidence (roundabout exits, link starts) stay small: group 'małe' (d = 132 mm, IV).
# WORKING_VALUE: by pkt 1.2.1 a national road takes 'średnie' / 'duże'; a 3 m board invented at a place no frame
# shows would be worse than a small one (ADR 0236).
E_RULE_BOARD_D_M = 0.132
# E-1 before a roundabout by rule: names in group IV = 132 mm (allowed for E-1 in 'średnie' and 'duże', Tabela 1.9)
E1_RULE_D_M = 0.132
