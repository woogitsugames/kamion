param([string]$Log = 'artifacts/vegetation-r3/import-after.log')
$ErrorActionPreference = 'Stop'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
# Fail before Unity acquisition if import-region would silently launch a heavy
# Python generator. Run that generator separately through heavy-task.ps1 first.
if (-not (Test-Path Data/raw/derived/bialystok-industrial-c/world/chunk_0_0.glb) -or
    -not (Test-Path Data/Regions/bialystok-industrial-c/route_start.json)) {
    throw 'World/route inputs missing; prepare them explicitly before import.'
}
$materialRoot = Join-Path (Get-Location).Path 'art-source/world/materials'
$spec = Get-Content (Join-Path $materialRoot 'materials_spec.json') -Raw | ConvertFrom-Json
$srcTime = (Get-ChildItem (Join-Path $materialRoot '_src') -Filter *.py | Measure-Object LastWriteTimeUtc -Maximum).Maximum
$need = @()
foreach ($set in $spec.sets.PSObject.Properties) {
    $entry = $set.Value.files.Medium
    if (-not $entry) { continue }
    foreach ($name in $entry.files) {
        $file = Join-Path $materialRoot "$($entry.dir)/$name"
        if (-not (Test-Path $file) -or (Get-Item $file).LastWriteTimeUtc -lt $srcTime) {
            $need += $set.Name
            break
        }
    }
}
if ($need.Count -gt 0) { throw "PBR preflight: run Materials in pool heavy first. Missing/stale sets: $($need -join ', ')" }
$slotScript = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
pwsh $slotScript -Acquire -Owner gpt-vegetation -StaleHours 1000000 -PollSeconds 10
if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
$importExit = 1
try {
    pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> $Log
    $importExit = $LASTEXITCODE
} finally {
    pwsh $slotScript -Release -Owner gpt-vegetation
    git restore --worktree -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
exit $importExit

