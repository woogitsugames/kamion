# Recenzja wewnętrzna R6 pavements-kerbs (2026-11-15)

**Werdykt: PASS z uwagami (P2).** Zadanie z bloku „Dokończenie” jest wykonane: 31 pobranych kadrów obejrzanych i opisanych. Część normowa z 2026-11-14 pozostała bez zmian (audyt 15/15 PASS).

## Sprawdzone
| Wymóg | Wynik | Dowód |
|---|---|---|
| ≥ 30 obejrzanych kadrów | ✓ 31 | R6-073…R6-103; każdy kadr obejrzany jako 960 px + 2 wycinki dolnych narożników |
| Opis = to, co widać | ✓ | ponowne obejrzenie 9 z 41 nowych wierszy (seed 20261115): 8 PASS, 1 FIX (F12 „wysepka” → „pas dzielący”) |
| Liczby kadrów per typ | ✓ (ESTIMATED) | R6-104…R6-113: zliczenia cech z `frames_desc.json`; próba celowa, nie losowa — napisane w metodzie |
| Bez zmyślonych wymiarów | ✓ | wysokości krawężników i rozmiary kostki z obrazu nie są podawane (UNVERIFIED) |
| Kierunek | ✓ | azymut z API. Dla F06/F07 zaznaczona rozbieżność z kursem toru (ok. 55°), Commons bez azymutu |
| Marki | ✓ | billboardy, pylony i budynki z napisami opisane jako „napis firmowy, nie odtwarzamy” |
| Licencje | ✓ | Panoramax/KartaView CC BY-SA 4.0, Commons CC0; kopie w repo ≤ 1600 px + `INDEX.csv` z sha256 |
| UA | ✓ | `fetch.py`: ogólne „Mozilla/5.0 (X11; Linux x86_64) research-client/1.0”, bez nazw organizacji/repo |

## Uwagi
- **P2-1:** „układ jodełkowy” na F36/F37 pochodzi z obrazu w małej skali (UNVERIFIED). Rzędy poprzeczne na F31/F32/F34/F35 są wyraźne.
- **P2-2:** krawężnik nie jest zmierzony. Do porównania z `KERB_HEIGHT = 0,13 m` potrzebny jest pomiar w terenie albo zdjęcie z miarką.
- **P2-3:** brakuje kadrów Sokólskiej, Wysockiego i Kombatantów, sekwencja Tysiąclecia 1155711 nieużyta.
- **P2-4:** wniosek „DDR w Dojlidach szara” opiera się na 7 kadrach z 3 ulic (Commons 2022–2024). Dla trasy C nie ma kadru DDR.
- **P2-5:** wpusty rozpoznane tylko na estakadzie (2 kadry). Rozstaw wpustów nadal UNVERIFIED.
