# S10 F / ADR0087
- Step1: read current F contract, owner glass decisions D31/D34/D44, ADR0059/0083 and project rules. Branch gpt-truck-paint at232fbada; A completed separately38149050. No source changes yet.
- NEXT COMMAND: git lfs checkout; copy ignored local sources/caches, read-only junction raw source folders, audit gitdiff, then fresh world build/import and canonical truck/trailer build/install before baseline.

- Step2: copied private Data/raw derived+cc0, CC0raw, Fab products, Unity Generated/Library, photos and PNG/NPY/NPZ material caches only. Read-only-use source junctions created. gitdiff clean. Missing ignored interiorLOD0 FBX SHA177d820ebe99b45b359789469107eaa498198e679a851a24db912ebd2a2930fe copied from main.
- NEXT COMMAND: uv run --project tools/worldgen python tools/worldgen/roads/build_world.py --region bialystok-industrial-c; then import-region +canonicalTruck/Trailer builders/install, snapshot and baseline6conditions.

- Step3: added isolated QA round17cameras x6conditions with exact LowWorldC/HighWorldC_High, actual TruckExterior Color GPU probe, true no-pane reference (disable GLASS_ renderers, not old partial qaNoGlass), and coat-off diagnostic. Canonical snapshot will preserve every GeneratedTruck/Trailer file plus raw192SHA and actual nested FabQA. No production shader/material changes. C confirms no vehicle edits; future clear-shoulder integration review remains separate.
- NEXT COMMAND: pwsh -ExecutionPolicy Bypass -File artifacts/truck-paint-r1/prepare-baseline.ps1 (queued after current world build); snapshot_fixture.py; run-round.ps1 before; run-baseline-ablations.ps1.

- Step4: root authorized merge latest main into F before any baseline captures. Stopped only verified own build_all PythonPID42312 while no Unity was active; no vehicle production edits/no baseline images. Fresh321.6s old-base world metadata persisted as WIP only.
- NEXT COMMAND: git merge main --no-edit (into F only); regenerate world and all PBR from merged sources, then canonical builders/install, raw192SHA/Fab15+320 proof and snapshot before baseline.

- Step5: merged main db1432c5 into F atf52fabf6 before captures; fresh fullPBR+world regeneration running from A-correct sources. Source diagnosis being tested: DRL160000/high80000 encoded directly in RGBAHalf(max65504) may overflow. Probe now records actual GPU texture sampling day/night/on/off alongside Color upload, before production edits.
- NEXT COMMAND: wait fresh PBR/world completion; prepare-baseline.ps1; snapshot_fixture.py; baseline102PNG plus no-pane/no-coat diagnostics.

- Step6: A-correct world finished339.5s; fullPBR near completion. Baseline preparation queued with per-Unity phone guards, canonicalTruck+Trailer+Install, shader/light GPU probe, immutable Generated snapshot including production sourceSHA then102matched images. Actual lampGPU and day/night state evidence pending; no production fix assumed.
- NEXT COMMAND: inspect baseline-prepare-a-correct.log and baseline-fixture-proof.log; then resize/view before102 and measure no-coat/no-pane references.
