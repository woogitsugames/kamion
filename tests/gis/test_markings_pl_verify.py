"""Weryfikacja M10/M25 z zrodel pierwotnych: stale oznakowania poziomego vs rozporzadzenie (zadania 18, 25).

P-11 zostalo skorygowane w zadaniu 25 (M25) do wartosci z rys. 4.2.2.1 - test przechodzi.
Pozostale testy xfail(strict=True) dokumentuja rozbieznosc miedzy wartoscia w generatorze
a wartoscia z rozporzadzenia (cytat ze zrodla pierwotnego) do czasu decyzji wlasciciela
(p21_hatch / P-21 czeka na decyzje wlasciciela - NIE zmieniac).

Zrodlo pierwotne: zalacznik nr 2 do rozporzadzenia Ministra Infrastruktury z dnia
3 lipca 2003 r. w sprawie szczegolowych warunkow technicznych dla znakow i sygnalow
drogowych oraz urzadzen bezpieczenstwa ruchu drogowego i warunkow ich umieszczania
na drogach - tekst jednolity Dz.U. 2019 poz. 2311 (WDU20190002311, status "obowiazujacy",
zmieniony m.in. Dz.U. 2021 poz. 2066, Dz.U. 2022 poz. 2377, Dz.U. 2026 poz. 132;
odczyt 2026-11-12 z ISAP/ELI: api.sejm.gov.pl / isap.sejm.gov.pl, zalacznik nr 2 =
strony Dz.U. 526-906). Numery stron ponizej to strony Dziennika Ustaw poz. 2311.

Uruchomienie: uv run --project tools/worldgen pytest tests/gis/test_markings_pl_verify.py -q
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
from roads import p21_hatch  # noqa: E402
from roads import standards as S  # noqa: E402

pytestmark = pytest.mark.unit


def test_p11_square_and_gap_vs_rys_4_2_2_1():
    # M25: skorygowane do rys. 4.2.2.1 (zal. nr 2, Dz.U. 2019 poz. 2311, str. 569, PDF
    # D2019000231102.pdf on isap.sejm.gov.pl): kwadraty 0,5 m, odstep 0,5 m; pkt 4.2.2
    # (str. 569): "Powierzchnie przejazdu wyznaczaja dwie linie przerywane, poprzeczne
    # do osi jezdni... nie mniejsza niz 1,8 m (jednokierunkowy) / 3,0 m (dwukierunkowy)".
    assert S.P11_SQUARE == 0.50
    assert S.P11_GAP == 0.50


@pytest.mark.xfail(
    strict=True,
    reason=(
        "NIEZGODNE: p21_hatch.py:28-29 STRIPE_W_M/STRIPE_GAP_M = 0.5/1.0 m, a pkt 5.2.7.1 "
        "(zal. nr 2, Dz.U. 2019 poz. 2311, str. 587): \"Szerokosc linii wewnetrznych oraz "
        "odstep miedzy nimi... wynosza odpowiednio: - 0,24 m z odstepem 0,39 m - na drogach "
        "o dopuszczalnej predkosci do 70 km/h (liniowanie waskie) - znak P-21a, - 0,60 m "
        "z odstepem 0,98 m - na pozostalych drogach (liniowanie szerokie) - znak P-21b.\" "
        "Obramowanie P-7b 0,24 m (BORDER_W_M) jest zgodne."
    ),
)
def test_p21_hatch_vs_pkt_5_2_7_1():
    assert (p21_hatch.STRIPE_W_M, p21_hatch.STRIPE_GAP_M) in {(0.24, 0.39), (0.60, 0.98)}
