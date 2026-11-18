# STATUS dk8-s8-s24 (ADR 0292, kafel dk8-s8-jeroniki)

- 18.11: worktree, skrypt kroków tools/worldgen/qa/dk8_s8_s24.ps1. Analiza dk65-01: z trasy (Szosa Knyszyńska) osiągalna Warszawska na szwie S (769448,5); S8 W (305447699) na szwie 769340,8 tylko z jeroniki.
- NASTĘPNY KROK: `pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase ingest` (exit w artifacts/dk8-s8-s24/run/ingest-dk8-s8-jeroniki-r1.exit)

- ingest exit=0 (NMT 2025 4 arkusze, orto 2024 0,25 m, 318 MB). NASTĘPNY KROK: `pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase world -Context`
- jeroniki: S8 W na szwie z dk65-01 osiągalne TYLKO z DK8 W od szwu z bialystok-porosly (Warszawska bez wjazdu na DK8 W; inne ścieżki = przejazd w pasie dzielącym access=no). Buduję też bialystok-porosly (ingest exit=0). Linki knyszynska-kleeberga-s, porosly-dk8-w, jeroniki-dk8-to-s8 + korytarz bialystok-s8 w route_links.yaml.
- NASTĘPNY KROK: czekaj na artifacts/dk8-s8-s24/run/route-dk8-s8-jeroniki-r2.exit; potem `pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase world -Context -Tiles bialystok-porosly -Tag r2`
- jeroniki r2: build_world exit=0, trasa 1586 m; dziura 15 m w DK8 obu jezdniach od tunelu 221522232 (obstacle_in_lane 90) -> graph_filter.authored.json (jak s8-04). DK8 orto: asfalt p50 8,55 m (26 stacji), generator 8,0 m. NASTĘPNY KROK: `pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase world -Context -Tag r3`
- porosly r2: build_world exit=0, trasa 1590 m (road_consistency 96, poza DK8 głównymi: łącznice/wiadukty). jeroniki r3 w toku (graph_filter). NASTĘPNY KROK: `pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase unity -Tiles bialystok-porosly -Tag r2`
- porosly import r2b: FAIL (nakładające się zapory krawędzi: service 222465086 x residential 40329438, 2,7 m, szew N) -> graph_filter porosly. NASTĘPNY KROK: `pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase world -Context -Tiles bialystok-porosly -Tag r3`, potem unity.
- jeroniki r4: road_consistency na trasie 0; import Win64 exit=0, WORLD_MEMORY Low 94,2 / High 217,4 MB; VQA High 43 PNG obejrzane (vqa-r4). Porosly r3 world w toku. NASTĘPNY KROK: po route-bialystok-porosly-r3.exit -> `-Phase unity -Tiles bialystok-porosly -Tag r3`, potem `-Phase post`.
