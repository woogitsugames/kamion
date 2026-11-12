# world-int-s16 STATUS
- 23:31 worktree z origin/main 55e66520d, prep (derived, cc0, megascans, _Generated, Library; junctiony gugik/osm/refs/mapillary/fab).
- 23:33 baseline Low-clear (import main) -> `before/Low-clear` (48 PNG, stats.txt).
- 23:3x łańcuch Python w tle: build_all -> build_world (navgraph wpięty, M27) -> export-route -> fidelity.
- NASTĘPNY KROK: `pwsh -NoProfile -File artifacts/world-int-s16/tools/chain-unity.ps1 -Tag after` (import, trim, EditMode, vqa Low/High)
- 00:05 import OK (64 chunks), ImpostorTrimBake 18 impostorów (37 %), EditMode 467/467, vqa Low/High clear -> after/.
- 00:20 pytest gis 935 passed, 4 xfailed (M29 free deck ends 32 -> 2, xfail zostaje). SBS pary Low overcast+clear 42/42 -> sbs/pairs.
- NASTĘPNY KROK: ocena par 494288/482392/320326/297817/275528, wpis do sbs_recognition.json, raport docs/reports/WORLD-INTEGRATION-2026-11-13-s16.md
