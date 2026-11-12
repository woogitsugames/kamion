param(
    [Parameter(Mandatory)]
    [ValidateSet('BuildWorld','BuildMaterials','FarField','GisFile','GisFinal','PhysicsFile','Gate3File','AuditMesh','AuditGround','ScopeGenerated','Compare')]
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
$started = Get-Date -Format o
& pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 2 -StaleHours 100000
if ($LASTEXITCODE -ne 0) { throw 'Heavy slot acquisition failed' }
$acquired = Get-Date -Format o
$code = 1
try {
    switch ($Task) {
        'BuildWorld' { & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c }
        'BuildMaterials' { & uv run --project tools/worldgen python art-source/world/materials/_src/build_all.py }
        'FarField' { & uv run --project tools/worldgen tools/worldgen/streetscape/far_field.py --region bialystok-industrial-c }
        'AuditMesh' { & uv run --project tools/worldgen python "$PSScriptRoot/audit_mesh.py" $Phase }
        'AuditGround' { & uv run --project tools/worldgen python "$PSScriptRoot/audit_ground_alignment.py" $Phase }
        'ScopeGenerated' { & uv run --project tools/worldgen python "$PSScriptRoot/scope_generated.py" }
        'Compare' { & uv run --project tools/worldgen python "$PSScriptRoot/compare.py" }
        'GisFinal' { & uv run --project tools/worldgen python -m pytest tests/gis -q }
        default { & uv run --project tools/worldgen python -m pytest $TestFile -q }
    }
    $code = $LASTEXITCODE
} finally {
    & pwsh $slot -Release -Pool heavy -Owner $owner -StaleHours 100000
    $receiptDir = Join-Path $PSScriptRoot 'job-receipts'
    New-Item -ItemType Directory -Force $receiptDir | Out-Null
    @{task=$Task;test_file=$TestFile;owner=$owner;started=$started;acquired=$acquired;
      finished=(Get-Date -Format o);exit_code=$code;pool='heavy'} | ConvertTo-Json |
        Set-Content (Join-Path $receiptDir ("{0}-{1}.json" -f (Get-Date -Format 'yyyyMMdd-HHmmss-fff'),$Task))
}
exit $code

