# STATUS gate3-signs (ADR 0125)

## 1. Worktree + baseline (2026-11-11)
Worktree `.claude/worktrees/gate3-signs` (gałąź `gate3-signs` z main ce3f1a77), dane skopiowane, junctiony Data/raw/{gugik,osm,refs,mapillary,fab}.
Baseline Low-overcast: 40 par SBS w `artifacts/gate3-signs/baseline/` (rendery + stats-*.txt + sheets).
Triangulacja bramownicy G3-B: ortofoto 2024 + Mapillary richlv 2020 (468708117568850 / 143559297695026), grobin 2019, kino 2024 -> portal przy E,N = (-261,-208) +-3 m; w świecie stał w (-306.8,-171.3), czyli 59 m za daleko. Kadr 3281350 pokazuje TĘ SAMĄ bramownicę od tyłu (GPS zsolt przesunięty ~45 m) - błąd pozy, nie brak obiektu.
Ekran i słup WN w 3678296 ISTNIEJĄ w renderze (słabo widoczne na Low-overcast): poprawka = czytelność, nie strona.
NASTĘPNY KROK: `uv run --project tools/worldgen pytest tests/gis/test_gate3_landmarks.py -q` (po napisaniu modułu streetscape/gate3_landmarks.py)

## 2. Generator (kod + dane)
Nowy moduł `tools/worldgen/streetscape/gate3_landmarks.py` (kind: gate3_sign; 1 prototyp = 1 materiał = 1 draw), haki: 1 linia w props.build_all, 1 wywołanie w stage.run. overrides.yaml: portal Andersa distance_m 40 -> 99, 7 znaków gate3_sign, wiadukt Putry screen_side: travel_right, pas pełny ekranu 1.0 -> 1.8 m (strefy 4-6). meshing.screen_sides + szyna pośrednia ekranu przeszklonego. Testy: tests/gis/test_gate3_landmarks.py 8 passed, 2 skipped (QA po przebudowie).
NASTĘPNY KROK: `pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner claude-gate3-signs; uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c; pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner claude-gate3-signs`
