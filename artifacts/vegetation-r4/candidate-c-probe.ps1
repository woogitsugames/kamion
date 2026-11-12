$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. ./artifacts/vegetation-r4/checkpoint.ps1
if (-not (Test-Path artifacts/vegetation-r4/green-c-and-world.done)) { throw 'World C not completed; inspect live task before retrying' }
if (Test-Path artifacts/vegetation-r4/snapshot-candidate-c) { throw 'Snapshot C exists; inspect state before repeating' }
if ((git branch --show-current).Trim() -ne 'gpt-vegetation-r4') { throw 'Wrong branch' }
# Streaming hashes and small JSON only; no build/test/mesh decoding here.
uv run --project tools/worldgen python artifacts/vegetation-r4/snapshot.py candidate-c *> artifacts/vegetation-r4/snapshot-candidate-c.log
if ($LASTEXITCODE -ne 0) { throw 'Snapshot C failed' }
uv run --project tools/worldgen python artifacts/vegetation-r4/compare_candidate.py candidate-c --allow-plantings-triangle-change *> artifacts/vegetation-r4/compare-candidate-c.log
if ($LASTEXITCODE -ne 0) { throw 'Candidate C provenance mismatch' }
Add-Content artifacts/vegetation-r4/STATUS.md 'Piny C przeszły: poza jawną zmianą tris nasadzeń reszta kontraktów danych zachowana. Budżet kamer jeszcze niepotwierdzony. Następny import i 16 prób C.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 pochodzenie C sprawdzone' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/candidate-c-input-proof.json')
pwsh artifacts/vegetation-r4/import-safe.ps1 -Log artifacts/vegetation-r4/import-candidate-c.log
if ($LASTEXITCODE -ne 0) { throw 'Import C failed' }
Add-Content artifacts/vegetation-r4/STATUS.md 'Import C kod0. Dalej16prób w tych samych kamerach i warunkach.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 C zaimportowany'
pwsh artifacts/vegetation-r4/probe-hedges.ps1 -Tag probe-c
if ($LASTEXITCODE -ne 0) { throw 'Probe C failed' }
Set-Content artifacts/vegetation-r4/candidate-c-probe.done 'Import and16probe frames exit0; visual review and full-camera budgets still required.'
