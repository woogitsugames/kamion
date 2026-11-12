# junctions-r7 (ADR 0144) — STATUS
- 2026-11-12 19:05 sha 1aa3f16cf: generator + shader + importer + overrides + tests/gis/test_guardrail_overlap.py (5 unit pass, 3 region skip do czasu regeneracji). Baza „przed”: m1 = build main w tym worktree (logs/m1_*), rendery b7 (kamery węzła) / i3 (SBS) z main artifacts.
- Źródła filarów: OSM 0 węzłów bridge:support w oknie (logs/osm_supports.txt), ortofoto 0,08 m zasłonięte pomostem (ortho/via_*.jpg) -> pomiar ze zdjęć Mapillary 2818/3970/178689.
- W TLE: build r7a (bash artifacts/junctions-r7/scripts/build.sh r7a -> logs/r7a_build.out, r7a_build.log; ~12 min, heavy slot claude-junctions-r7).
- NASTĘPNY KROK: `CAMS=artifacts/junctions-r7/cams_r7.json bash artifacts/junctions-r7/scripts/imp.sh r7a` (import + Low clear + Low overcast), potem pary (scripts/pairs.sh r7a), post.sh r7a full, EditMode.
- Gotowe do scalenia: NIE (brak renderów i testów regionu).
