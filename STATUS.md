# STATUS plaza-barn-fix-s24 (krytyk s24 dzień 27: skrzynie/kwiaty/cokół/ławki rynku Tykocina + wrota stodół)

- Worktree `agent-a8bad7a40407c997e`, gałąź `worktree-agent-a8bad7a40407c997e`. `Data/raw/derived` = PRYWATNA kopia (`tykocin`, `dk65-07`, `cache`),
  reszta `Data/raw/*` = junction do main; Library + `_Generated` (bez regionów) z worktree a492 (Win64). Układ: `artifacts/plaza-barn-fix-s24/setup.ps1`.
- Python: shim `artifacts/plaza-barn-fix-s24/shim/uv.cmd` (interpreter a492, Smart App Control).
- [krok 1] Setup; build_world „przed” (kod HEAD 0e9424aaa) tykocin 965 s, dk65-07 746 s, exit 0.
- [krok 2] Kod: `tykocin_rynek_0320.py` (10 skrzyń 0,91 m w pierścieniu 2,80 m, begonie karminowe kopułką, 2 bejce ławek),
  `make_czarniecki.py` (nalot/zacieki dołu cokołu, pole inskrypcji z ramą; asset przebudowany Blenderem, LOD0 26 516),
  `buildings_mesh.py`/`facade_kit.py`/`materials.py` (wrota stodół: tint COLOR_0 na facade_atlas, zwietrzałe szaro-brązowe).
  pytest truss_bridge_0320 + rural_outbuildings + typology_0238 + budget_0221: 59/59.
- [krok 3] W toku: `after.ps1` czeka na import+VQA „przed”, potem `pipeline.ps1 -Tag after` → `artifacts/plaza-barn-fix-s24/vqa-{before,after}/<region>/`.
- NASTĘPNY KROK: arkusze przed|po (`magick`), dopiski ADR 0320 / 0238, commit. Nie scalać.
