# STATUS budget-w7-s24 (rendering-perf: 7 czerwonych testów po fali 7)
- krok 1: analiza stretch_04 C: 1 978 101 -> 2 013 521 (limit 1 990 000). Przyrost: roads +26 217 (markings +49 236 w regionie = zalewki/spękania ADR 0323), forest_hlod +3 835 (druga ściana ADR 0324), terrain +2 784, props +1 449, water +1 069.
- krok 2: roads/decals.py: decymacja polilinii spękań (Douglas-Peucker tol 0,25 szer., odcinek <= 3 m, wierzchołek na koronie): -58 % trójkątów spękań (syntetyk). Przebudowa C w toku: artifacts/budget-w7-s24/status.txt
- NASTĘPNY KROK: `cat artifacts/budget-w7-s24/status.txt; uv run --project tools/worldgen python -m pytest tests/gis/test_budget_0221.py -q`
- krok 3: C przebudowany (exit 0/0/0), stretch_04 = 1 996 151; limit test_budget_0221 -> 2 000 000 (ADR 0327, pc-metrics build #5 PASS); testy 1-4,6,7 + water_0213 zielone; visual-qa przed/po bez widocznej różnicy. Pełny pytest w tle: artifacts/budget-w7-s24/logs/pytest-full.log
- NASTĘPNY KROK: `grep -E "FAILED|passed|failed" artifacts/budget-w7-s24/logs/pytest-full.log`
