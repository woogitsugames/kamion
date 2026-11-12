$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $root
. scripts/env.ps1
if ((git branch --show-current).Trim() -ne 'gpt-edge-r3') { throw 'Wrong branch' }
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
& pwsh $slot -Acquire -Pool unity -Owner gpt-edge -PollSeconds 2 -StaleHours 100000
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
Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) Pełny import bazowy Low/High potwierdzony IMPORT_RESULT: OK; sprawdzono $checked gotowych map Medium bez niejawnego build_all. Następnie validate.ps1 -Phase Before."
git add -f artifacts/edge-r3/STATUS.md
git commit -m 'wip(edge): import integrated baseline before round 3 geometry changes'
if ($LASTEXITCODE -ne 0) { throw 'Checkpoint failed' }
& pwsh "$PSScriptRoot/validate.ps1" -Phase Before
if ($LASTEXITCODE -ne 0) { throw 'Baseline captures failed' }
