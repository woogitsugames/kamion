# STATUS — trailer-763-s23 (ADR 0280 §9: model 3D naczepy pod 7,63 m)
- Krok 0: worktree z origin/main @ 64e54592e; dims.json/trailer.json/TrailerAssetBuilder już mają −6.32/−7.63/−8.94.
  Generator Blendera czyta osie z dims.json (`trailer_build.py:37`); poprawiony komentarz, kamera `zbl_kolo` liczona z
  `T.AXLES[1]`, nowa kamera `gora` (ortho z góry). Rendery „przed” w `artifacts/trailer-763-s23/before/`.
- NASTĘPNY KROK: `blender -b --factory-startup --python tools/blender/truck/trailer/trailer_export.py` (eksport + rendery),
  potem `check_export.py`, `regs_audit.py`, `regs_check.py`.
