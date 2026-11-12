$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
& uv run --project tools/worldgen python artifacts/asphalt-r1/audit_manifest.py
if ($LASTEXITCODE -ne 0) { throw 'Candidate manifest/files mismatch' }
$log = Get-Content artifacts/asphalt-r1/candidate-World.log -Raw
if ($log -match 'fallback=True|Traceback') { throw 'Generator error or Megascans fallback' }
& pwsh artifacts/asphalt-r1/run-unity-stage.ps1 -Stage Import
if ($LASTEXITCODE -ne 0) { throw 'Candidate import failed' }
Add-Content artifacts/asphalt-r1/STATUS.md "$(Get-Date -Format o): Import kandydata zakończony. Następny krok: cztery serie Capture candidate."
git add -f artifacts/asphalt-r1/STATUS.md
git commit -m 'wip(asphalt): checkpoint candidate import'
& pwsh artifacts/asphalt-r1/run-unity-stage.ps1 -Stage Capture -Label candidate
if ($LASTEXITCODE -ne 0) { throw 'Candidate capture failed' }
Set-Content artifacts/asphalt-r1/CANDIDATE-COMPLETE.txt (Get-Date -Format o)
