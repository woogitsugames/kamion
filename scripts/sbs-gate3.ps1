<# ADR 0103: render photo-pose cameras at their native aspect ratio; compose attributed evidence. #>
param(
    [string[]]$Tiers = @('Low', 'High'),
    [string[]]$Lighting = @('overcast', 'clear'),
    [switch]$EditMode,
    [string]$SlotOwner = 'gpt-sbs',
    [string]$OutputRoot = 'artifacts/sbs-gate3',
    [switch]$RenderOnly,
    [switch]$IncludeDiagnostics,
    [string]$Photometry,
    [switch]$ComposeOnly
)
$ErrorActionPreference = 'Stop'
if($RenderOnly -and $ComposeOnly){throw 'RenderOnly and ComposeOnly are mutually exclusive'}
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$mainRoot = (& git -C $taskRoot rev-parse --path-format=absolute --git-common-dir).Trim()
$mainRoot = Split-Path $mainRoot -Parent
$slotScript = Join-Path $mainRoot 'scripts/unity-slot.ps1'
$phoneLock = Join-Path $mainRoot 'artifacts/locks/PHONE_RUN'
$cameraFile = Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/sbs_cameras.json'
$references = (Get-Content (Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/sbs_references.json') -Raw | ConvertFrom-Json).references
$loadedReferencesHash = (Get-FileHash -LiteralPath (Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/sbs_references.json') -Algorithm SHA256).Hash.ToLowerInvariant()
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
function Save-EvidenceInputs {
    $sourceMap=[ordered]@{
        'sbs_cameras.json'=$cameraFile
        'sbs_references.json'=(Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/sbs_references.json')
        'world_manifest.json'=(Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/generated/world_manifest.json')
        'materials_spec.json'=(Join-Path $taskRoot 'art-source/world/materials/materials_spec.json')
    }
    $expected=@{'sbs_cameras.json'='cameras_sha256';'sbs_references.json'='references_sha256';'world_manifest.json'='world_manifest_sha256';'materials_spec.json'='materials_spec_sha256'}
    $captureRows=@();$metricRows=@()
    foreach($tier in $Tiers){foreach($light in $Lighting){
        $files=@(Get-ChildItem -LiteralPath (Join-Path $output "renders/$tier-$light") -Filter 'capture-*.json')
        if(!$files.Count){throw 'Cannot snapshot evidence without render captures'}
        foreach($file in $files){$captureRows+=Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json}
        $metricRows+=Get-Content -LiteralPath (Join-Path $output "sheets/$tier-$light/metrics.json") -Raw | ConvertFrom-Json
        if($IncludeDiagnostics){$metricRows+=Get-Content -LiteralPath (Join-Path $output "diagnostics/$tier-$light/metrics.json") -Raw | ConvertFrom-Json}
    }}
    if(@($captureRows.git_sha | Select-Object -Unique).Count -ne 1){throw 'Cannot snapshot mixed code epochs'}
    foreach($name in @('sbs_authored_overrides.json','sbs_extra_references.json','sbs_intrinsics.json','sbs_landmarks.json','sbs_photometry.json','sbs_recognition.json')){
        $source=Join-Path $taskRoot ('Data/Regions/bialystok-industrial-c/'+$name)
        if(Test-Path -LiteralPath $source){$sourceMap[$name]=$source}
    }
    if($Photometry){$sourceMap['sbs_photometry.json']=[IO.Path]::GetFullPath($Photometry,$taskRoot)}
    $nonce=[Guid]::NewGuid().ToString('N')
    $staging=Join-Path $output ('.inputs-'+$nonce)
    New-Item -ItemType Directory -Force $staging | Out-Null
    foreach($key in $sourceMap.Keys){Copy-Item -LiteralPath $sourceMap[$key] -Destination (Join-Path $staging $key)}
    # Validate copied bytes, never a source reread before Copy-Item.
    foreach($key in $expected.Keys){
        $copied=(Get-FileHash -LiteralPath (Join-Path $staging $key) -Algorithm SHA256).Hash.ToLowerInvariant()
        foreach($capture in $captureRows){
            if($capture.status -ne 'OK' -or $capture.($expected[$key]) -ne $copied){throw "Snapshot differs from captures: $key"}
        }
    }
    foreach($binding in @(@('sbs_photometry.json','photometry_sha256'),@('sbs_landmarks.json','landmarks_sha256'))){
        $file=Join-Path $staging $binding[0]
        $copied=if(Test-Path -LiteralPath $file){(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()}else{$null}
        foreach($metric in $metricRows){if($metric.($binding[1]) -ne $copied){throw "Snapshot annotations differ from composed metrics: $($binding[0])"}}
    }
    $stagingZip=Join-Path $output ('.inputs-'+$nonce+'.zip')
    Compress-Archive -LiteralPath @($sourceMap.Keys | ForEach-Object {Join-Path $staging $_}) -DestinationPath $stagingZip
    $snapshot=Join-Path $output 'inputs'
    # All directory moves stay inside the explicitly owned OutputRoot; preserve prior inputs.
    $archive=Join-Path $output ('inputs-history/'+$nonce)
    $outputPrefix=[IO.Path]::GetFullPath($output).TrimEnd([IO.Path]::DirectorySeparatorChar)+[IO.Path]::DirectorySeparatorChar
    foreach($path in @($staging,$snapshot,$archive)){
        if(![IO.Path]::GetFullPath($path).StartsWith($outputPrefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Snapshot move outside OutputRoot'}
    }
    if(Test-Path -LiteralPath $snapshot){
        New-Item -ItemType Directory -Force (Split-Path $archive -Parent) | Out-Null
        Move-Item -LiteralPath $snapshot -Destination $archive
    }
    Move-Item -LiteralPath $staging -Destination $snapshot
    Move-Item -LiteralPath $stagingZip -Destination (Join-Path $output 'inputs.zip') -Force
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
                    $captureFile = Join-Path $renderDir "capture-$($group.Name).json"

                    & pwsh -NoProfile -File $slotScript -Acquire -Owner $SlotOwner -PollSeconds 7 -StaleHours 87600
                    if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
                    try {
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
                        if ($capture.references_sha256 -ne $loadedReferencesHash) { throw 'Reference grouping changed while waiting; restart SBS' }
                        $capture.captured_at_utc = [DateTime]::UtcNow.ToString('o')
                        $capture | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $captureFile -Encoding utf8
                        & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -Width $width -Height $height -Gate3 $cameraFile -Cameras $ids -OutputDir $renderDir
                        if ($LASTEXITCODE -ne 0) { throw "Render failed: $tier $light $($group.Name)" }
                        $after = [ordered]@{
                            git_sha = (& git rev-parse HEAD).Trim()
                            cameras_sha256 = (Get-FileHash -LiteralPath $cameraFile -Algorithm SHA256).Hash.ToLowerInvariant()
                            references_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/sbs_references.json') -Algorithm SHA256).Hash.ToLowerInvariant()
                            world_manifest_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c/generated/world_manifest.json') -Algorithm SHA256).Hash.ToLowerInvariant()
                            materials_spec_sha256 = (Get-FileHash -LiteralPath (Join-Path $taskRoot 'art-source/world/materials/materials_spec.json') -Algorithm SHA256).Hash.ToLowerInvariant()
                        }
                        foreach ($key in $after.Keys) {
                            if ($after[$key] -ne $capture[$key]) {
                                $capture.status = 'STALE_INPUTS'
                                $capture | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $captureFile -Encoding utf8
                                throw "Render inputs changed during capture: $key"
                            }
                        }
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
            if($RenderOnly){continue}
            $heavyOwner = (& git branch --show-current).Trim()
            & pwsh -NoProfile -File $slotScript -Acquire -Pool heavy -Owner $heavyOwner -PollSeconds 7 -StaleHours 87600
            if ($LASTEXITCODE -ne 0) { throw 'Heavy slot acquisition failed' }
            try {
                $composeArgs=@('compose','--renders',$renderDir,'--output',(Join-Path $output "sheets/$tier-$light"))
                if($Photometry){$composeArgs+=@('--photometry',$Photometry)}
                & uv run --project tools/refs python tools/refs/sbs_gate3.py @composeArgs
                if ($LASTEXITCODE -ne 0) { throw "Incomplete evidence: $tier $light" }
                if($IncludeDiagnostics){
                    $diagnosticArgs=@('compose','--renders',$renderDir,'--output',(Join-Path $output "diagnostics/$tier-$light"),'--include-rejected')
                    if($Photometry){$diagnosticArgs+=@('--photometry',$Photometry)}
                    & uv run --project tools/refs python tools/refs/sbs_gate3.py @diagnosticArgs
                    if($LASTEXITCODE -ne 0){throw "Incomplete diagnostic evidence: $tier $light"}
                }
            } finally { & pwsh -NoProfile -File $slotScript -Release -Pool heavy -Owner $heavyOwner }
        }
    }
    if(!$RenderOnly){Save-EvidenceInputs}
} finally { Pop-Location }
