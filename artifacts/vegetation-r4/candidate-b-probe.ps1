$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. ./artifacts/vegetation-r4/checkpoint.ps1
if (-not (Test-Path artifacts/vegetation-r4/green-b-and-world.done)) { throw 'World B not completed; inspect live task before retrying' }
if (Test-Path artifacts/vegetation-r4/snapshot-candidate-b) { throw 'Snapshot B exists; inspect state before repeating' }
if ((git branch --show-current).Trim() -ne 'gpt-vegetation-r4') { throw 'Wrong branch' }
# Streaming hashes and small JSON only; no build/test/mesh decoding here.
uv run --project tools/worldgen python artifacts/vegetation-r4/snapshot.py candidate-b *> artifacts/vegetation-r4/snapshot-candidate-b.log
if ($LASTEXITCODE -ne 0) { throw 'Snapshot B failed' }
uv run --project tools/worldgen python artifacts/vegetation-r4/compare_candidate.py candidate-b --allow-plantings-triangle-change *> artifacts/vegetation-r4/compare-candidate-b.log
if ($LASTEXITCODE -ne 0) { throw 'Candidate B provenance mismatch' }
Add-Content artifacts/vegetation-r4/STATUS.md 'Piny B przeszły: poza jawną zmianą tris nasadzeń reszta kontraktów danych zachowana. Budżet kamer jeszcze niepotwierdzony. Następny import i16prób B.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 pochodzenie B sprawdzone' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/candidate-b-input-proof.json')
pwsh artifacts/vegetation-r4/import-safe.ps1 -Log artifacts/vegetation-r4/import-candidate-b.log
if ($LASTEXITCODE -ne 0) { throw 'Import B failed' }
Add-Content artifacts/vegetation-r4/STATUS.md 'Import B kod0. Dalej16prób w tych samych kamerach i warunkach.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 B zaimportowany'
pwsh artifacts/vegetation-r4/probe-hedges.ps1 -Tag probe-b
if ($LASTEXITCODE -ne 0) { throw 'Probe B failed' }
Set-Content artifacts/vegetation-r4/candidate-b-probe.done 'Import and16probe frames exit0; visual review and full-camera budgets still required.'
