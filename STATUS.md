# STATUS dk8-s8-s24 (ADR 0292, kafel dk8-s8-jeroniki)

- 18.11: worktree, skrypt kroków tools/worldgen/qa/dk8_s8_s24.ps1. Analiza dk65-01: z trasy (Szosa Knyszyńska) osiągalna Warszawska na szwie S (769448,5); S8 W (305447699) na szwie 769340,8 tylko z jeroniki.
- NASTĘPNY KROK: `pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase ingest` (exit w artifacts/dk8-s8-s24/run/ingest-dk8-s8-jeroniki-r1.exit)

- ingest exit=0 (NMT 2025 4 arkusze, orto 2024 0,25 m, 318 MB). NASTĘPNY KROK: `pwsh -File tools/worldgen/qa/dk8_s8_s24.ps1 -Phase world -Context`
