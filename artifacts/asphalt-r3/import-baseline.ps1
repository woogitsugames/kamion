$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((& git branch --show-current).Trim() -ne 'gpt-asphalt-r3') { throw 'Wrong round' }
$receipt=Get-Content artifacts/asphalt-r3/baseline-producer-progress.json -Raw|ConvertFrom-Json
if(-not $receipt.complete -or $receipt.world_exit -ne 0 -or $receipt.resync_merge -ne 'e5eb5902'){throw 'Fresh post-0131 producer did not complete'}
if($receipt.manifest_sha256 -ne (Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash){throw 'Producer receipt/manifest mismatch'}
$status=Get-Content artifacts/asphalt-r3/STATUS.md -Raw
if($status -notmatch 'heavy World owner=gpt-asphalt-r3 exit=0; log artifacts/asphalt-r3/baseline-World.log'){throw 'Fresh World producer has not completed'}
if(Select-String -Path artifacts/asphalt-r3/baseline-World.log -Pattern 'fallback=True' -SimpleMatch -Quiet){throw 'Fallback found'}
# Lightweight standard-library SHA audit, no NumPy or geometry/image analysis.
& uv run --project tools/worldgen python artifacts/asphalt-r3/audit_manifest.py *> artifacts/asphalt-r3/baseline-pre-import-audit.log
if($LASTEXITCODE -ne 0){throw 'Pre-import reference audit failed'}
$started=Get-Date
& pwsh artifacts/asphalt-r3/run-unity-stage.ps1 -Stage Import -Label baseline *> artifacts/asphalt-r3/baseline-import.log
$code=$LASTEXITCODE
$report='artifacts/world/bialystok-industrial-c-import.json'
if($code -eq 0){
    if(-not(Test-Path $report) -or (Get-Item $report).LastWriteTime -lt $started){throw 'Fresh import report missing'}
    Copy-Item -LiteralPath $report artifacts/asphalt-r3/baseline-import.json
}
[ordered]@{started_at=$started.ToString('o');finished_at=(Get-Date -Format o);exit=$code;note='Unity import only, no capture or material candidate chosen yet.'}|ConvertTo-Json|Set-Content artifacts/asphalt-r3/baseline-import-progress.json
Add-Content artifacts/asphalt-r3/STATUS.md "$(Get-Date -Format o): Import baseline zakończony z kodem $code. Świeży raport i log wymagają odczytania. Sonda powierzchni czeka w osobnej puli heavy; pełnego baseline capture jeszcze nie wykonano."
exit $code
