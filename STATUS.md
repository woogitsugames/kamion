# STATUS dk8-s8-s24 (ADR 0292, kafel dk8-s8-jeroniki)

- 18.11: worktree, skrypt kroków tools/worldgen/qa/dk8_s8_s24.ps1. Analiza dk65-01: z trasy (Szosa Knyszyńska) osiągalna Warszawska na szwie S (769448,5); S8 W (305447699) na szwie 769340,8 tylko z jeroniki.
- NASTĘPNY KROK: `pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase ingest` (exit w artifacts/dk8-s8-s24/run/ingest-dk8-s8-jeroniki-r1.exit)

- ingest exit=0 (NMT 2025 4 arkusze, orto 2024 0,25 m, 318 MB). NASTĘPNY KROK: `pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase world -Context`
- jeroniki: S8 W na szwie z dk65-01 osiągalne TYLKO z DK8 W od szwu z bialystok-porosly (Warszawska bez wjazdu na DK8 W; inne ścieżki = przejazd w pasie dzielącym access=no). Buduję też bialystok-porosly (ingest exit=0). Linki knyszynska-kleeberga-s, porosly-dk8-w, jeroniki-dk8-to-s8 + korytarz bialystok-s8 w route_links.yaml.
- NASTĘPNY KROK: czekaj na artifacts/dk8-s8-s24/run/route-dk8-s8-jeroniki-r2.exit; potem `pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase world -Context -Tiles bialystok-porosly -Tag r2`
