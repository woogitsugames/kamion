# STATUS pc-budget-s23
- DONE 17.11: 66/66 przebiegów, analiza (tools/pcperf/sweep/analyze.py), raport docs/reports/PC-BUDGET-2026-11-16.md, tileBudgetsD83 w pc-budgets.json, sekcja w docs/PERFORMANCE_BUDGETS.md.
- Następny krok: powtórka na nowym buildzie: `pwsh -File tools/pcperf/sweep/run.ps1 -Exe <nowy Kamion.exe>` (najpierw przenieś stare artifacts/pc-budget-s23/runs), potem `uv run --no-project --with numpy python tools/pcperf/sweep/analyze.py C:\Users\matma\Documents\Claude\kamion\artifacts\pc-budget-s23`.
