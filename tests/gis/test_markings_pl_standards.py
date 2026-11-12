"""Audit M10: stałe oznakowania poziomego i geometrii vs przepisy (bez Data/raw).

Wartości przepisowe:
  [ZNAKI-Z2]  załącznik nr 2 do rozporządzenia MI z 3.07.2003 (t.j. Dz.U. 2019 poz. 2311):
              pkt 2.2.1 (linie podziału pasów, szerokość 0,12 m, P-1a 4/8 m, P-1b 2/4 m, P-2a >= 20 m,
              5,80 m), pkt 2.2.2 (P-7a/P-7b szerokie 0,24 m), pkt 3.2.1 + rys. 3.2.1.2 (P-8: krótka 5 m,
              długa 7,5 m, odstępy 15/30 m), pkt 4.2.1 + rys. 4.2.1.1 (P-10: s = 4,0 m, pasy 0,5/0,5 m),
              pkt 4.2.2 (P-11), pkt 4.2.3 + rys. 4.2.3.1 (P-12: 0,50 m), pkt 4.2.4 + rys. 4.2.4.1
              (P-13: trójkąty 0,50 x 0,70 m, odstęp 0,25 m), pkt 4.2.5 + rys. 4.2.5.1 (P-14: prostokąty
              0,75 x 0,50 m, odstęp 0,25 m, >= 2,0 m przed sygnalizatorem obok jezdni i przed P-10/P-11).
  [PTB2022]   rozporządzenie MI z 24.06.2022 (Dz.U. 2022 poz. 1518), które zastąpiło WT z 1999 r.
              (t.j. Dz.U. 2016 poz. 124): § 17 ust. 1 (szerokości pasów wg klasy), § 17 ust. 3 (jezdnia
              1-pasowa >= 3,50 m), § 23 ust. 7 (opaska zewnętrzna 0,75 m, min 0,50 m w trudnych
              warunkach), § 23 ust. 10 (pobocze gruntowe 1,25/1,00/0,75 m), § 80 ust. 1 (skrajnia 5,00 m
              A/S, 4,50 m pozostałe). WT 1999 § 43 ust. 5: krawężnik 6-16 cm ponad jezdnię.

Uruchomienie: uv run --project tools/worldgen pytest tests/gis/test_markings_pl_standards.py -q
"""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
from roads import standards as S  # noqa: E402
from roads.markings import arrow_glyph  # noqa: E402


# --- szerokości pasów wg klasy drogi (PTB2022 § 17 ust. 1: standardowo / w trudnych warunkach) ----------

@pytest.mark.parametrize("cls,std,diff", [
    ("A", 3.75, 3.50),
    ("S", 3.50, 3.25),
    ("GP", 3.50, 3.25),
    ("G", 3.50, 3.00),   # dopuszcza się 3,25 lub 3,00
    ("Z", 3.00, 2.75),
    ("L", 2.75, 2.50),
    ("D", 2.50, 2.25),
])
def test_lane_width_by_class(cls, std, diff):
    assert S.LANE_WIDTH[cls] == (std, diff)


def test_single_lane_min():
    # § 17 ust. 3: jezdnia z jednym pasem ruchu - mniej niż 2 pasy, ale nie mniej niż 3,50 m
    assert S.SINGLE_LANE_MIN == 3.50


# --- opaska i pobocze (PTB2022 § 23) ----------------------------------------------------------------------

def test_edge_strip():
    # § 23 ust. 7: opaska zewnętrzna 0,75 m (A/S/GP), w trudnych warunkach nie mniej niż 0,50 m
    assert S.EDGE_STRIP["A"] == 0.75
    assert S.EDGE_STRIP["S"] == 0.75
    assert S.EDGE_STRIP["GP"] >= 0.50


def test_shoulder_width():
    # § 23 ust. 10 pkt 3-5: pobocze gruntowe przy jezdni G 1,25 m, Z 1,00 m, L/D 0,75 m (standardowo)
    assert S.SHOULDER_W["G"] == 1.25
    assert S.SHOULDER_W["Z"] == 1.00
    assert S.SHOULDER_W["L"] == 0.75
    assert S.SHOULDER_W["D"] == 0.75


# --- linie podłużne (ZNAKI-Z2 pkt 2.2.1 / 2.2.2) -----------------------------------------------------------

def test_line_widths():
    assert S.LINE_W_NARROW == 0.12   # wąska (P-1a/P-1b/P-2a, rys. 2.2.1.x)
    assert S.LINE_W_WIDE == 0.24     # szeroka (P-2b rys. 2.2.1.7; P-7a/P-7b szerokie rys. 2.2.2.2)


def test_dash_patterns():
    assert S.DASH["P-1a"] == (4.0, 8.0)   # rys. 2.2.1.1, V > 70 km/h
    assert S.DASH["P-1b"] == (2.0, 4.0)   # rys. 2.2.1.2, V <= 70 km/h
    assert S.DASH["P-1d"] == (1.0, 1.0)   # rys. 2.2.1.4, prowadząca wąska na skrzyżowaniach


def test_p2a_min_len():
    assert S.P2A_MIN_LEN == 20.0         # pkt 2.2.1.6: linia pojedyncza ciągła wąska co najmniej 20 m


