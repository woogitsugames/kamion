# garden-trees-s24 — STATUS (dopisek do ADR 0352)

Gałąź `worktree-agent-a2b12b7efe07eff87`, worktree `.claude/worktrees/agent-a2b12b7efe07eff87`.
`Data/raw/derived` = PRYWATNA kopia tylko `knyszyn-w` + `cache` (skopiowana z worktree a492…, nie junction; main nietknięty).
Python: `C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\agent-a492e5af856a32ed3\tools\worldgen\.venv\Scripts\python.exe`, `PYTHONPATH` = ten worktree.

## Krok 1 (27.11) — prototyp bryły, podgląd offline
- `tools/worldgen/streetscape/small_trees.py`: `young_tree` (liściaste < 6,5 m: pień 3-ścienny, 3 dolne + 3 górne płaty
  korony na konarach, 20–21 trójkątów; było 14) i `orchard_tree` (owocowe: pień, 3–4 konary, kępy, bez `_core`,
  40 / 50 trójkątów; było 46). Normalne sferyczne od środka korony, karty skręcone (2 trójkąty w różnych płaszczyznach).
- `plot_kit._crown_hw`: zaokrąglony spód kart koron (`_UNDER` 0,07 zamiast 0,30 / 0,34 — płaskie cięcie spodu „lizaka”).
- `plots.fruit_tree` i `plantings.garden_tree` (pełny wariant, H < 6,5 m) wołają nowe bryły; warianty lite bez zmian.
- Podgląd: `artifacts/garden-trees-s24/preview/{old,young,fruit}_*.jpg` (rasteryzator `preview_kit`, bez cieni).

NASTĘPNY KROK: testy (`& <python> -m pytest tests/gis/test_house_greenery_0163.py tests/gis/test_horizon_0170.py tests/gis/test_trees_0352.py tests/gis/test_buildings_r9.py -q`),
potem render „przed” (visual-qa na skopiowanym imporcie), `build_world.py --region knyszyn-w`, import Win64, render „po”.
