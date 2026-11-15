# Knyszyn Rynek 0227

- 2026-11-15 18:02 +01:00 — Utworzono worktree z origin/main; scalono origin/summer-led-0216 bez konfliktów.
- NASTĘPNY KROK: `git push -u origin knyszyn-rynek-0227`
- 2026-11-15 18:04 +01:00 — Obejrzano zdjęcia dzienne; fontanna ma dysze w posadzce, kostka układana łukami. Kopiowanie danych i Library trwa; źródła tylko do odczytu przez junction, derived lokalny.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/copy.done; pwsh scripts/import-region.ps1 -Region knyszyn`
- 2026-11-15 18:05 +01:00 — Wstępna tabela referencji zapisana w artifacts/knyszyn-rynek-0227/AUDYT.md; wykryta rozbieżność wymiaru fontanny K1 vs istniejący override. Baseline nadal oczekuje na kopię Library.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/copy.done; pwsh scripts/unity-slot.ps1 -Acquire -Owner knyszyn-rynek-0227`
- 2026-11-15 18:06 +01:00 — Lokalna kopia danych i Library gotowa; import przygotowawczy w toku. Skopiowane GLB mogą być starsze niż scalony LED — przed baseline przebudować knyszyn i ponownie zaimportować.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/import-before.done; pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner knyszyn-rynek-0227`
