# STATUS — D26 worldgen-perf2-0281 (ADR 0281)

- K1b (STRtree po prostokącie), K1c (cache nan_to_num w crossfall_z), K2 (memo road_footprint_polygon), K4a (nan_to_num raz na build_meshes), K5 (cache textures()) — wdrożone + `tools/worldgen/tests/test_perf_0281.py` (10 passed).
- W toku: bieg bazowy C (`--nmt flat --skip-far-field`) na origin/main w scratchpad; potem bieg „po” i porównanie sha256.
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tools/worldgen/tests/test_perf_0281.py -q` + build przed/po (`qa/profile_build_world.py --nmt flat --skip-far-field --out-root <scratch>`).