def test_segregation_min_carriageway():
    assert S.SEGREGATION_MIN_CARRIAGEWAY == 5.80   # pkt 2.2.1


# --- znaki poprzeczne (ZNAKI-Z2 rozdz. 4) -------------------------------------------------------------------

def test_p10_crossing():
    assert S.P10_WIDTH == 4.0            # pkt 4.2.1: s = 4,0 m (w zabudowanym min 2,5 m)
    assert S.P10_STRIPE == 0.50          # rys. 4.2.1.1: pasy 0,5 m
    assert S.P10_GAP == 0.50             # rys. 4.2.1.1: przerwy 0,5 m
    assert S.P10_EDGE_MAX == 0.50


def test_p12_stop_line():
    assert S.P12_W == 0.50               # rys. 4.2.3.1


def test_p13_triangles():
    assert (S.P13_BASE, S.P13_GAP, S.P13_H) == (0.50, 0.25, 0.70)   # rys. 4.2.4.1


def test_p14_rectangles():
    assert (S.P14_LEN, S.P14_GAP, S.P14_DEPTH) == (0.75, 0.25, 0.50)  # rys. 4.2.5.1
    assert S.P14_BEFORE_SIGNAL == 2.0    # pkt 4.2.5: >= 2,0 m przed sygnalizatorem obok jezdni
    assert S.P14_BEFORE_CROSSING == 2.0  # pkt 4.2.5: >= 2,0 m przed P-10/P-11


# --- strzałki P-8 (ZNAKI-Z2 pkt 3.2.1, rys. 3.2.1.2) ---------------------------------------------------------

def test_arrow_dims():
    assert S.ARROW_SHORT["len"] == 5.00    # rys. 3.2.1.2 a) krótka
    assert S.ARROW_LONG["len"] == 7.50     # rys. 3.2.1.2 b) długa (V > 70 km/h)
    assert S.ARROW_SPACING == {"short": 15.0, "long": 30.0}  # pkt 3.2.1


def test_arrow_glyph_geometry():
    g = arrow_glyph(["through"], long=False)
    xs = [p[0] for p in g.exterior.coords]
    assert max(xs) - min(xs) == pytest.approx(S.ARROW_SHORT["len"], abs=0.01)
    g = arrow_glyph(["through"], long=True)
    xs = [p[0] for p in g.exterior.coords]
    assert max(xs) - min(xs) == pytest.approx(S.ARROW_LONG["len"], abs=0.01)
    # skręt: główka boczna, ale długość w osi pasa nie przekracza długości strzałki
    g = arrow_glyph(["left"], long=False)
    ys = [p[1] for p in g.exterior.coords]
    assert max(ys) > 0.5


# --- geometria drogi: krawężnik, pochylenie, skrajnia (WT 1999 / PTB2022) -----------------------------------

def test_kerb_height_in_regulation_range():
    # WT 1999 § 43 ust. 5: chodnik wyniesiony ponad krawędź jezdni na wysokość od 6 cm do 16 cm
    assert 0.06 <= S.KERB_HEIGHT <= 0.16


def test_crossfall():
    assert S.CROSSFALL == 0.02           # 2% - praktyka projektowa (WT 1999 tabele, PTB2022 § 18 wynikowe)


def test_clearance():
    # PTB2022 § 80 ust. 1: skrajnia >= 5,00 m (A/S), >= 4,50 m (GP/G/Z/L/D)
    assert S.CLEARANCE_BY_CLASS["A"] == 5.00
    assert S.CLEARANCE_BY_CLASS["S"] == 5.00
    for cls in ("GP", "G", "Z", "L", "D"):
        assert S.CLEARANCE_BY_CLASS[cls] == 4.50
    assert S.clearance_height("unknown") == S.BRIDGE_CLEARANCE == 4.50


# --- czyste funkcje pomocnicze generatora --------------------------------------------------------------------

def test_road_class_mapping():
    assert S.road_class("motorway") == "A"
    assert S.road_class("trunk") == "GP"
    assert S.road_class("primary") == "G"
    assert S.road_class("tertiary") == "Z"
    assert S.road_class("residential") == "L"
    assert S.road_class("service") == "D"
    assert S.road_class("track") == "D"      # fallback


def test_grade_limit():
    assert S.grade_limit("motorway_link", None) == (0.07, 0.07)   # PTB2022 § 62 ust. 2: łącznice <= 7%
    assert S.grade_limit("service", None) == (0.12, 0.12)        # drogi wewnętrzne - niepubliczne
    std, diff = S.grade_limit("primary", 50.0)                    # Vp = 50 -> § 20 ust. 2
    assert (std, diff) == (0.09, 0.11)


def test_lane_layout_two_way():
    from roads.markings import lane_layout
    sec = SimpleNamespace(lane_w=3.5, edge_strip=0.0, oneway=False, lanes_fwd=1, lanes_bwd=1,
                          lanes=2, width=7.0)
    lat_c, bounds, centres = lane_layout(sec, 3.5, 1)
    assert lat_c == 0.0
    assert bounds == []
    assert centres["fwd"] == [-1.75]
    assert centres["bwd"] == [1.75]
