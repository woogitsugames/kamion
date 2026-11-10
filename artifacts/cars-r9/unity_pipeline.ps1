param([string]$Stage = 'after', [switch]$SkipImport, [switch]$SkipSetup, [string]$Tiers = 'Low,High', [string]$Lights = 'overcast,lowsun')
$ErrorActionPreference = 'Stop'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\agent-adeef0c396335e1ed'
Set-Location $wt
. "$wt\scripts\env.ps1"
$ev = "$wt\artifacts\cars-r9"
$lock = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
function Gate { while (Test-Path $lock) { Write-Host "LOCK present, waiting $(Get-Date -Format HH:mm:ss)"; Start-Sleep 60 } }
function Step([string]$name, [string]$method) {
    Gate
    $log = Join-Path $LogsDir "cars-r9-$name-$(Get-Timestamp).log"
    $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod', $method)
    Write-Host "STEP $name exit $code log $log"
    if ($code -ne 0) { Show-UnityLogErrors $log; throw "$name failed ($code)" }
}
if (-not $SkipSetup) {
    Step 'truck' 'Game.Editor.Setup.TruckAssetBuilder.BuildBatch'
    Step 'trailer' 'Game.Editor.Setup.TrailerAssetBuilder.BuildBatch'
}
if (-not $SkipImport) {
    Gate
    & pwsh "$wt\scripts\import-region.ps1" -Region bialystok-industrial-c
    if ($LASTEXITCODE -ne 0) { throw "import-region failed ($LASTEXITCODE)" }
    Write-Host 'IMPORT DONE'
    Step 'install' 'Game.World.Import.WorldTruckInstaller.InstallBatch'
}
$cams = 'cab-dash,truck-34,stretch_01,glass_side_00,glass_side_40,glass_front,car_lod_08,car_lod_12,car_lod_15,car_lod_25'
foreach ($tier in $Tiers.Split(',')) {
    foreach ($light in $Lights.Split(',')) {
        Gate
        $out = Join-Path $ev "$Stage\$tier-$light"
        & "$wt\scripts\visual-qa.ps1" -Scene WorldC -Tier $tier -Lighting $light -OutputDir $out -Cameras $cams -Gate3 "$ev\car_cams.json"
        Write-Host "QA $tier $light exit $LASTEXITCODE"
    }
}
Write-Host 'PIPELINE DONE'
