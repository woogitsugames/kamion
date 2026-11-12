# junctions-r7 (ADR 0144) — STATUS
- 2026-11-12 19:05 sha 1aa3f16cf: generator + shader + importer + overrides + tests/gis/test_guardrail_overlap.py (5 unit pass, 3 region skip do czasu regeneracji). Baza „przed”: m1 = build main w tym worktree (logs/m1_*), rendery b7 (kamery węzła) / i3 (SBS) z main artifacts.
- Źródła filarów: OSM 0 węzłów bridge:support w oknie (logs/osm_supports.txt); BDOT10k OT_BUIN_L = 2 linie „estakada” po 196,0 m (466,6 −675,6 → 638,7 −769,3) = zakres otwarty modelu 196,25 m (przyczółki potwierdzone danymi), brak filarów; ortofoto 0,08 m zasłonięte pomostem -> rytm rzędów ze zdjęć Mapillary 2818/3970/178689.
- 19:14 W TLE: build r7a, 2. próba (1. próba: MemoryError 32 MiB w paved.build_meshes przy 24 GB wolnych, przejściowe) -> logs/r7a_build.out, r7a_build.log; heavy slot claude-junctions-r7.
- NASTĘPNY KROK: `CAMS=artifacts/junctions-r7/cams_r7.json bash artifacts/junctions-r7/scripts/imp.sh r7a` (import + Low clear + Low overcast), potem pary (scripts/pairs.sh r7a), post.sh r7a full, EditMode.
- Gotowe do scalenia: NIE (brak renderów i testów regionu).
