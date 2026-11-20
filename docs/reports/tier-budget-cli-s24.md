# tier-budget-cli — raport s24, 2026-11-19

- Wynik: wdrożone i zacommitowane na `tier-budget-cli`; bez push. Implementacja: `15b2981e7`.
- Przyczyna: D89 podniosła tylko Low 640→850 i High 1450→2000 MB; Medium zostało 800, Ultra 2000 (ADR 0273/0290).
- Drabinka PC: **850 ≤ 850 ≤ 2000 ≤ 2000 MB (WORKING_VALUE)**; tylko Medium +50 MB, wspólna treść Low z tierem Low.
- Pochodzenie wszystkich progów i odrzucone warianty: `docs/adr/0309-spojne-budzety-pamieci-streamingu-pc.md`; HANDOVER: ostatni 0308, zlecony 0309.
- Runtime: `StreamingPolicy.cs`; wybór treści pobiera limit z tej metody. `PcTierTable`/assety URP nie przechowują tego budżetu.
- JSON pcperf dostał osobną tabelę `streamingWorldMemory`; istniejące limity procesu/VRAM/geometrii mają inne znaczenie. Tabela docs/03 i dopisek D89 zaktualizowane.
- pytest: `uv run --no-project --with pytest python -m pytest tools/pcperf -q` → **55 passed in 5.22s** (w tym zgodność JSON/C# i monotoniczność). `git diff --check` bez błędów.
- EditMode: aktualizacja oczekiwań w `StreamingContentChoiceTests`, `WorldStreamingPolicyTests`; monotoniczność PC/telefon i regresja 825 MB na Low/Medium przy wyłączonym `allowOneOverBudget`.
- Napisane i sprawdzone statycznie; **Unity, EditMode i buildów nie uruchamiano** zgodnie ze zleceniem. Brak nowego pomiaru RAM/VRAM/FPS; pomiary cytowane w ADR są historyczne.
- `ProjectSettings/`, Packages, asmdef i HANDOVER bez zmian; poprawka nie wymaga zmian ustawień ani reimportu. Wszystkie zapisy wyłącznie w tym worktree.
- Otwarte: niezależny review lidera, wykonanie EditMode i przejazd Medium z telemetrią w osobnej sesji. Parser pcperf nie sprawdza WORLD_MEMORY (brak tego licznika w CSV).
- Integracja przez lidera: `git merge tier-budget-cli`, następnie (po dopuszczeniu Unity) `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64`.
