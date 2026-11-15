# c-regen2-s23 (live) — etap 1: przygotowanie drugiej przebudowy C + Dojlidy
Worktree `.claude/worktrees/c-regen2-s23`, gałąź `c-regen2-s23`, baza main `7e044ac0a`. Bez Unity/build_world w tym etapie.

## UWAGI DLA LIDERA (decyzje przed etapem 2)
1. **#123 typology-0238 = FIX** w recenzji, head `243b3065b` bez zmian od recenzji → NIE scalone. Skutek: kolejna (trzecia) przebudowa C po poprawkach #123, chyba że lider zleci 3 poprawki P1 w gałęzi integracyjnej przed etapem 2.
2. **#119 tests-hygiene-0245 nie jest w main** (`merge-base --is-ancestor` = 1), a recenzja każe scalić go PRZED przebudową C (zmienia strumień losowy płaszcza lasu). Nie ma go w moim zadaniu — nie scalam; do decyzji lidera.

## Kroki
- [23:4x] worktree + junctions Data/raw/{gugik,osm,refs,mapillary,fab}; kopie cc0/_raw/megascans (0,9 GB). Heady 7 PR = sha z recenzji (0 nowych commitów). Żaden PR nie zmienia ProjectSettings/Packages/asmdef/scen/prefabów/generated.
- [23:5x] Merge #109 `9c8ab51a0` (pytest 3 pliki: 33 passed), #110 `3d4144f9e`, #111 `72ce5ed05` (tools/perf/tests 61 passed). RegionImporter.cs: oba hunki (l. 308 i 462), RenderOverrides.cs: ThinShadows + GpuAbOverrides, CurrentRevision 240 — jak w recenzji.
- Znalezisko #110 × #120: `thin_shadow_audit.py --check` exit 1 (1 niezgodność `lamp_old_concrete_led_9m`, prototyp dodany do main po #110) → dopisany do FAMILY_EXCEPTIONS (osobny commit); teraz 155 prototypów, 48 thin, 0 niezgodności.

NASTĘPNY KROK: `git -C .claude/worktrees/c-regen2-s23 merge --no-ff --no-commit origin/signs-c-0236` (potem #125 + łatka haka, #122)
