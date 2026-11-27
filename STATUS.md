# STATUS plaza-barn-fix-s24 (krytyk s24 dzień 27: skrzynie/kwiaty/cokół/ławki rynku Tykocina + wrota stodół)

- Worktree `agent-a8bad7a40407c997e`, gałąź `worktree-agent-a8bad7a40407c997e`. `Data/raw/derived` = PRYWATNA kopia (`tykocin`, `dk65-07`, `cache`),
  reszta `Data/raw/*` = junction do main; Library + `_Generated` (bez regionów) z worktree a492 (Win64). Układ: `artifacts/plaza-barn-fix-s24/setup.ps1`.
- Python: shim `artifacts/plaza-barn-fix-s24/shim/uv.cmd` (interpreter a492, Smart App Control).
- [krok 1] Rozpoznanie + setup; przebieg „przed” (kod HEAD 0e9424aaa): `pwsh artifacts/plaza-barn-fix-s24/pipeline.ps1 -Tag before`
  → `artifacts/plaza-barn-fix-s24/vqa-before/<region>/`.
- NASTĘPNY KROK: po „przed” — poprawki w `tykocin_rynek_0320.py`, `make_czarniecki.py`, `buildings_mesh.py`, potem
  `pwsh artifacts/plaza-barn-fix-s24/pipeline.ps1 -Tag after`.
