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
