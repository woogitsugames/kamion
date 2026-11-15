# Recenzje kodu s21 (chmura) — podsumowanie dla lidera

Data: 2026-11-15. Sprawdzone 8 pozycji (R1–R8), każdą recenzował osobny agent. Pełne raporty: `docs/reports/REVIEW-2026-11-15-s21-code-<nr>.md`. Nic nie zostało scalone przez chmurę. #103 i #104 lider scalił do main wcześniej; ich FIX trzeba zrobić osobnym commitem.

| PR | gałąź / ADR | werdykt | najważniejszy FIX | kolejność |
|---|---|---|---|---|
| #103 | legal-0230 / 0230 | **SCAL** (już w main) | P1: audyt licencji po scaleniu znów czerwony. 142 pliki `research/cloud2/*` bez wpisu; dopisać 4 wiersze w `docs/LICENSES.md` i poprawić „360 → 0” w ADR | 1 ✓ |
| #104 | region-select-0229 / 0229 | **SCAL** (już w main) | P1: zestaw `d67` (`region_catalog.json:159`) bez Dojlidy, niezgodny dosłownie z D67. Opisać w ADR i dodać `d67-full` (decyzja z właścicielem). P2: pusta lista `-Regions` ma kończyć build błędem | 2 ✓ |
| #80 | dk65-d65-data / 0215 | (poza listą; zależność) | gałąź nadal ma `width: 6.9`; wg D66 ma być **6,6 m** (poprawka jest na `origin/verify-cloud-c`) | 3 |
| #98 | dk65-k1-0220 / 0220 | **FIX** | P1 `markings.py:276-279`: `edge_dashed_spans` przedłuża kreskę do końca łańcucha także przy dziurze (None). P1: ADR 0220 nadal 6,9 m zamiast 6,6 m (D66) | 4 |
| #93 | putry-ring-0198b / 0226 | **FIX** (lekki) | P1: usunąć `STATUS.md` i wpisany raport recenzji. P1: `apron_width` (#93) i `truck_apron` (#97) zapisują tę samą szerokość ISLAND; wybrać jedno pole albo dodać walidację | 5 (rebase na main) |
| #82 | piers-0198 / 0198 | **ZAMKNIJ** | zastąpiony przez #93 (zawiera wszystkie jego commity) | — |
| #97 | roundabout-0218 / 0218 | **SCAL** | P1 przed nałożeniem override: w przykładzie `material: kostka` wychodzi ciepły brąz, właściciel ma jasną kostkę/beton. ADR §6 dopiąć do zdjęć S21 | 6 |
| #101 | treerows-0222 / 0222 | **SCAL** | P2 `tree_rows.py:372,378`: częściowo przejęta linia BDOT zostaje bez drzew | 7 |
| rail-fix-s21 | (bez PR) / 0217 | wejść **ZAMIAST #96** | konflikt z main tylko w `stage.py`; cytuje uchylony Dz.U. 2015/1744, trzeba podmienić na 2025 poz. 1105 | 8 (zamknąć #96) |
| #106 | seams-0224 / 0224 | **SCAL** | P1: raport SEAMS i ADR przeliczyć po scaleniu #80 + #98 (z gałęzi łączonej: 22 FAIL / 5 UWAGA, 0 nowych) | 9 |
| #102 | rail-dk65-0223 / 0223 | **FIX** | P0: po scaleniu z rail-fix są dwa mechanizmy `rail_crossing`; `OVERRIDE_KEYS` (`rail.py:212`) daje `ValueError` w dw671-tykocin-01, G-2 daje `KeyError 'arm_l_m'` | 10 (rebase po rail-fix) |

## Kolejność scalania (proponowana)
1. #103 ✓ → 2. #104 ✓ → 3. #80 z poprawką D66 6,6 m → 4. #98 (FIX 1–2, rebase; kamery dk65-03 = suma po id; `overrides.yaml` dk65-02…05: width 6,6 + blok ADR 0220; `markings.py` = suma) → 5. #93 (baza na main, FIX 1) → 6. #97 (rozstrzyga FIX 2 z #93; po #98 i #97 jedno `fidelity/run.py`) → 7. #101 (w `STATUS.md` wziąć wersję z main) → 8. rail-fix-s21 (zamknąć #96 jako zastąpiony) → 9. #106 (`overrides.yaml` tykocina = oba bloki) → 10. #102 po rebase z FIX P0/P1 (`stage.py`: zachować `rail.blocked` + `VG.place(..., tree_rows=)`). #82 zamknąć.

Po każdej zmianie `route_start.json` (#80, #98, #97) uruchomić `python scripts/export-region-catalog.py`, inaczej test EditMode katalogu regionów padnie (#104).

## Testy (chmura, bez Unity/Data/raw)
Na main (`855af773e`) pełne `tests/gis` przechodzi z 3 znanymi failami: `test_report_not_stale` (brak Data/raw), `test_forest_0187::…wall_and_mantle_rows` i `test_world_v31::…forest_hlod`. Żaden PR nie dodaje nowych failów. Jedyny wyjątek to scalenie próbne rail-fix + #102: 2 faile, czyli P0 z #102. `dotnet test tools/about-runner` 30/30 (#103). Liczby per PR są w raportach. Część pełnych przebiegów przerwano, bo 8 recenzentów dzieliło CPU; raporty to zaznaczają.

## Budżet
Region C (`stretch_04` 2,02 M High już na main, ponad limitem 2 M) nie rośnie od żadnego PR. #93 dokłada ok. +1,1–1,3 k tris w `putry_above` (ESTIMATED), #102 ok. 11,9 k tris na 5 kafli DK65 (szacunek z ADR 0223), #101 nie zmienia regionów bez `tree_rows.yaml`. Najcięższa kamera dk65-01…05 to 1 639 892 tris High (dk65-05, z `streetscape_qa.json`). Wszystko potwierdzić `build_world` + visual-qa + A16; komendy są w raportach.
