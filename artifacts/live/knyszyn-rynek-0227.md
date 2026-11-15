# Knyszyn Rynek 0227

- 2026-11-15 18:02 +01:00 — Utworzono worktree z origin/main; scalono origin/summer-led-0216 bez konfliktów.
- NASTĘPNY KROK: `git push -u origin knyszyn-rynek-0227`
- 2026-11-15 18:04 +01:00 — Obejrzano zdjęcia dzienne; fontanna ma dysze w posadzce, kostka układana łukami. Kopiowanie danych i Library trwa; źródła tylko do odczytu przez junction, derived lokalny.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/copy.done; pwsh scripts/import-region.ps1 -Region knyszyn`
- 2026-11-15 18:05 +01:00 — Wstępna tabela referencji zapisana w artifacts/knyszyn-rynek-0227/AUDYT.md; wykryta rozbieżność wymiaru fontanny K1 vs istniejący override. Baseline nadal oczekuje na kopię Library.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/copy.done; pwsh scripts/unity-slot.ps1 -Acquire -Owner knyszyn-rynek-0227`
- 2026-11-15 18:06 +01:00 — Lokalna kopia danych i Library gotowa; import przygotowawczy w toku. Skopiowane GLB mogą być starsze niż scalony LED — przed baseline przebudować knyszyn i ponownie zaimportować.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/import-before.done; pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner knyszyn-rynek-0227`
- 2026-11-15 18:07 +01:00 — Przygotowano i uruchomiono sekwencyjny baseline: po imporcie przygotowawczym build_world, ponowny import oraz Low/High × clear/dusk; status w baseline.done, log baseline.log.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/baseline.done; Get-Content artifacts/knyszyn-rynek-0227/baseline.log -Tail 30`
- 2026-11-15 18:09 +01:00 — Audyt kodu: kolejność authored paved_area prawdopodobnie usuwa płytę fontanny pod placem; weryfikacja na baseline oczekuje na render. Import nadal buduje brakujące materiały.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/baseline.done; Get-Content artifacts/knyszyn-rynek-0227/import-before.log -Tail 20`
- 2026-11-15 18:14 +01:00 — Przerwano własną regenerację materiałów przed Unity, skopiowano gotowe PNG z main po sprawdzeniu identyczności źródeł generatora; wznowiono import i baseline.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/baseline.done; Get-Content artifacts/knyszyn-rynek-0227/baseline2.log -Tail 30`
- 2026-11-15 18:16 +01:00 — Import przygotowawczy OK (64 chunków, Low+High); build_world oczekuje w kolejce heavy. Cofnięto efekt uboczny M_Sky.mat.
- NASTĘPNY KROK: `Get-Content artifacts/knyszyn-rynek-0227/baseline2.log -Tail 30; Get-Content artifacts/knyszyn-rynek-0227/baseline.done`
