# STATUS — D28 dense-lod-0282 (chmura D r7, ADR 0282)
- Krok 1: prototyp `tools/worldgen/qa/dense_lod_estimate.py` (model legacy = frame_estimate odtworzony 624/624 kategorii; model runtime = tabela LOD Unity + frustum + pas terenu; sonda generatora budynków) + `tests/gis/test_dense_lod_0282.py` 18 passed.
- Kalibracja SceneStats w gicie: Unity/legacy 0,47 (kleeberga, 14 kamer), 0,56 (C, 3); Unity/runtime 0,66 / 0,56.
- NASTĘPNY KROK: `uv run --project tools/worldgen python tools/worldgen/qa/dense_lod_estimate.py --buildings --json docs/reports/map/dense_lod_0282.json` → ADR 0282 + raport DENSE-LOD-2026-11-16 → PR.
