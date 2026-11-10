# STATUS — Kwadrat Park r11 (gałąź worktree-kwadrat-r11, worktree .claude/worktrees/kwadrat-r11)

## 2026-11-10 (start)
- Przeczytane: AGENT-RULES, CLAUDE.md, REVIEW-2026-11-10-0071-0080, ADR 0071.
- DIAGNOZA P0 (kostka 0,4-0,5 m): źródło GLOBALNE, nie 0071. `WorldPbrMaterials.Create` nigdy nie zapisuje `_Tile`
  (komentarz ADR 0067), więc każdy zestaw jest próbkowany co 4 m. Zestaw `behaton_i_grey` ze skanu CC0 (ADR 0063) to
  1,92 x 1,92 m i 106 kostek (spec: `source.elements_per_tile`) = 0,0348 m2/kostkę (rzeczywista ok. 0,033) -> przy 4 m
  kostka wychodzi 4/1,92 = 2,08x za duża (0,2 m -> 0,42 m). Rendery 0080 miały drobną kostkę, bo w tamtym worktree
  (i na dysku main: PNG z 16:50) leżały stare tekstury PROCEDURALNE (20 kostek na 4 m), niezgodne ze spec w gicie.
- Zrobione: commit 61ad878 importer (`_Tile` dla zestawów z `elements_per_tile`, ściany `weather`, dekale `band`, `cracks`).
- Tekstury PBR zbudowane ze skanów (446 s, `logs/build_all_base.log`), spec bez zmian.
- W toku: baseline (kod main: stash zmian Pythona + C# z ad9760d) build_world -> import -> rendery "before".
- NASTĘPNY KROK: po baseline `git stash pop; git checkout 61ad878 -- game/Assets/_Project/World/Import`

## 23:40 — baseline gotowy, after1 w toku
- Baseline (kod main, tekstury ze skanów): `before/{Medium-overcast,Medium-clear,Low-overcast}` (8 kamer, PNG + JPG 960), `logs/build_world_base.log`,
  pytest gis baseline: 223 zielone / 7 czerwonych (`logs/pytest_gis_base.log`; 2 moje nowe testy czerwone na starym świecie, reszta = znane z main + 2 do sprawdzenia:
  `test_life_prototypes_budget_and_lods`, `test_every_vehicle_has_a_spec_and_others_none` — skutki moich zmian prototypów, do poprawy).
- Kod r11: yard_wear.py (ślady, łaty, olej, brud krawędzi), authored dock_trailers, detal naczep, wyspa szlabanu + pętle + słupki, UV1 zacieków hali, płyta `yard_concrete_worn`.
- UWAGA: pytest gis zapisuje `generated/streetscape_qa.json` / `world_manifest.json` i przebudowuje GLB hali — po testach zawsze pełny build_world.
- NASTĘPNY KROK: `pwsh artifacts/kwadrat-r11/cycle.ps1 -Phase after1 -Combos Medium-overcast` (w toku) -> obejrzeć -> iteracja.

## 00:20 — iteracja 3 obejrzana, final chain w toku
- after1 (obejrzane): kostka OK (~0,2 m), ale łata jasna = biała plama, ślady za mocne, słupek na krawędzi wyspy, łata asfaltu pod pętlą.
- after3 (obejrzane, Medium-overcast/clear, Low-overcast): łaty +7 %/-10 %, ślady 0,35-0,85, słupki w osi wyspy, bez łaty asfaltu przy szlabanie,
  naczepy ≤ 1188 tris LOD0 (budżet testu 1200), bez nowych submeshów poza filmem brudu na LOD0, brud krawędzi = pasy decal_tyre.
- pytest gis after3: 227 zielone / 3 czerwone = te same co baseline z main (fidelity stale, 2x korytarz trasy s≈1434–1480, chunk_2_4) — `logs/pytest_gis_after3.log`.
- Budżet Low (stats.txt, 8 kamer, before -> after3): draws 6170 -> 6218 (+0,8 %), tris 2092k -> 2127k (+1,7 %); +10 % tris w kamerze bramy =
  2 słupki w warstwie furniture rozciągnęły bounds meshu furniture chunku 6_6 (19 k tris) na kadr bramy -> słupki przeniesione do warstwy paved.
- W toku: `pwsh artifacts/kwadrat-r11/final.ps1` (build_world -> import -> after/{Medium-overcast,Medium-clear,Low-overcast} -> PlayMode barrier -> EditMode), log `logs/final.log`.
- NASTĘPNY KROK: `uv run --project tools/worldgen python artifacts/kwadrat-r11/budget.py artifacts/kwadrat-r11/before/Low-overcast artifacts/kwadrat-r11/after/Low-overcast`;
  obejrzeć after/*; montaż before/after; ADR liczby; kopia do main/artifacts/kwadrat-r11.

## 00:35 (11.11) — r11 ZAKOŃCZONE
- Final: `after/{Medium-overcast,Medium-clear,Low-overcast}` (8 kamer), `compare/*.jpg` (before nad after), `budget_low.txt`.
- Budżet Low (8 kamer, stats.txt): draws 6170 -> 6214 (+0,7 %), tris 2092k -> 2108k (+0,8 %); najgorsza kamera +1,3 % draws (brama).
- Testy: pytest gis 227/3 (te same 3 czerwone co baseline main: fidelity stale, 2x korytarz trasy s≈1434–1480); PlayMode
  `WorldCBarrierTests|DepotBarrierTests` 4/4 (0 kontaktów, max |dv| 0,050 m/s — wyspa nie jest dotykana); EditMode 176 zielone / 0 czerwonych /
  5 inconclusive (prefab ciężarówki nie generowany w worktree) / 7 skip.
- Efekty uboczne Unity cofnięte (M_Sky, ProjectSettings, LP_Clear/LP_Dusk/LP_LowSun — serializacja presetów światła, NIE commitowane).
- OTWARTE: visual-critic (lider); zrzuty z telefonu; A8 (wieżowiec, klosz lampy); tablica przy bramie (brak źródła);
  `_Tile` nadal 4 m dla zestawów bez `elements_per_tile` (concrete_cast 10 m, kerb 2x0,5, sandwich 6 m, brick 1,4 m...) — decyzja lidera;
  tekstury PBR na dysku main są STARE (proceduralne, sprzed skanów CC0) — po scaleniu: build_all.py (import-region zrobi to sam tylko gdy brakuje plików / _src nowsze).
- NASTĘPNY KROK (lider): scalić `worktree-kwadrat-r11`; na main:
    uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py
    $env:KAMION_BLENDER='C:\Users\matma\AppData\Local\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe'; uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c
    pwsh scripts/import-region.ps1 -Region bialystok-industrial-c
    pwsh scripts/test.ps1 -Platform PlayMode -Filter "WorldCBarrierTests|DepotBarrierTests"
