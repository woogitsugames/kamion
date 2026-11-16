# STATUS ci-gis-s23 (D20)
- CI gis: selektywny `git lfs pull --include $LFS_GIS` (~18 MB, 55 obiektów) + cache `.git/lfs/objects` po liście oid;
  `require_lfs` w test_forest_0187; KAMION_LFS_REQUIRED = wskaźnik z listy CI -> fail zamiast skip.
- NASTĘPNY KROK: `uv run --project tools/worldgen python -m pytest tests/gis -q` (wskaźnik vs `git lfs pull --include ...`), push, PR.
