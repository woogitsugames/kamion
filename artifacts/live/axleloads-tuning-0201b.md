# axleloads-tuning-0201b (ADR 0201b) — live
Gałąź `axleloads-tuning-0201b` (baza: `truckdata-0201` = PR #77). Cel: naciski solo 73/27 % (S9 R3-013/014) + przestrojenie zawieszenia/kabiny bez luzowania tolerancji.
- 15.11: baseline runnera na gałęzi bazowej (R3, 8962caf66) → `artifacts/axleloads-0201b/r3-base/summary.md`: 135/135 PASS. Powtórzenie eksperymentu n1 (`exp-n1-repro/`) = te same 4 FAIL co w truckdata-0201.
- 15.11: kandydaci rozkładu mas A/B1/C (WIP, JSON w worktree) — analiza przyczyn 4 FAIL w toku.
- NASTĘPNY KROK: `bash` → `dotnet run -c Release --project tools/physics-runner/Runner -- --out artifacts/axleloads-0201b/<tag>` po każdej zmianie strojenia.
