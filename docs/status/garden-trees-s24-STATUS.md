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

## Krok 2 (27.11) — testy, render „przed”, build
- Testy: `tests/gis/test_small_trees_0352.py` 4/4 (budżet ≤ +50 %, 3 formy, brak rdzenia, spód kart); poprawione nieaktualne
  asercje `test_house_greenery_0163` / `test_horizon_0170` (na main 9ec10a5a2 już czerwone po ADR 0352: skirt, 34 → 28).
  Pełny zestaw roślinność / plot_kit / budynki r7–r9 / 0348 / 0316: 83 passed + te 2 (teraz zielone).
- Render „przed”: `artifacts/garden-trees-s24/before/knyszyn-w/High-{clear,overcast}/` (5 kamer kontrolnych + 6 ogrodowych
  `garden_cams.json`, format gate3; import = stan main skopiowany z a492).
- knyszyn-w: 213 małych liściastych (164 „near” = pełna bryła na High), 156 owocowych (121 „near”).
- `build_world.py --region knyszyn-w` 481 s, exit 0 (prywatny derived). `import-region.ps1` woła `uv run` → Smart App Control;
  obejście: `artifacts/garden-trees-s24/shim/uv.cmd` (przekierowanie na interpreter a492) dopisany do PATH w `vqa.ps1`.

NASTĘPNY KROK: `pwsh artifacts/garden-trees-s24/build.ps1; pwsh artifacts/garden-trees-s24/vqa.ps1 -Label after-r1` (w toku),
potem pary przed|po i poprawki bryły.
