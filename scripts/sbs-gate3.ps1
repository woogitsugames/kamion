<# ADR 0103: render photo-pose cameras at their native aspect ratio; compose attributed evidence. #>
param(
    [string[]]$Tiers = @('Low', 'High'),
    [string[]]$Lighting = @('overcast', 'clear'),
    [switch]$EditMode,
    [switch]$ComposeOnly
)
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$mainRoot = (& git -C $taskRoot rev-parse --path-format=absolute --git-common-dir).Trim()
$mainRoot = Split-Path $mainRoot -Parent
$phoneLock = Join-Path $mainRoot 'artifacts/locks/PHONE_RUN'
$cameraFile = Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/sbs_cameras.json'
$references = (Get-Content (Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/sbs_references.json') -Raw | ConvertFrom-Json).references
$output = Join-Path $taskRoot 'artifacts/sbs-gate3'
function Wait-Phone {
    while (Test-Path -LiteralPath $phoneLock) {
        Write-Host 'PHONE_RUN active; waiting 60 seconds before any Unity start.'
        Start-Sleep -Seconds 60
    }
}
function Restore-UnitySideEffects {
    & git -C $taskRoot restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Push-Location $taskRoot
try {
    if ($EditMode -and !$ComposeOnly) {
        Wait-Phone
        try {
            & pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode
            if ($LASTEXITCODE -ne 0) { throw 'EditMode failed; inspect artifacts/tests and artifacts/logs.' }
        } finally { Restore-UnitySideEffects }
    }
    foreach ($tier in $Tiers) {
        if ($tier -notin @('Low','Medium','High','Ultra')) { throw "Invalid tier: $tier" }
        foreach ($light in $Lighting) {
            if ($light -notin @('overcast','clear','lowsun','dusk')) { throw "Invalid lighting: $light" }
            $renderDir = Join-Path $output "renders/$tier-$light"
            if (!$ComposeOnly) {
                # Camera FOV was converted from horizontal to vertical using this EXACT aspect ratio.
                foreach ($group in ($references | Group-Object { "$($_.width)x$($_.height)" })) {
                    $first = $group.Group[0]
                    $width = 1280
                    $height = [int]($width * $first.height / $first.width)
                    $ids = ($group.Group.camera -join ',')
                    Wait-Phone
                    try {
                        & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -Width $width -Height $height -Gate3 $cameraFile -Cameras $ids -OutputDir $renderDir
                        if ($LASTEXITCODE -ne 0) { throw "Render failed: $tier $light $($group.Name)" }
                        # visual-qa stats.txt is overwritten per invocation; preserve every aspect group.
                        Copy-Item -LiteralPath (Join-Path $renderDir 'stats.txt') -Destination (Join-Path $renderDir "stats-$($group.Name).txt")
                    } finally { Restore-UnitySideEffects }
                }
            }
            & uv run --project tools/refs python tools/refs/sbs_gate3.py compose --renders $renderDir --output (Join-Path $output "sheets/$tier-$light")
            if ($LASTEXITCODE -ne 0) { throw "Incomplete evidence: $tier $light" }
        }
    }
} finally { Pop-Location }
