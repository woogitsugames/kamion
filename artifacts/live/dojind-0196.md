# dojind-0196 (ADR 0196) — w toku
- Gałąź `dojind-0196`, worktree `.claude/worktrees/dojind-0196`. W TLE: `artifacts/dojind-0196/chain.ps1 -Tag r1` (czeka w kolejce slotu heavy → build_world dojlidy → import → visual-qa Low overcast; status `artifacts/dojind-0196/chain.status`, koniec `chain.done`). Nie zabijać.
- Kod: `buildings_mesh.py` (`wall_gates`, `runoff_blocks`/`runoff_cells` opt-in `facade_rules.runoff_shuffle`), `runway_paint.py` + hook `stage.py` (2 672 trójkąty farby pasa), `build_world.py` (`control_cameras_place.authored.json` → kamera `krywlany_runway`).
- Dane: blok „ADR 0196” w `Data/Regions/bialystok-dojlidy/overrides.yaml` (Kuronia 2: hala grafitowa 12,72 m + 5 części 9,0/7,2 m UNVERIFIED do M63; 2 bramy 4,5 × 5,0 m; oznakowanie pasa z ortofoto).
- Testy: `tests/gis/test_dojind_0196.py` 8 passed / 2 skipped (tekstura i generated przed buildem); 0179 + 0174 zielone. ADR: `docs/adr/0196-dojlidy-zaklad-bramy-zacieki-pas.md` (bez wyników).
- Budżet geometrii (offline, wszystkie budynki kafla): LOD0 467 487 → 476 890 (+2,0 %), LOD1 47 375 → 54 437 (+14,9 %), materiały LOD0 43 → 45, LOD1 48 → 50.
- BRAK: render, SBS, staty kadrów A/B, pełny pytest gis, EditMode, krytyk.
- NASTĘPNY KROK (gdy `chain.done`): `bash artifacts/dojind-0196/sbs.sh artifacts/dojind-0196/r1-Low-overcast artifacts/dojind-0196/sbs-r1` → obejrzeć sbs-P11-063/094 + `r1-Low-overcast/krywlany_runway.png`; gdy łańcuch nie działa: `pwsh -File artifacts/dojind-0196/chain.ps1 -Tag r1`.
