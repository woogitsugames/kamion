# STATUS worldgen-perf-s23 (D22)

- Analiza kosztu build_world (bez zmian w generatorze). Skrypt `tools/worldgen/qa/profile_build_world.py` (timery etapów + cProfile, NMT syntetyczny).
- Pomiar w chmurze: C na płaskim NMT, w jednorazowym worktree (scratchpad) — w toku.
- NASTĘPNY KROK: `uv run --project tools/worldgen python tools/worldgen/qa/profile_build_world.py --region bialystok-industrial-c --nmt flat --skip-far-field --out-root <scratch>/world --prof <scratch>/bw.prof --i-know-generated-is-dirtied` (w jednorazowym worktree), potem raport docs/reports/WORLDGEN-PERF-2026-11-16.md.
