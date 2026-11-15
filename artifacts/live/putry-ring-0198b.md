# putry-ring-0198b (ADR 0226, wyspa ronda Putry + 2 rzędy podpór pomostu SW) — sesja w chmurze, bez Unity / Data/raw / build_world

- Gałąź `putry-ring-0198b` od `origin/piers-0198` `51f89f4c0` (PR #82). Worktree w chmurze: /workspace/wt-putry-ring.
- Krok 1 (zrobione): pomiar wyspy na ortofoto GUGiK WMS HighResolution (0,05 m/px, 38 punktów krawężnika, ±0,3 m,
  WORKING_VALUE; plik nie jest w repo). OSM nie ma obrysu wyspy (4 drogi `junction=roundabout`).
- Krok 2 (zrobione): generator `apron_width` (krawędzie pierścienia, 0,2–4,0 m, domyślnie reguła 2,0 m) i
  `island_curb_radius` (węzeł, tylko narożnik wyspy); overrides regionu C: `putry-ring-island-kerb`
  (`apron: asphalt`, `apron_width: 0.4`), `putry-ring-s-placement` jako profil (oś 0,15–0,25 m / 6,0 m przy wyspie,
  2,9 m / 7,0 m od t 0,62 jak MA-010), `putry-ring-island-nw-corner` (R 10,0).
  Krawężnik wyspy vs ortofoto: średnio 2,02 → 0,46 m, max 4,93 → 1,37 m; pole wyspy 1388 → 1679 m².
- Krok 3 (zrobione): pomost SW — rzędy 89,0 i 109,0 m w `pier_lines_en` (86,0 / 111,0 stały 1,65 / 1,94 m od asfaltu,
  ale w keep-out generatora ok. 2,5 m; wolne okno 88–110 m). `pier_lines_en_held` usunięte.
  Przęsła SW 19,5 / 20,5 / 16,5 / 32,5 / 20,0 / 26,5 / 26,0 / 26,0 / 25,8 m — **max 32,5 m** (było 79,0). NE bez zmian (33,7).
  `check_piers_vs_roads.py`: rc 0, `BLOCKED_COLS` pusty, każda kolumna ≥ 2,53 m od jezdni
  (`artifacts/putry-ring-0198b/piers_vs_roads.txt/.json`).
- Krok 4 (testy): patrz `artifacts/putry-ring-0198b/PR-BODY.md`.
- Krok 5 (zrobione): ADR 0226 (PROPOSED, numer do potwierdzenia), runda 2 w ADR 0198, `docs/WORLD_GENERATION.md`.
- Dowody: `artifacts/putry-ring-0198b/ortho-overlay-island.jpg`, `ortho-overlay-sw-deck-rows.jpg`.
  Ortofoto: Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl), tylko referencja.

KONIEC (chmura). NASTĘPNY KROK (lider, maszyna z Data/raw + Unity):
`uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c`
potem `check_piers_vs_roads.py`, `fidelity/run.py`, import-region, visual-qa (putry-above, g3b_eye_s1582,
g3b_eye_s1632, route-putry-approach, driver-andersa-to-putry; Low i High), kadr MA-010 `au_r_s1160`, EditMode.
