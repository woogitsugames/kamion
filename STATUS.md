# STATUS worldgen-perf-s23 (D22)

- DONE (analiza): raport `docs/reports/WORLDGEN-PERF-2026-11-16.md` — 5 kosztów (2× pipeline.build 28,5 %, road_footprint_polygon ×5 16,6 %, plan działek ~14 % / 63 % na kleeberga, paved.build_meshes 9 %, biblioteka propsów 7,9 %), propozycje z zyskiem/ryzykiem, plan pomiaru.
- Profiler `tools/worldgen/qa/profile_build_world.py` + test (2 passed). Zero zmian w generatorze.
- NASTĘPNY KROK (lider): `uv run --project tools/worldgen python tools/worldgen/qa/profile_build_world.py --region bialystok-industrial-c --out-root artifacts/perf/c/world --prof artifacts/perf/c/bw_c.prof --json artifacts/perf/c/stages.json --i-know-generated-is-dirtied` i `git checkout -- Data/Regions/bialystok-industrial-c/generated art-source/world/landmarks`.
