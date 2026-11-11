param(
    [Parameter(Mandatory)]
    [ValidateSet('BuildWorld','BuildMaterials','GisFile','GisFinal','PhysicsFile','Gate3File','AuditMesh','Compare')]
    [string]$Task,
    [string]$TestFile,
    [switch]$AtRoundEnd,
    [ValidateSet('before','after','prototype')] [string]$Phase = 'after'
)
$ErrorActionPreference = 'Stop'
$edgeRoot = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $edgeRoot
$owner = (git branch --show-current).Trim()
if ($owner -notmatch '^gpt-edge-r\d+$') { throw "Unexpected branch: $owner" }
if ($Task -eq 'GisFinal' -and -not $AtRoundEnd) { throw 'Full GIS is allowed only at round end.' }
if ($Task -in @('GisFile','PhysicsFile','Gate3File')) {
    $group = @{GisFile='gis';PhysicsFile='physics';Gate3File='gate3'}[$Task]
    if ($TestFile -notmatch "^tests/$group/[^/\\]+\.py$" -or -not (Test-Path -LiteralPath $TestFile)) {
        throw 'Provide exactly one test file in the selected test group.'
    }
}
# Use the current central protocol, even before the next round merges updated main.
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh $slot -Acquire -Pool heavy -Owner $owner
if ($LASTEXITCODE -ne 0) { throw 'Heavy slot acquisition failed' }
$code = 1
try {
    switch ($Task) {
        'BuildWorld' { & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c }
        'BuildMaterials' { & uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py }
        'AuditMesh' { & uv run --project tools/worldgen python "$PSScriptRoot/audit_mesh.py" $Phase }
        'Compare' { & uv run --project tools/worldgen python "$PSScriptRoot/compare.py" }
        'GisFinal' { & uv run --project tools/worldgen python -m pytest tests/gis -q }
        default { & uv run --project tools/worldgen python -m pytest $TestFile -q }
    }
    $code = $LASTEXITCODE
} finally {
    & pwsh $slot -Release -Pool heavy -Owner $owner
}
exit $code
