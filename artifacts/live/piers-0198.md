# piers-0198 (ADR 0198, podpory estakady A ronda Putry) — sesja w chmurze, bez Unity / Data/raw / build_world

- Gałąź `piers-0198` od origin/main `5724a161b`. Worktree w chmurze: /workspace/wt-piers-0198.
- Krok 1 (zrobione): `pier_lines_en` per pomost w `Data/Regions/bialystok-industrial-c/viaduct_underdeck.json`,
  odczyt w `hero_bridge.underdeck_rows`, wspólny keep-out `hero_bridge.keepout`, raport BLOCKED_COLS także dla underdeck,
  skrypt `tools/worldgen/qa/check_piers_vs_roads.py`, test `tests/gis/test_piers_vs_roads_0198.py`.
- Stacje (m od końca NW zakresu otwartego, WORKING_VALUE): NE 24,39 / 48,78 / 82,5 / 106,0 / 133,5 / 155,0 / 176,5 / 198,0
  (8 rzędów, max przęsło 33,7 m; było 48,8 i para 16,4). SW aktywne 19,5 / 40,0 / 56,5 / 135,5 / 161,5 / 187,5
  (max przęsło 79,0 m; było 94,8).
- KONFLIKT (SW): rzędy wyspowe 86,0 i 111,0 m są w `pier_lines_en_held` (nieczytane) — w wygenerowanym świecie krawędź
  wyspy ronda leży pod osią pomostu SW (62–133 m: jedna kolumna każdego rzędu na asfalcie pierścienia albo na pierścieniu
  najazdowym). Ortofoto GUGiK (WMS HighResolution, obejrzane 2026-11-15): prawdziwa wyspa sięga ok. 1,5–2,5 m poza
  południową krawędź pomostu SW. Jezdni nie ruszałem.
- Kontrola kolizji: `BLOCKED_COLS` pusty, każda kolumna ≥ 2,5 m od jezdni (`artifacts/piers-0198/piers_vs_roads.json/.txt`).
- Emulacja sprawdzona: z regułą przęseł (bez `pier_lines_en`) skrypt odtwarza rzędy ze scommitowanego spec co do 1 cm
  (NE 7 rzędów, 1 pominięty; SW 5 rzędów, 3 pominięte; przęsła 94,78 / 48,78 / 16,39).
- Dowody: `artifacts/piers-0198/ortho-overlay-rows.jpg` (rzędy na ortofoto; żółte = wyspa, pomarańczowe = krawędź
  asfaltu z generatora, niebieskie = krawędzie pomostów), `ortho-overlay-sw-island-conflict.jpg`.
  Ortofoto: Źródło danych: Główny Urząd Geodezji i Kartografii (www.geoportal.gov.pl), tylko referencja.
- Wycinków c027 / c022 (`research/_incoming/...`) NIE MA w repo (katalog poza gitem) — oparłem się na opisach w
  manifest.csv (P13-022, P13-027, P13-030, P13-031) i przeglądzie REVIEW-2026-11-14.

- Krok 2 (zrobione): opisy w overrides.yaml / gate3-segment.py / gate3_segment.json, ADR 0198 (PROPOSED).
- Testy: tests/gis/test_piers_vs_roads_0198.py 8 passed (104 s z underdeck + hero_bridge: 26 passed, 4 skipped);
  całe tests/gis: 1185 passed, 48 skipped, 3 xfailed, 1 failed = test_road_fidelity::test_report_not_stale
  (sha overrides.yaml + build_world.py; wymaga fidelity/run.py z Data/raw — lider).
- Raport: artifacts/piers-0198/PR-BODY.md.

KONIEC (chmura). NASTĘPNY KROK (lider, maszyna z Data/raw + Unity):
`uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c`
potem `uv run --project tools/worldgen python tools/worldgen/qa/check_piers_vs_roads.py`, fidelity/run.py, import-region,
visual-qa (putry-above, g3b_eye_s1582, g3b_eye_s1632, route-putry-approach, driver-andersa-to-putry; Low i High), EditMode.
