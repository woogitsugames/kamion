# STATUS frontage-r2 (ADR 0129, pierzeja G3-B runda 2)

## 1. Worktree + rozpoznanie (2026-11-12 13:20-14:30)
Worktree `.claude/worktrees/frontage-r2`, gałąź `frontage-r2` (main f8b85fa2, ff). Dane skopiowane (derived, cc0, megascans, _Generated, Library), junctiony gugik/osm/refs/mapillary/fab.
`_Generated` z main jest sprzed scalenia 0126 (brak frontages w streetscape_qa) -> baseline izolowany = pełny cykl z kodu main w tym worktree (`run-cycle.ps1 -Name baseline -Tag 0`, w kolejce heavy).
Rozpoznanie: szkło = `glass` z sky_occ 0.9 (czarne z założenia), maszt = `downpipe` metal 0.7 (biały przy overcast), białe ogrodzenie = OSM way 344253283 / 913217348 z hasha `fence_galv`; plac aut na ortofoto 2024: 2 rzędy furgonów/aut E -179..-167 N -334..-345.
Zdjęcia 2024 stacji #21/#22 już są lokalnie (strudel 2024-08-15: 490210580292738, 469512365899192, 1020363345994649) -> kamery kontrolne z `reference_for` w `g3b_frontage_cameras.json` (pozy SBS nietknięte).
Kod rundy 2 gotowy w kopii roboczej (scratchpad/dev; testy 12 passed) - wchodzi do worktree PO starcie builda baseline.
NASTĘPNY KROK: po `cycle-0.done`: skopiować zmiany (frontage.py, materials.py, furniture.py, stage.py, buildings_mesh.py, overrides.yaml, test_g3b_frontage.py) i `pwsh artifacts/frontage-r2/run-cycle.ps1 -Name after -Tag 1`

## 2. Stan 13:50 (limit lidera 91 %)
Baseline `run-cycle.ps1 -Name baseline -Tag 0` nadal czeka w kolejce heavy (2 przed nami); działa w tle - nie przerywać.
Kod rundy 2 (testy 12 passed w kopii roboczej) leży w `artifacts/frontage-r2/pending/` (NIE w drzewie, żeby baseline był czysty). ADR szkic: `docs/adr/0129-frontage-r2.md` (RESULTS_PLACEHOLDER do uzupełnienia). Skrypt par: `artifacts/frontage-r2/make-pairs.py <after> <Tier-Lighting>`.
NASTĘPNY KROK (po linii `build exit=` w `artifacts/frontage-r2/cycle-0.log`): `cp -r artifacts/frontage-r2/pending/* . ; uv run --project tools/worldgen pytest tests/gis/test_g3b_frontage.py -q ; git add -A tools tests Data/Regions ; git commit -m "wip(frontage-r2): round-2 code" ; pwsh artifacts/frontage-r2/run-cycle.ps1 -Name after -Tag 1 ; python artifacts/frontage-r2/make-pairs.py after Low-overcast ; python artifacts/frontage-r2/stats-diff.py after`
