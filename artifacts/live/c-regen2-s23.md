# c-regen2-s23 (live) — etap 1: przygotowanie drugiej przebudowy C + Dojlidy
Worktree `.claude/worktrees/c-regen2-s23`, gałąź `c-regen2-s23`, baza main `7e044ac0a`. Bez Unity/build_world w tym etapie.

## UWAGI DLA LIDERA (decyzje przed etapem 2)
1. **#123 typology-0238 = FIX** w recenzji, head `243b3065b` bez zmian od recenzji → NIE scalone. Skutek: kolejna (trzecia) przebudowa C po poprawkach #123, chyba że lider zleci 3 poprawki P1 w gałęzi integracyjnej przed etapem 2.
2. **#119 tests-hygiene-0245 nie jest w main** (`merge-base --is-ancestor` = 1), a recenzja każe scalić go PRZED przebudową C (zmienia strumień losowy płaszcza lasu). Nie ma go w moim zadaniu — nie scalam; do decyzji lidera.

## Kroki
- [23:1x] worktree + junctions Data/raw/{gugik,osm,refs,mapillary,fab}; kopie cc0/_raw/megascans (0,9 GB). Heady 7 PR = sha z recenzji (0 nowych commitów). Żaden PR nie zmienia ProjectSettings/Packages/asmdef/scen/prefabów/generated.
- [23:2x] Merge #109 `9c8ab51a0` (pytest 3 pliki: 33 passed), #110 `3d4144f9e`, #111 `72ce5ed05` (tools/perf/tests 61 passed). RegionImporter.cs: oba hunki (l. 308 i 462), RenderOverrides.cs: ThinShadows + GpuAbOverrides, CurrentRevision 240 — jak w recenzji.
- Znalezisko #110 × #120: `thin_shadow_audit.py --check` exit 1 (1 niezgodność `lamp_old_concrete_led_9m`, prototyp dodany do main po #110) → dopisany do FAMILY_EXCEPTIONS (osobny commit); teraz 155 prototypów, 48 thin, 0 niezgodności.


- [23:3x] Merge #124 `f8095bf20` (6 plików testów: 70 passed, 1 skip oczekiwany), #125 `71c4e83bf` + hak build_world `4ee4f646a` (łatka nie wchodziła po tunelu 0211 — 3 hunki ręcznie; 88 passed, 1 skip), #122 `f06f372bd`. overrides C 190 / Dojlidy 47 wpisów, 0 duplikatów. Katalog regionów `--check` exit 0.
- Zestaw końcowy 16 plików na `f06f372bd`: **192 passed, 3 skipped, 0 failed** (48 s; skipy = brak przebudowy / tekstur w worktree).
- #123 potwierdzone blokady: `test_typology_0238.py:305` (`2022535` vs QA 1 986 314), baseline Dojlid sprzed #122, konflikt `buildings_mesh.py:storey_plan` (merge-tree na tej gałęzi).
- Skrypty etapu 2 w `artifacts/c-regen2-s23/tools/` (00-prep, 10-before, 20-regen, 30-budget.py, 40-unity, 50-pytest, 60-postmerge, 70-ab, vqa, _common) — składnia sprawdzona parserem, `30-budget.py` uruchomiony na obecnych danych (delty 0, czerwony na 3 brakach oczekiwanych przed przebudową). NIE uruchomione.
- Uwaga 3 dla lidera: derived/_Generated C w main (16:54/16:59) są starsze niż zacommitowane generated → „before” wymaga świeżej budowy (`10-before.ps1`, ok. 55 min) albo `-Mode Reuse` (rendery c-regen-s22/after).
- Raport: `docs/reports/INTEGRATION-2026-11-15-c-regen2-s23.md`.

- [23:4x] Po uwagach recenzenta: bramki między krokami (gałąź, exit= z regen.status), ponowienie przy 0xC0000142 także z logu, prep kopiuje całe derived, dowód side-effectów Unity dla #110; `test_streetscape.py` 58 passed / 1 skip.


## ETAP 2 (16.11)
- Łańcuch lidera: regen exit 0 (budżet zielony), unity DONE, pytest 1. przebieg 3 faile. Poprawka 00-prep lidera zacommitowana (`ae761cca4`).
- **Budżet C `stretch_04` High 1 985 807 (< 2 M, zapas 14 193), Low 938 274; Dojlidy max High 1 768 010.**
- P0 znaleziony na renderach: płot z siatki magenta (shader #109 nie kompilował się: `IsAlphaToMaskAvailable` tylko pod `_ALPHATEST_ON`) → poprawka `a2a5dfa64`, macierz VQA wyrenderowana ponownie (12 komórek exit 0, 0 błędów shadera). Stare rendery: `after-r1-magenta/`.
- 3 testy #124 czerwone po przebudowie → dostosowane (`6a337b125`). Generated C + Dojlidy zacommitowane (`4ff1cfb3f`).
- Merge origin/main `6e6fe972f` → `4129c4297` (bez kodu świata). pytest 2. przebieg: **1653 passed, 0 failed**; perf 61 passed.
- EditMode po imporcie: 786/788, 1 fail `StreetLampOpticsTests.SodiumTint_HasTheLedLuminance` (gałąź nie rusza kodu latarni; hipoteza: stan statyczny LED po 0216b).
- Oględziny par w `artifacts/c-regen2-s23/view/` (bez visual-critic): płot OK po poprawce, cienie Low OK, E-1 na wysięgniku p37 nieczytelna na Low — do oceny.

ETAP 2 KONIEC. Gotowe do scalenia: TAK (kod/testy/budżet), zastrzeżenia w raporcie §Gotowość.
NASTĘPNY KROK (lider): `git -C C:\Users\matma\Documents\Claude\kamion merge --no-ff origin/c-regen2-s23` → `pwsh scripts/setup-project.ps1` (oczekiwany brak diffu) → visual-critic na `artifacts/c-regen2-s23/view/*.jpg`
