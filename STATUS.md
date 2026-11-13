# STATUS region-0166 (ADR 0166 Dojlidy/Krywlany — przygotowanie danych)

Stan: przerwane na limicie 5 h zaraz po starcie. Zrobione: worktree `.claude/worktrees/region-0166`, gałąź `region-0166` z origin/main (17c294976). Nic więcej — brak konfiguracji regionu, brak pobrań, brak zadań w tle.

Następny krok (komenda):
`cd C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\region-0166; Get-Content Data/Regions/bialystok-industrial-c/region.yaml, research/gptpro/2-next-regions/README.md, research/g10-truck-restrictions/README.md`
potem: wyznaczyć kafel 2x2 km Dojlidy/Krywlany, utworzyć `Data/Regions/bialystok-dojlidy/region.yaml` + manifest źródeł, sprawdzić `Data/raw` (osm/gugik), `uv run tools/worldgen/build_region.py --region bialystok-dojlidy`, `uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy`, QA, lista landmarków D51, ADR 0166.
