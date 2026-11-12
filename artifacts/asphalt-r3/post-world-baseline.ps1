param([Parameter(Mandatory)][int]$ProducerProcessId)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((& git branch --show-current).Trim() -ne 'gpt-asphalt-r3') { throw 'Wrong round' }
$producer=Get-CimInstance Win32_Process -Filter "ProcessId=$ProducerProcessId"
if($producer){
    if($producer.Name -ne 'pwsh.exe' -or $producer.CommandLine -notmatch '" artifacts/asphalt-r3/(prepare|resync)-baseline\.ps1$'){throw 'Unexpected producer to wait for'}
    "Waiting for own baseline producer PID $ProducerProcessId"
    Wait-Process -Id $ProducerProcessId -ErrorAction SilentlyContinue
}
$receipt=Get-Content artifacts/asphalt-r3/baseline-producer-progress.json -Raw|ConvertFrom-Json
if(-not $receipt.complete -or $receipt.world_exit -ne 0 -or $receipt.resync_merge -ne 'e5eb5902'){throw 'Fresh post-0131 producer did not complete'}
if($receipt.manifest_sha256 -ne (Get-FileHash Data/Regions/bialystok-industrial-c/generated/world_manifest.json).Hash){throw 'Producer receipt/manifest mismatch'}
$status=Get-Content artifacts/asphalt-r3/STATUS.md -Raw
if($status -notmatch 'heavy World owner=gpt-asphalt-r3 exit=0; log artifacts/asphalt-r3/baseline-World.log'){throw 'Matching World producer did not complete successfully'}
if(Select-String -Path artifacts/asphalt-r3/baseline-World.log -SimpleMatch 'fallback=True' -Quiet){throw 'World fallback present'}
& pwsh artifacts/asphalt-r3/run-heavy.ps1 -Stage SurfaceAudit -Label baseline
$code=$LASTEXITCODE
[ordered]@{finished_at=(Get-Date -Format o);producer_pid=$ProducerProcessId;surface_audit_exit=$code;next='Read yard-probe-baseline.json; choose and verify yard camera heights before Unity pose trial.'}|ConvertTo-Json|Set-Content artifacts/asphalt-r3/baseline-analysis-progress.json
Add-Content artifacts/asphalt-r3/STATUS.md "$(Get-Date -Format o): Odczyt materiałów placu i geometria baseline zakończone z kodem $code. Wyniki wymagają odczytania; nie wybrano jeszcze zmiany materiału ani pozy referencyjnej."
git add -f artifacts/asphalt-r3/STATUS.md artifacts/asphalt-r3/baseline-analysis-progress.json
git commit -q -m 'wip(asphalt): checkpoint source surface and geometry baseline analysis' 2> artifacts/asphalt-r3/git-checkpoint-warnings.log
exit $code
