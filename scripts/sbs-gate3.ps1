<# ADR 0103: render photo-pose cameras at their native aspect ratio; compose attributed evidence. #>
param(
    [string[]]$Tiers = @('Low', 'High'),
    [string[]]$Lighting = @('overcast', 'clear'),
    [switch]$EditMode,
    [string]$SlotOwner = 'gpt-sbs',
    [string]$OutputRoot = 'artifacts/sbs-gate3',
    [switch]$ComposeOnly
)
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$mainRoot = (& git -C $taskRoot rev-parse --path-format=absolute --git-common-dir).Trim()
$mainRoot = Split-Path $mainRoot -Parent
$slotScript = Join-Path $mainRoot 'scripts/unity-slot.ps1'
$phoneLock = Join-Path $mainRoot 'artifacts/locks/PHONE_RUN'
$cameraFile = Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/sbs_cameras.json'
$references = (Get-Content (Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/sbs_references.json') -Raw | ConvertFrom-Json).references
$output = [IO.Path]::GetFullPath($OutputRoot, $taskRoot)
function Wait-Phone {
    while (Test-Path -LiteralPath $phoneLock) {
        Write-Host 'PHONE_RUN active; waiting 60 seconds before any Unity start.'
        Start-Sleep -Seconds 60
    }
}
function Get-AspectKey($width, $height) {
    $a=[int]$width; $b=[int]$height
    while($b -ne 0) { $remainder=$a % $b; $a=$b; $b=$remainder }
    return "$([int]($width/$a))x$([int]($height/$a))"
}
function Restore-UnitySideEffects {
    & git -C $taskRoot restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Push-Location $taskRoot
try {
    if ($EditMode -and !$ComposeOnly) {
        & pwsh -NoProfile -File $slotScript -Acquire -Owner $SlotOwner -PollSeconds 7 -StaleHours 87600
        if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
        try {
            & pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode
            if ($LASTEXITCODE -ne 0) { throw 'EditMode failed; inspect artifacts/tests and artifacts/logs.' }
        } finally { Restore-UnitySideEffects; & pwsh -NoProfile -File $slotScript -Release -Owner $SlotOwner }
    }
    foreach ($tier in $Tiers) {
        if ($tier -notin @('Low','Medium','High','Ultra')) { throw "Invalid tier: $tier" }
        foreach ($light in $Lighting) {
            if ($light -notin @('overcast','clear','lowsun','dusk')) { throw "Invalid lighting: $light" }
            $renderDir = Join-Path $output "renders/$tier-$light"
            if (!$ComposeOnly) {
                # Camera FOV was converted from horizontal to vertical using this EXACT aspect ratio.
                foreach ($group in ($references | Group-Object { Get-AspectKey $_.width $_.height })) {
                    $first = $group.Group[0]
                    $width = 1280
                    $height = [int]($width * $first.height / $first.width)
                    $ids = ($group.Group.camera -join ',')
                    New-Item -ItemType Directory -Force $renderDir | Out-Null
                    $capture = [ordered]@{
                        captured_at_utc = [DateTime]::UtcNow.ToString('o')
                        git_sha = (& git rev-parse HEAD).Trim()
                        main_sha = (& git merge-base HEAD main).Trim()
                        main_tip_sha = (& git rev-parse main).Trim()
                        world_manifest_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/generated/world_manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant()
                        materials_spec_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskRoot 'art-source/world/materials/materials_spec.json') -Algorithm SHA256).Hash.ToLowerInvariant()
                        cameras_sha256 = (Get-FileHash -LiteralPath $cameraFile -Algorithm SHA256).Hash.ToLowerInvariant()
                        references_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/sbs_references.json') -Algorithm SHA256).Hash.ToLowerInvariant()
                        tier = $tier; lighting = $light; width = $width; height = $height
                        cameras = @($group.Group.camera)
                        status = 'RUNNING'
                    }
                    $captureFile = Join-Path $renderDir "capture-$($group.Name).json"

                    & pwsh -NoProfile -File $slotScript -Acquire -Owner $SlotOwner -PollSeconds 7 -StaleHours 87600
                    if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
                    try {
                        $capture.captured_at_utc = [DateTime]::UtcNow.ToString('o')
                        $capture | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $captureFile -Encoding utf8
                        & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -Width $width -Height $height -Gate3 $cameraFile -Cameras $ids -OutputDir $renderDir
                        if ($LASTEXITCODE -ne 0) { throw "Render failed: $tier $light $($group.Name)" }
                        $capture.render_sha256 = @{}
                        foreach ($camera in $group.Group.camera) {
                            $png = Join-Path $renderDir ($camera + '.png')
                            $capture.render_sha256[$camera] = (Get-FileHash -LiteralPath $png -Algorithm SHA256).Hash.ToLowerInvariant()
                        }
                        $capture.status = 'OK'
                        $capture | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $captureFile -Encoding utf8
                        # visual-qa stats.txt is overwritten per invocation; preserve every aspect group.
                        Copy-Item -LiteralPath (Join-Path $renderDir 'stats.txt') -Destination (Join-Path $renderDir "stats-$($group.Name).txt")
                    } finally { Restore-UnitySideEffects; & pwsh -NoProfile -File $slotScript -Release -Owner $SlotOwner }
                }
            }
            $heavyOwner = (& git branch --show-current).Trim()
            & pwsh -NoProfile -File $slotScript -Acquire -Pool heavy -Owner $heavyOwner -PollSeconds 7 -StaleHours 87600
            if ($LASTEXITCODE -ne 0) { throw 'Heavy slot acquisition failed' }
            try {
                & uv run --project tools/refs python tools/refs/sbs_gate3.py compose --renders $renderDir --output (Join-Path $output "sheets/$tier-$light")
                if ($LASTEXITCODE -ne 0) { throw "Incomplete evidence: $tier $light" }
            } finally { & pwsh -NoProfile -File $slotScript -Release -Pool heavy -Owner $heavyOwner }
        }
    }
} finally { Pop-Location }
