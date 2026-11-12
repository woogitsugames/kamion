$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. ./artifacts/vegetation-r4/checkpoint.ps1
if (-not (Test-Path artifacts/vegetation-r4/green-and-world.done)) { throw 'World not completed; do not launch duplicate work' }
if (Test-Path artifacts/vegetation-r4/snapshot-candidate-a) { throw 'Snapshot already exists; inspect live state before repeating' }
$owner=(git branch --show-current).Trim()
if ($owner -ne 'gpt-vegetation-r4') { throw 'Wrong branch' }
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
# These two helpers use only stdlib, streaming file hashes and small JSON
# comparisons. They do not generate a world, decode meshes, render or run tests.
# The heavy World/collision job already completed and released its slot.
uv run --project tools/worldgen python artifacts/vegetation-r4/snapshot.py candidate-a *> artifacts/vegetation-r4/snapshot-candidate-a.log
if ($LASTEXITCODE -ne 0) { throw 'Candidate snapshot failed' }
uv run --project tools/worldgen python artifacts/vegetation-r4/compare_candidate.py candidate-a *> artifacts/vegetation-r4/compare-candidate-a.log
if ($LASTEXITCODE -ne 0) { throw 'Candidate provenance mismatch; stop before import' }
Add-Content artifacts/vegetation-r4/STATUS.md 'Migawka A: kontrola źródeł, wszystkich instancji, dekodowanej kolizji i nasadzeń przeszła. Import i 16 próbnych kadrów dalej, bez akceptacji wyglądu.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 pochodzenie kandydata A sprawdzone' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/candidate-a-input-proof.json')
pwsh artifacts/vegetation-r4/import-safe.ps1 -Log artifacts/vegetation-r4/import-candidate-a.log
if ($LASTEXITCODE -ne 0) { throw 'Candidate import failed' }
Add-Content artifacts/vegetation-r4/STATUS.md 'Import kandydata A kod 0; następny krok to 16 próbnych kadrów.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 kandydat A zaimportowany'
pwsh artifacts/vegetation-r4/probe-hedges.ps1 -Tag probe-a
if ($LASTEXITCODE -ne 0) { throw 'Candidate probe failed' }
Set-Content artifacts/vegetation-r4/candidate-a-probe.done 'Import and four probe groups exit0; review still required.'
