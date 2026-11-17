# STATUS cabin-polish-s23 (D84: wnętrze kabiny PC — polish po recenzji REVIEW-2026-11-17-s23-cabin-pc)
- Worktree z origin/main 14925a7cc. Skrypty odłączone: `artifacts/cabin-polish-s23/{run,chain,assets-win64,bl}.ps1` (status `*.status`, `exit=`).
- Krok 1 (plastik, P1-2): `plastic_grain.py` + `cab_material_scans.json` — ziarno 1,2–3 mm (z fotela 1 px ≈ 0,9 mm, stare 0,25–0,6 mm było podpikselowe), plamy połysku 2,5–10 cm, nachylenie normalnych mediana 8,9°, p95 18,2°. Tekstury jeszcze NIE zapisane do `art-source/.../export/textures` (czeka na baseline).
- Baseline we własnym worktree: `chain.ps1 -Tag base -Assets` w toku (pełny reimport Win64 Library).
- NASTĘPNY KROK: po `base-chain.status`: `uv run --project tools/worldgen python tools/blender/truck/interior/plastic_grain.py --output art-source/truck/interior/export/textures`; potem zmierzch (CabInteriorLighting), geometria (słupek A, kratki, daszek), eksport a6.
