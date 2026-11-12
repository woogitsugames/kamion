$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $root
$owner = (git branch --show-current).Trim()
if ($owner -ne 'gpt-edge-r3') { throw "Unexpected branch $owner" }
$main = 'C:/Users/matma/Documents/Claude/kamion'
# Only immutable source caches. Main is regenerating its derived world concurrently.
foreach ($relative in @('Data/raw/cc0','art-source/world/cc0/_raw','art-source/world/megascans')) {
    & robocopy (Join-Path $main $relative) (Join-Path $root $relative) /E /XJ /MT:1 /R:1 /W:1 /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -ge 8) { throw "Cache copy failed: $relative" }
}
function Save-Step([string]$message) {
    Add-Content "$PSScriptRoot/STATUS.md" "$(Get-Date -Format o) $message"
    git add -f artifacts/edge-r3/STATUS.md
    git commit -m "wip(edge): $message"
    if ($LASTEXITCODE -ne 0) { throw 'Checkpoint failed' }
}
Save-Step 'Odświeżono niezmienne cache CC0/Megascans; nie kopiowano aktywnie regenerowanych derived ani scen main.'
$slot = Join-Path $main 'scripts/unity-slot.ps1'
$started = Get-Date -Format o
& pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 2 -StaleHours 100000
if ($LASTEXITCODE -ne 0) { throw 'Heavy slot failed' }
$acquired = Get-Date -Format o
$materialsCode = 1
$worldCode = 1
try {
    $env:PYTHONUNBUFFERED = '1'
    & uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py *> "$PSScriptRoot/build-materials.log"
    $materialsCode = $LASTEXITCODE
    if ($materialsCode -ne 0) { throw "Materials failed: $materialsCode" }
    Save-Step 'Zregenerowano zestawy materiałów nowego main pod heavy; bez zmian źródeł innych dziedzin.'
    & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$PSScriptRoot/build-world-baseline.log"
    $worldCode = $LASTEXITCODE
    if ($worldCode -ne 0) { throw "World baseline failed: $worldCode" }
    if (Select-String -LiteralPath "$PSScriptRoot/build-world-baseline.log" -SimpleMatch 'fallback=True' -Quiet) {
        throw 'Megascans fallback detected'
    }
    Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json "$PSScriptRoot/baseline-operational-world-manifest.json"
    Save-Step 'Zregenerowano pełny świat bazowy r3 bez fallback=True; następnie pełny import Unity i rendery Before.'
} finally {
    & pwsh $slot -Release -Pool heavy -Owner $owner -StaleHours 100000
    @{owner=$owner;pool='heavy';started=$started;acquired=$acquired;finished=(Get-Date -Format o);
      materials_exit_code=$materialsCode;world_exit_code=$worldCode} | ConvertTo-Json |
        Set-Content "$PSScriptRoot/baseline-preparation-receipt.json"
}
