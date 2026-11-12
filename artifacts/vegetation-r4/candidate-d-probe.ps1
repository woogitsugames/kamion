$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. ./artifacts/vegetation-r4/checkpoint.ps1
if (-not (Test-Path artifacts/vegetation-r4/green-d-and-world.done)) { throw 'World D not completed; inspect live task before retrying' }
if (Test-Path artifacts/vegetation-r4/snapshot-candidate-d) { throw 'Snapshot D exists; inspect state before repeating' }
if ((git branch --show-current).Trim() -ne 'gpt-vegetation-r4') { throw 'Wrong branch' }
# Streaming hashes and small JSON only; no build/test/mesh decoding here.
# One bounded1m terrain accessor read additionally checks the frozen test input.
uv run --project tools/worldgen python artifacts/vegetation-r4/extract_ground_fixture.py --verify *> artifacts/vegetation-r4/verify-ground-d.log
if ($LASTEXITCODE -ne 0) { throw 'D conformed ground differs from the frozen C test fixture' }
uv run --project tools/worldgen python artifacts/vegetation-r4/snapshot.py candidate-d *> artifacts/vegetation-r4/snapshot-candidate-d.log
if ($LASTEXITCODE -ne 0) { throw 'Snapshot D failed' }
uv run --project tools/worldgen python artifacts/vegetation-r4/compare_candidate.py candidate-d --allow-plantings-triangle-change *> artifacts/vegetation-r4/compare-candidate-d.log
if ($LASTEXITCODE -ne 0) { throw 'Candidate D provenance mismatch' }
Add-Content artifacts/vegetation-r4/STATUS.md 'Piny D przeszły: poza jawną zmianą tris nasadzeń reszta kontraktów danych zachowana. Budżet kamer jeszcze niepotwierdzony. Następny import i 16 prób C.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 pochodzenie D sprawdzone' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/candidate-d-input-proof.json','artifacts/vegetation-r4/ground-fixture-d-proof.json')
pwsh artifacts/vegetation-r4/import-safe.ps1 -Log artifacts/vegetation-r4/import-candidate-d.log
if ($LASTEXITCODE -ne 0) { throw 'Import D failed' }
Add-Content artifacts/vegetation-r4/STATUS.md 'Import D kod0. Dalej16prób w tych samych kamerach i warunkach.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 D zaimportowany'
pwsh artifacts/vegetation-r4/probe-hedges.ps1 -Tag probe-d
if ($LASTEXITCODE -ne 0) { throw 'Probe D failed' }
Set-Content artifacts/vegetation-r4/candidate-d-probe.done 'Import and16probe frames exit0; visual review and full-camera budgets still required.'
