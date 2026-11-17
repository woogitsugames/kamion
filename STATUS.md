# STATUS cabin-polish-s23 (D84: wnętrze kabiny PC — polish po recenzji REVIEW-2026-11-17-s23-cabin-pc)
- Worktree z origin/main 14925a7cc. Skrypty odłączone: `artifacts/cabin-polish-s23/{run,chain,assets-win64,bl,a6}.ps1` (status `*.status`, `exit=`).
- Baseline we własnym worktree (Win64 High -Pc): `artifacts/cabin-polish-s23/base-{clear,dusk}` (8 kamer), pomniejszone w `view/`.
- Krok 1 plastik (P1-2): `plastic_grain.py` + `cab_material_scans.json` — ziarno 1,2–3 mm + plamy połysku; normalne mediana 8,9°, p95 18,2°.
- Krok 2 zmierzch (P1-3): `CabInteriorLighting` — `nightViewEv` 0,25 (wygaszanie podbicia +3°…−5°), `panelGlow` 0,035 ciepły. ADR: `docs/adr/DRAFT-d84-kabina-polish-zmierzch-i-ziarno.md`.
- Krok 3 geometria (`build_interior.py`): uszczelki + zaślepki słupka A, żebra tacek deski, daszek zegarów (fade 50 mm), roleta kierowcy 0,30 m, przeszycie ×3,2, wytarcie wieńca niesymetryczne. LOD0-only przez `LOD1_DROP` (pierwszy eksport: LOD1 45 625 / LOD2 22 304 ponad limit).
- Surowe skany skóry (CC0, md5 zgodne z configiem) skopiowane lokalnie z `artifacts/cab-r1/cc0-prep` do `art-source/truck/interior/cc0/_raw/brown_leather` (gitignore).
- NASTĘPNY KROK: po `a6.status exit=0`: `blender -b --factory-startup --python-exit-code 1 --python tools/blender/truck/interior/check_export.py`; potem `pwsh artifacts/cabin-polish-s23/chain.ps1 -Tag r1 -Assets -Tests`; obejrzeć `r1-{clear,dusk}`.
