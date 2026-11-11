# STATUS — 0096 worldgen determinism (gałąź worktree-determinism, z main 0889cae1)

## Krok 1 — dwa przebiegi build_world w tym samym worktree (ten sam kod, te same wejścia)
- run1 == stan c6588194 (1526 stanowisk), run2 == stan 95f49598 (1500): 5 plików generated/*.json różne, GLB różne
  (`run1/*.sha256`, `run2/*.sha256`, `run1_vs_run2_generated.diff`). Niedeterminizm potwierdzony.

## Krok 2 — źródło
- Etap dróg (`roads.pipeline.build`) pod PYTHONHASHSEED 0..9 dawał 3 różne siatki (`probe_seed*.json`):
  56ee… (seed 0,1,2,3,8), 2aea… (4,5,6,7), 0b6f… (9). Różnice: paski naroży skrzyżowań `j:*:cornerN` i `c:w537184112:…:R`
  raz `curb_concrete`, raz `sidewalk_paving`.
- Przyczyna: `tools/worldgen/roads/meshing.py` `_emit_strip`: `mat = max(set(mats), key=mats.count)` — remis rozstrzygany
  kolejnością iteracji zbioru stringów = losowy hash str na proces.

## Krok 3 — poprawka + dowód
- `meshing.py`: `max(dict.fromkeys(mats), key=mats.count)` (remis -> materiał pierwszy wzdłuż paska). `consistency.py`: 2x `sorted(...)`.
- Etap dróg seed 0/4/9 po poprawce: jeden hash 81ae1c30… (12166 części).
- Pełny build_world PYTHONHASHSEED=4 i =9: 202 pliki derived + 27 Regions + art-source identyczne
  (`fix_run_seed4/*.sha256` == `fix_run_seed9/*.sha256`). Liczby: `numbers_before_after.txt` (1526 stanowisk, 908 aut, kerb_tris 84 731).
- Testy: `tests/gis/test_determinism.py`, sonda `tools/worldgen/qa/determinism.py`.

NASTĘPNY KROK: sprawdzenie izolacji Fab (robocopy megascans z main, build z Fab vs fallback), potem
`uv run --project tools/worldgen python -m pytest tests/gis -q`
