$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
# These are this worktree's two Python launcher PIDs, recorded at launch; never stop/touch other sessions.
while ((Get-Process -Id 90580,112584 -ErrorAction SilentlyContinue).Count -gt 0) {
    Start-Sleep -Seconds 10
}
$log = Get-Content artifacts/asphalt-r1/baseline-build-world.log -Raw
if ($log -match 'Traceback|fallback=True') { throw 'World generator error or Megascans fallback; inspect baseline log' }
$manifest = Get-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json
if ($manifest.LastWriteTime -lt [datetime]'2026-11-11T21:33:46') { throw 'Fresh baseline manifest not found' }
Add-Content artifacts/asphalt-r1/STATUS.md "$(Get-Date -Format o): zakończono build_world baseline. Rozpoczynam import, następnie cztery serie bazowe; slot pobierany osobno przed każdym Unity."
git add -f artifacts/asphalt-r1/STATUS.md
git commit -m 'wip(asphalt): checkpoint fresh world before baseline import'
& pwsh artifacts/asphalt-r1/run-unity-stage.ps1 -Stage Import
if ($LASTEXITCODE -ne 0) { throw 'Baseline import failed' }
Add-Content artifacts/asphalt-r1/STATUS.md "$(Get-Date -Format o): import baseline zakończony. Następny krok: Capture baseline."
git add -f artifacts/asphalt-r1/STATUS.md
git commit -m 'wip(asphalt): checkpoint baseline import'
& pwsh artifacts/asphalt-r1/run-unity-stage.ps1 -Stage Capture -Label baseline
if ($LASTEXITCODE -ne 0) { throw 'Baseline capture failed' }
Set-Content artifacts/asphalt-r1/BASELINE-COMPLETE.txt (Get-Date -Format o)
