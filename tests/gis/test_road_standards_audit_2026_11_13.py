"""Audyt M36 (2026-11-13): stale geometrii/wyposazenia drogi vs zrodla pierwotne, bez Data/raw.

Zrodla pierwotne (odczyt 2026-11-13 z ELI/ISAP: api.sejm.gov.pl, isap.sejm.gov.pl,
dziennikustaw.gov.pl; numery stron Dz.U. tam, gdzie podano):
  [PTB2022]  rozporzadzenie MI z 24.06.2022 r. (Dz.U. 2022 poz. 1518, zmienione Dz.U. 2025
             poz. 1352 - § 17 ust. 5 i § 23 ust. 10 pkt 5 brzmienie wynikowe/bez wplywu na
             wartosci tu uzyte; zweryfikowane w PDF D20251352.pdf).
  [ZNAKI]    rozporzadzenie MI z 3.07.2003 r., t.j. Dz.U. 2019 poz. 2311 (status "obowiazujacy";
             nowelizacje po tescie jednolitym: Dz.U. 2021 poz. 438 [zal. 1 tylko], 2021 poz. 2066
             [zal. 1, Tabela 1.11], 2022 poz. 2377 [zal. 1 pkt 5.2.19/5.2.20/5.2.48.1/5.2.49],
             2026 poz. 132 [zal. 1, 2 i 4]) - wszystkie cztery sprawdzone w ELI/ISAP 2026-11-13.

Zakres: dopelnienie test_markings_pl_standards.py / test_signs_pl_audit.py o pozycje tam
niepokryte oraz o poprawke M36: SHOULDER_W["GP"] 1.25 -> 0.75 (PTB2022 § 23 ust. 10 pkt 2).

Uruchomienie: uv run --project tools/worldgen pytest tests/gis/test_road_standards_audit_2026_11_13.py -q
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
from roads import standards as S  # noqa: E402

pytestmark = pytest.mark.unit


# --- pobocze gruntowe (PTB2022 § 23 ust. 10) ------------------------------------------------------------------

def test_shoulder_w_gp_next_to_opaska():
    """PTB2022 § 23 ust. 10 pkt 2: "standardowo 0,75 m ... w przypadku części pobocza
    przyległej do opaski zewnętrznej" (Dz.U. 2022 poz. 1518). Poprawka M36: bylo 1.25
    (wartosc pkt 1, tylko przy pasie awaryjnym A/S)."""
    assert S.SHOULDER_W["GP"] == 0.75


def test_shoulder_w_other_classes():
    """PTB2022 § 23 ust. 10 pkt 1: 1.25 m przy pasie awaryjnym (A/S); pkt 3-5: 1.25 (G),
    1.00 (Z), 0.75 (L/D) standardowo."""
    assert S.SHOULDER_W["A"] == 1.25
    assert S.SHOULDER_W["S"] == 1.25
    assert S.SHOULDER_W["G"] == 1.25
    assert S.SHOULDER_W["Z"] == 1.00
    assert S.SHOULDER_W["L"] == 0.75
    assert S.SHOULDER_W["D"] == 0.75


# --- pochylenia podluzne wg predkosci do projektowania (PTB2022 § 20 ust. 2) ---------------------------------

@pytest.mark.parametrize("vp,std,diff", [
    (130, 0.04, 0.05),   # pkt 1: Vp 140 lub 130 km/h
    (110, 0.05, 0.06),   # pkt 2: 120 lub 110
    (90, 0.06, 0.07),    # pkt 3: 100 lub 90
    (70, 0.07, 0.08),    # pkt 4: 80 lub 70
    (60, 0.08, 0.10),    # pkt 5: 60
    (50, 0.09, 0.11),    # pkt 6: 50
    (0, 0.10, 0.12),     # pkt 7: 40 lub 30 (catch-all w kodzie)
])
def test_max_grade_by_vp(vp, std, diff):
    """PTB2022 § 20 ust. 2: "Pochylenie podłużne jezdni ... powinno wynosić nie więcej niż:
    standardowo 4% ... jeżeli prędkość do projektowania wynosi 140 lub 130 km/h" (i kolejne
    punkty 5/6/7/8/9/10% wg Vp; w trudnych warunkach +1-2 pkt)."""
    assert (vp, std, diff) in S.MAX_GRADE_BY_VP


def test_grade_limit_ramp_documented_two_values():
    """PTB2022 § 62 ust. 2: "Pochylenie podłużne jezdni łącznicy węzła typu WA powinno być
    nie większe niż 6%, a jezdni łącznicy węzła typu WB lub WC - nie większe niż 7%".
    Kod stosuje 7% dla wszystkich *_link (przypadek przedziału dwuwartościowego - patrz
    raport M36, punkt 4: propozycja reguły WA/WB-WC bez wdrażania). Dane regionu: max 5.13%."""
    assert S.MAX_GRADE_RAMP == 0.07
    assert S.grade_limit("motorway_link", None) == (0.07, 0.07)


# --- chodnik (PTB2022 § 29 ust. 1, § 33) ----------------------------------------------------------------------

def test_sidewalk_width_vs_29_1():
    """PTB2022 § 29 ust. 1: "Szerokość chodnika powinna być nie mniejsza niż 1,80 m"."""
    assert S.SIDEWALK_W >= 1.80
    assert S.SIDEWALK_W == 2.00  # WORKING_VALUE powyzej minimum


def test_sidewalk_crossfall_vs_33():
    """PTB2022 § 33: "Pochylenie poprzeczne drogi dla pieszych ... powinno być nie większe
    niż 2%" (chodnika do 3% w trudnych warunkach)."""
    assert S.SIDEWALK_CROSSFALL <= 0.02


# --- krawężnik (PTB2022 § 89 ust. 2 pkt 1) ---------------------------------------------------------------------

def test_kerb_height_vs_89():
    """PTB2022 § 89 ust. 2 pkt 1: dopuszcza się zmniejszenie odległości bariery do 0,50 m
    od krawędzi pasa ruchu, "jeżeli na krawędzi pasa ruchu znajduje się krawężnik o wysokości
    wynoszącej co najmniej 0,12 m"."""
    assert S.KERB_HEIGHT >= 0.12


# --- wysokości znaków (ZNAKI zał. 1 Tabela 1.11, brzmienie po Dz.U. 2021 poz. 2066 pkt 1.5.3) -------------------

def test_sign_heights_vs_tabela_1_11():
    """Zał. nr 1 Tabela 1.11 (Dz.U. 2021 poz. 2066): w obszarze zabudowanym znaki A-D min.
    2,00 m (2,20 m na chodniku); nad jezdnią min. 5,00 m."""
    assert S.SIGN_H_MIN == 2.00
    assert S.SIGN_H_SIDEWALK == 2.20
    assert S.SIGN_H_OVERHEAD == 5.00


# --- skrajnia (PTB2022 § 80 ust. 1) ---------------------------------------------------------------------------

def test_clearance_vs_80_1():
    """PTB2022 § 80 ust. 1: "Wysokość skrajni powinna być nie mniejsza niż: 5,00 m - w przypadku
    skrajni jezdni drogi klasy A lub S; 4,50 m - ... klasy GP, G, Z, L lub D"."""
    assert S.CLEARANCE_BY_CLASS["A"] == 5.00
    assert S.CLEARANCE_BY_CLASS["S"] == 5.00
    for cls in ("GP", "G", "Z", "L", "D"):
        assert S.CLEARANCE_BY_CLASS[cls] == 4.50
