# c-regen2-s23 (live) — etap 1: przygotowanie drugiej przebudowy C + Dojlidy
Worktree `.claude/worktrees/c-regen2-s23`, gałąź `c-regen2-s23`, baza main `7e044ac0a`. Bez Unity/build_world w tym etapie.

## UWAGI DLA LIDERA (decyzje przed etapem 2)
1. **#123 typology-0238 = FIX** w recenzji, head `243b3065b` bez zmian od recenzji → NIE scalone. Skutek: kolejna (trzecia) przebudowa C po poprawkach #123, chyba że lider zleci 3 poprawki P1 w gałęzi integracyjnej przed etapem 2.
2. **#119 tests-hygiene-0245 nie jest w main** (`merge-base --is-ancestor` = 1), a recenzja każe scalić go PRZED przebudową C (zmienia strumień losowy płaszcza lasu). Nie ma go w moim zadaniu — nie scalam; do decyzji lidera.

## Kroki
- [23:4x] worktree + junctions Data/raw/{gugik,osm,refs,mapillary,fab}; kopie cc0/_raw/megascans (0,9 GB). Heady 7 PR = sha z recenzji (0 nowych commitów). Żaden PR nie zmienia ProjectSettings/Packages/asmdef/scen/prefabów/generated.
- [23:5x] Merge #109 `9c8ab51a0` (pytest 3 pliki: 33 passed), #110 `3d4144f9e`, #111 `72ce5ed05` (tools/perf/tests 61 passed). RegionImporter.cs: oba hunki (l. 308 i 462), RenderOverrides.cs: ThinShadows + GpuAbOverrides, CurrentRevision 240 — jak w recenzji.
- Znalezisko #110 × #120: `thin_shadow_audit.py --check` exit 1 (1 niezgodność `lamp_old_concrete_led_9m`, prototyp dodany do main po #110) → dopisany do FAMILY_EXCEPTIONS (osobny commit); teraz 155 prototypów, 48 thin, 0 niezgodności.


- [00:1x] Merge #124 `f8095bf20` (6 plików testów: 70 passed, 1 skip oczekiwany), #125 `71c4e83bf` + hak build_world `4ee4f646a` (łatka nie wchodziła po tunelu 0211 — 3 hunki ręcznie; 88 passed, 1 skip), #122 `f06f372bd`. overrides C 190 / Dojlidy 47 wpisów, 0 duplikatów. Katalog regionów `--check` exit 0.
- Zestaw końcowy 16 plików na `f06f372bd`: **192 passed, 3 skipped, 0 failed** (48 s; skipy = brak przebudowy / tekstur w worktree).
- #123 potwierdzone blokady: `test_typology_0238.py:305` (`2022535` vs QA 1 986 314), baseline Dojlid sprzed #122, konflikt `buildings_mesh.py:storey_plan` (merge-tree na tej gałęzi).
- Skrypty etapu 2 w `artifacts/c-regen2-s23/tools/` (00-prep, 10-before, 20-regen, 30-budget.py, 40-unity, 50-pytest, 60-postmerge, 70-ab, vqa, _common) — składnia sprawdzona parserem, `30-budget.py` uruchomiony na obecnych danych (delty 0, czerwony na 3 brakach oczekiwanych przed przebudową). NIE uruchomione.
- Uwaga 3 dla lidera: derived/_Generated C w main (16:54/16:59) są starsze niż zacommitowane generated → „before” wymaga świeżej budowy (`10-before.ps1`, ok. 55 min) albo `-Mode Reuse` (rendery c-regen-s22/after).
- Raport: `docs/reports/INTEGRATION-2026-11-15-c-regen2-s23.md`.

ETAP 1 KONIEC — czekam na polecenie lidera.
NASTĘPNY KROK (etap 2, po zwolnieniu slotów): `Start-Process pwsh -WindowStyle Hidden -ArgumentList '-NoProfile','-File','C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\c-regen2-s23\artifacts\c-regen2-s23\tools\00-prep.ps1'` → potem 10-before → 20-regen → 40-unity → 50-pytest (statusy `artifacts/c-regen2-s23/<krok>/*.status`, czytać `exit=`)
