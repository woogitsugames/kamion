# FIX typology-fix-s23 — PR #123 (ADR 0238) do stanu scalalnego

- Gałąź: `typology-fix-s23` (z `origin/typology-0238` `243b3065b`), scalony `origin/main` `ade885234` (zawiera #122 i c-regen2)
- Źródła uwag: `docs/reports/REVIEW-2026-11-15-s22-code-123.md`, `REVIEW-2026-11-15-s22-code-SUMMARY.md`,
  `INTEGRATION-2026-11-15-c-regen2-s23.md` („Co blokuje #123”)
- Bez Unity, bez `build_region` / `build_world`, bez dotykania `Data/raw`.

## Commity
| sha | co |
|---|---|
| `7d1764d14` | merge `origin/main` — konflikty: `buildings_mesh.py:storey_plan`, `docs/LICENSES.md` (suma), `STATUS.md` (= main) |
| `80e91c5eb` | P1: test budżetu bez liczb z innego stanu; baseline C i Dojlid przeliczone na kodzie main; test regresji `storey_plan` |
| `ea81e80d6` | P2: `BLOCK_ETICS_SHARE = 0.7` (WORKING_VALUE), opis w ADR 0238 |
| (ten) | raport |

## Zmiany (plik:linia)
1. **Konflikt `storey_plan` (P1)** — `tools/worldgen/streetscape/buildings_mesh.py:98-122` (`:112-114`). Zostaje
   `if p.get("storeys_fixed"): return int(nb), shb, zb` z #122. Usunięta linia `lo, hi = …` z #122, bo
   nadpisywała `storey_fit_m` kamienicy (#123, `:104-107` w `storey_plan`). W jej miejscu jest komentarz. Diff gałęzi względem
   `origin/main` obejmuje tylko pliki #123 (8 plików `tools/worldgen`, testy, ADR, docs/05, LICENSES). Kod #122 z main
   jest więc nietknięty poza tą jedną linią. `Data/` i `tools/worldgen/generated/` nie mają różnic względem main.
2. **Test regresji scalenia** — `tests/gis/test_typology_0238.py:196-207`
   `test_storey_plan_keeps_the_kamienica_fit_with_the_0242_storeys_fixed_rule`. Kamienica 2 × 3,9 m mieści się w
   zakresie kamienicy 2,8–4,0, ale nie w zakresie bloku 2,6–3,8, więc wynik musi być (2, 3,9, 0,6). `storeys_fixed` daje
   ten sam wynik. Biuro ze `storeys_fixed` zachowuje 3 kondygnacje przy 4,77 m na kondygnację. **Sprawdzone mutacją:**
   po przywróceniu linii `lo, hi` z #122 test pada (1 failed), po cofnięciu przechodzi.
3. **Wpisane `2022535` (P1)** — `tests/gis/test_typology_0238.py:317-330`. `qa_tris_high` jest teraz czytane z
   bieżącego `Data/Regions/<id>/generated/streetscape_qa.json` w chwili testu. Dla każdej kamery z szacunkiem
   `est_tris_high ≤ qa_tris_high` i `est_tris_low ≤ qa_tris_low`. Dla C limit **2 000 000 High** (`C_TRIS_HIGH_LIMIT`,
   `:23`) sprawdza się dla `stretch_04` i wszystkich kamer C. Porównanie jest względne (Δ ≤ 0 względem baseline
   per chunk), jak w PR.
4. **Baseline Dojlid i C (P1)** — `tests/gis/data/typology_0238_baseline_bialystok-{dojlidy,industrial-c}.json`.
   Przeliczone harnessem `tools/worldgen/qa/typology_budget.py` (z PR) na **kodzie generatora i danych z `origin/main`
   `ade885234`** (`git archive` do scratchpada, bez `streetscape/typology.py`, raport `subtypes: null`, czyli kod sprzed
   #123). Stare baseline nie zgadzały się z main w obu regionach: Dojlidy w 31 z 415 budynków, C w 43 z 644. Przyczyna w C
   jest UNVERIFIED (recenzja podawała, że #122 nie zmienia C). Możliwe źródła to inne PR-y scalone do main po baseline
   #123 albo dane po c-regen2. Dojlidy prawdopodobnie zmienił #122 (recenzja: hala `bdot:2058ad2f-…`).
   Baseline z wyciętego drzewa zgadza się z pełnym worktree, bo test bit-identyczności przechodzi na > 250 budynkach
   na region. Nie zadziałał więc cichy fallback.
   - Dojlidy: 501 031 / 68 367 → **500 537 / 68 404** (LOD0 / LOD1, harness)
   - C: 964 087 / 101 067 → **964 112 / 101 095**
5. **P2 udział bloków nieocieplonych** — `buildings_mesh.py:82-85` (stała `BLOCK_ETICS_SHARE = 0.7`, WORKING_VALUE, ze
   źródłem braku) i `:1437` (użycie); `docs/adr/0238-…md` „Otwarte 3”. Wartość jest bez zmian, więc zero zmian
   geometrii i barw. Zmiana wartości wymaga renderu.
6. **P2 `STATUS.md` w gałęzi** — po scaleniu identyczny z main (diff z `origin/main` = 0).

## Budżet trójkątów — ESTIMATED (harness #123 vs nowy baseline, bez przebudowy)
Szacunek = zacommitowany `frame_estimate` + Δ harnessu per chunk. To nie jest pomiar.
| region / kamera | QA (main, c-regen2) | Δ High | Δ Low | szacunek High |
|---|---|---|---|---|
| C `stretch_04` | 1 985 807 | −697 | −303 | **≈ 1 985 110** (limit 2 M, zapas ≈ 14 890) |
| C `route_onramp_andersa_above` | 1 966 411 | −889 | −231 | ≈ 1 965 522 |
| C `route_onramp_andersa` | — | −1 057 | −255 | ≈ 1 850 958 |
| C `fire_station_abeam` | — | −382 | −176 | ≈ 1 170 237 |
| Dojlidy max High (`photo_P11-063`) | 1 768 010 | −232 | — | ≈ 1 767 778 |
Wszystkie 23 kamery C i 17 kamer Dojlid mają Δ ≤ 0 (High i Low). Harness, suma budynków: C 964 112 → 959 601
(LOD0), 101 095 → 100 626 (LOD1); Dojlidy 500 537 → 495 883, 68 404 → 67 876.
**Nie ujęte:** `BASE_M` 1,5 działa dopiero po `build_region`. Zmienia wysokości `bdot10k_storeys`, więc może zmienić
liczbę kondygnacji i pasów okien. Wpływ UNVERIFIED, trzeba go zmierzyć po przebudowie (P2-L z recenzji).

## Testy
- `uv run --project tools/worldgen python -m pytest tests/gis -q -k "typology or 0238 or buildings or storey or 0242"`:
  **124 passed, 1635 deselected, 0 failed** (259,6 s; uruchomione na drzewie z `BLOCK_ETICS_SHARE`).
- Szerszy zestaw z recenzji (`building or facade or frontage or typology or doj or roof or house or materials`),
  uzupełnienie w 3 przebiegach: `test_dojbld_0185.py test_dojind_0196.py test_dojlidy_0242.py` **27 passed, 1 skipped**;
  `-k "(facade or frontage or roof) and not (…)"` **45 passed, 1 skipped**; `-k "(doj or house or materials or building)
  and not (…)"` **93 passed, 2 skipped**. Razem z zestawem wyżej: **289 passed, 4 skipped, 0 failed**.
- `tests/gis/test_typology_0238.py` osobno: **22 passed** (22,8 s).
- `python scripts/export-region-catalog.py --check`: **exit 0**.

## Czego NIE sprawdzono
- Przebudowa C i Dojlid (`build_region` + `build_world`) i zmierzony `frame_estimate` / `stats.txt` po #123 + `BASE_M`.
- Unity: import, kompilacja, kamery kontrolne, `visual-critic` (front pawilonu na Low, barwy bloków, kamienica).
- Pełny `pytest tests/gis` (tylko zestaw z `-k` wyżej).
- Baseline jest związany z kodem budynków w main `ade885234`. Jeśli przed scaleniem #123 do main wejdzie inna zmiana
  generatora budynków, test bit-identyczności znów padnie. Wtedy trzeba przeliczyć baseline tak jak w pkt 4.

## Komendy dla lidera
Head PR #123 (`origin/typology-0238`) jest bez zmian (`243b3065b`). Poprawki są tylko na `origin/typology-fix-s23`.
Trzeba scalić tę gałąź albo przepiąć PR na nią.
```
# scalenie (gałąź już zawiera main ade885234)
git -C C:\Users\matma\Documents\Claude\kamion merge --no-ff origin/typology-fix-s23
# jeśli main się zmienił: przeliczyć baseline na kodzie main (bez #123), np.
#   git archive origin/main tools/worldgen Data/Regions/bialystok-industrial-c Data/Regions/bialystok-dojlidy | tar -x -C <tmp>
#   cp tools/worldgen/qa/typology_budget.py <tmp>/tools/worldgen/qa/
#   uv run --project tools/worldgen python <tmp>/tools/worldgen/qa/typology_budget.py --region <id> --out tests/gis/data/typology_0238_baseline_<id>.json
uv run --project tools/worldgen python -m pytest tests/gis -q -k "typology or 0238 or buildings or storey or 0242"
# przebudowa (po scaleniu, gdy maszyna wolna)
uv run tools/worldgen/build_region.py --region bialystok-industrial-c
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c
uv run tools/worldgen/build_region.py --region bialystok-dojlidy
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -OutputDir artifacts/visual-qa/typology-0238/low
pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting clear -OutputDir artifacts/visual-qa/typology-0238/high
# kamery: r10_block_*, photo_biezenstwa_ground, g3b_*, stretch_04; potem visual-critic; stretch_04 tris_high <= 2 000 000
```
