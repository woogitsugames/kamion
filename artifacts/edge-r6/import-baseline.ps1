param([switch]$ResumeVehicle)
$ErrorActionPreference = 'Stop'
if(Test-Path "$PSScriptRoot/STOP.requested"){
    @{state='paused-by-owner-before-import';observed=(Get-Date -Format o);
      note='Queued world preparation may finish; no Unity import/captures started after owner stop.'}|
        ConvertTo-Json|Set-Content "$PSScriptRoot/PAUSED-BEFORE-IMPORT.json"
    Write-Host 'Owner requested handover; prepared world retained, baseline import intentionally not started.'
    exit 75
}
$root = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $root
. scripts/env.ps1
$cloudPath=Join-Path $root 'game/Assets/_Project/Rendering/Resources/Sky/T_ClearClouds.png'
$cloudBytes=[IO.File]::ReadAllBytes($cloudPath)
if(($cloudBytes[0..7] -join ',') -ne '137,80,78,71,13,10,26,10'){throw 'Cloud PNG missing or still an LFS pointer'}
if ((git branch --show-current).Trim() -ne 'gpt-edge-r6') { throw 'Wrong branch' }
$receipt = Get-Content "$PSScriptRoot/baseline-preparation-receipt.json" -Raw | ConvertFrom-Json
if ($receipt.materials_exit_code -ne 0 -or $receipt.world_exit_code -ne 0) { throw 'Baseline preparation failed' }
if (-not (Test-Path "$PSScriptRoot/baseline-operational-world-manifest.json")) { throw 'Missing successful source snapshot' }
if (Select-String -LiteralPath "$PSScriptRoot/build-world-baseline.log" -SimpleMatch 'fallback=True' -Quiet) {
    throw 'Megascans fallback detected'
}
# Reproduce the import script's material preflight, but refuse an implicit Python
# rebuild here: build_all has already run separately inside the heavy pool.
$matRoot = Join-Path $root 'art-source/world/materials'
$spec = Get-Content (Join-Path $matRoot 'materials_spec.json') -Raw | ConvertFrom-Json
$sourceTime = (Get-ChildItem (Join-Path $matRoot '_src') -Filter *.py | Measure-Object LastWriteTimeUtc -Maximum).Maximum
$checked = 0
foreach ($set in $spec.sets.PSObject.Properties) {
    $files = $set.Value.files.Medium
    if (-not $files) { continue }
    foreach ($name in $files.files) {
        $path = Join-Path $matRoot "$($files.dir)/$name"
        if (-not (Test-Path -LiteralPath $path)) { throw "Missing material map: $path" }
        if ((Get-Item -LiteralPath $path).LastWriteTimeUtc -lt $sourceTime) { throw "Stale material map: $path" }
        $checked++
    }
}
$slot = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
if (-not $ResumeVehicle) {
    & pwsh -File "$PSScriptRoot/acquire-slot.ps1" -Pool unity -Owner gpt-edge
    if ($LASTEXITCODE -ne 0) { throw 'Unity slot failed' }
    try {
        $code = Invoke-UnityBatch -LogFile "$PSScriptRoot/import-baseline.log" -Arguments @(
            '-executeMethod','Game.World.Import.RegionImporter.ImportBatch',
            '-region','bialystok-industrial-c','-tiers','Low,High','-materialTier','Medium')
        if ($code -ne 0 -or -not (Select-String -LiteralPath "$PSScriptRoot/import-baseline.log" -Pattern 'IMPORT_RESULT: OK' -SimpleMatch -Quiet)) {
            throw "Full baseline import failed: $code"
        }
    } finally {
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
        & pwsh $slot -Release -Pool unity -Owner gpt-edge -StaleHours 100000
    }
} elseif (-not (Select-String -LiteralPath "$PSScriptRoot/import-baseline.log" -Pattern 'IMPORT_RESULT: OK' -SimpleMatch -Quiet)) {
    throw 'Cannot resume the vehicle step without a successful full world import'
}
# The merged cab source needs its generated prefab rebuilt as well; importing the
# world alone reuses an existing prefab. This is baseline preparation, not a cab edit.
& pwsh -File "$PSScriptRoot/acquire-slot.ps1" -Pool unity -Owner gpt-edge
if ($LASTEXITCODE -ne 0) { throw 'Truck baseline slot failed' }
try {
    $truckCode = Invoke-UnityBatch -LogFile "$PSScriptRoot/install-baseline-truck.log" -Arguments @(
        '-executeMethod','Game.World.Import.WorldTruckInstaller.InstallBatch')
    if ($truckCode -ne 0 -or -not (Select-String -LiteralPath "$PSScriptRoot/install-baseline-truck.log" -Pattern 'TRUCK_RESULT: OK' -SimpleMatch -Quiet)) {
        throw "Truck baseline preparation failed: $truckCode"
    }
} finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Pool unity -Owner gpt-edge -StaleHours 100000
}
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Pełny import bazowy Low/High i odtworzenie generowanych prefabów pojazdów nowego main potwierdzone IMPORT_RESULT/TRUCK_RESULT: OK; sprawdzono $checked gotowych map Medium bez niejawnego build_all. Źródła cab/truck bez edycji. Następnie validate.ps1 -Phase Before."
git add -f artifacts/edge-r6/STATUS.md
git commit -m 'wip(edge): import integrated baseline before round 6 edge changes'
if ($LASTEXITCODE -ne 0) { throw 'Checkpoint failed' }
& pwsh "$PSScriptRoot/validate.ps1" -Phase Before
if ($LASTEXITCODE -ne 0) { throw 'Baseline captures failed' }
