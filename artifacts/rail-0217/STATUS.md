# STATUS rail-0217 (ADR 0217)
- krok 1: streetscape/rail.py + hooki build_world/build_region/stage + Region.rail; tests/gis/test_rail_0217.py 23/23, water 0210 5/5.
- NASTEPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis -q` + ADR 0217.
- krok 2: ADR 0217 + LICENSES; pelny pytest tests/gis w toku.
- NASTEPNY KROK: sprawdzic log pytest, PR do main.
- krok 3: pytest tests/gis 1282 passed, 47 skipped (Data/raw), 3 xfailed; deselected: determinism hash-seed (3x pelny build) i road_fidelity stale (build_world.py zmieniony -> lider odswieza fidelity C).
- NASTEPNY KROK (lider): wlaczyc rail=True w dw671-tykocin-01 i uruchomic komendy z ADR 0217 "Odtworzenie".
