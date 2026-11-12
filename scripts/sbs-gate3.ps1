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
    [switch]$ComposeOnly,
    [string]$Inputs,
    [string]$HeavyLeaseOwner
)
$ErrorActionPreference = 'Stop'
if($RenderOnly -and $ComposeOnly){throw 'RenderOnly and ComposeOnly are mutually exclusive'}
if(($Inputs -or $HeavyLeaseOwner) -and !$ComposeOnly){throw 'Inputs and HeavyLeaseOwner require ComposeOnly'}
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$mainRoot = (& git -C $taskRoot rev-parse --path-format=absolute --git-common-dir).Trim()
$mainRoot = Split-Path $mainRoot -Parent
$slotScript = Join-Path $mainRoot 'scripts/unity-slot.ps1'
$phoneLock = Join-Path $mainRoot 'artifacts/locks/PHONE_RUN'
$output = [IO.Path]::GetFullPath($OutputRoot, $taskRoot)
$region = Join-Path $taskRoot 'Data/Regions/bialystok-industrial-c'
$inputSnapshot = $null
if($Inputs){$inputSnapshot=[IO.Path]::GetFullPath($Inputs,$taskRoot)}
elseif($ComposeOnly){$inputSnapshot=Join-Path $output 'inputs'}
if($ComposeOnly -and !(Test-Path -LiteralPath $inputSnapshot -PathType Container)){throw 'Captured input directory required for ComposeOnly; render or provide Inputs first'}
$sourceInputRoot=if($inputSnapshot){$inputSnapshot}else{$region}
if($inputSnapshot){
    foreach($name in @('sbs_cameras.json','sbs_references.json','world_manifest.json','materials_spec.json')){
        if(!(Test-Path -LiteralPath (Join-Path $inputSnapshot $name) -PathType Leaf)){throw "Incomplete captured inputs: $name"}
    }
    Write-Host "Composing from captured input bytes: $inputSnapshot"
}
$cameraFile = Join-Path $sourceInputRoot 'sbs_cameras.json'
$references = (Get-Content (Join-Path $sourceInputRoot 'sbs_references.json') -Raw | ConvertFrom-Json).references
$loadedReferencesHash = (Get-FileHash -LiteralPath (Join-Path $sourceInputRoot 'sbs_references.json') -Algorithm SHA256).Hash.ToLowerInvariant()
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
function Assert-RenderState($captures,$tier,$light,$renderDir) {
    $ids=@($references.camera)
    if(!$ids.Count -or @($ids | Select-Object -Unique).Count -ne $ids.Count){throw 'Reference roster must be nonempty and unique'}
    if(@($ids | Where-Object {$_ -notmatch '^sbs-[A-Za-z0-9_-]+$'}).Count){throw 'Invalid reference camera ID'}
    $groups=@($references | Group-Object {Get-AspectKey $_.width $_.height})
    if($captures.Count -ne $groups.Count){throw 'Incomplete aspect capture roster'}
    $seen=@();$aspectKeys=@()
    foreach($capture in $captures){
        if($capture.status -ne 'OK' -or $capture.tier -ne $tier -or $capture.lighting -ne $light){throw 'Capture status or render state differs'}
        if($capture.git_sha -notmatch '^[a-fA-F0-9]{40}$' -or $capture.main_sha -notmatch '^[a-fA-F0-9]{40}$'){throw 'Incomplete capture code provenance'}
        if($capture.width -le 0 -or $capture.height -le 0){throw 'Invalid capture dimensions'}
        $key=Get-AspectKey $capture.width $capture.height
        $group=@($groups | Where-Object Name -eq $key)
        if($group.Count -ne 1 -or $key -in $aspectKeys){throw 'Unexpected or duplicate capture aspect'}
        $aspectKeys+=$key
        $first=$group[0].Group[0]
        if($capture.width -ne 1280 -or $capture.height -ne [int](1280*$first.height/$first.width)){throw 'Capture dimensions differ from reference aspect'}
        $expected=@($group[0].Group.camera);$actual=@($capture.cameras)
        if($actual.Count -ne $expected.Count -or @($actual | Select-Object -Unique).Count -ne $actual.Count){throw 'Incomplete or duplicate capture cameras'}
        if(@(Compare-Object $expected $actual).Count){throw 'Capture cameras differ from reference aspect roster'}
        $hashed=@($capture.render_sha256.PSObject.Properties.Name)
        if($hashed.Count -ne $actual.Count -or @(Compare-Object $actual $hashed).Count){throw 'Capture hash roster differs from cameras'}
        $seen+=$actual
        foreach($camera in $actual){
            $path=Join-Path $renderDir ($camera+'.png')
            if(!(Test-Path -LiteralPath $path -PathType Leaf)){throw "Missing captured raw: $camera"}
            $digest=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
            if($capture.render_sha256.$camera -ne $digest){throw "Captured raw hash differs: $camera"}
            $stream=[IO.File]::OpenRead($path)
            try {
                $header=[byte[]]::new(24)
                if($stream.Read($header,0,24) -ne 24 -or [BitConverter]::ToString($header,0,8) -ne '89-50-4E-47-0D-0A-1A-0A' -or [Text.Encoding]::ASCII.GetString($header,12,4) -ne 'IHDR'){throw "Invalid PNG header: $camera"}
                $width=[Net.IPAddress]::NetworkToHostOrder([BitConverter]::ToInt32($header,16))
                $height=[Net.IPAddress]::NetworkToHostOrder([BitConverter]::ToInt32($header,20))
                if($width -ne $capture.width -or $height -ne $capture.height){throw "Raw dimensions differ from capture: $camera"}
            } finally {$stream.Dispose()}
        }
    }
    if($seen.Count -ne $ids.Count -or @($seen | Select-Object -Unique).Count -ne $ids.Count){throw 'Incomplete or duplicate state camera roster'}
    $rawIds=@(Get-ChildItem -LiteralPath $renderDir -Filter '*.png' -File | ForEach-Object BaseName)
    if($rawIds.Count -ne $ids.Count -or @(Compare-Object $ids $rawIds).Count){throw 'Raw PNG roster differs from references'}
}
function Save-EvidenceInputs([switch]$CaptureOnly) {
    $sourceMap=[ordered]@{
        'sbs_cameras.json'=$cameraFile
        'sbs_references.json'=(Join-Path $sourceInputRoot 'sbs_references.json')
        'world_manifest.json'=$(if($inputSnapshot){Join-Path $inputSnapshot 'world_manifest.json'}else{Join-Path $region 'generated/world_manifest.json'})
        'materials_spec.json'=$(if($inputSnapshot){Join-Path $inputSnapshot 'materials_spec.json'}else{Join-Path $taskRoot 'art-source/world/materials/materials_spec.json'})
    }
    $expected=@{'sbs_cameras.json'='cameras_sha256';'sbs_references.json'='references_sha256';'world_manifest.json'='world_manifest_sha256';'materials_spec.json'='materials_spec_sha256'}
    $captureRows=@();$metricRows=@()
    foreach($tier in $Tiers){foreach($light in $Lighting){
        $stateDir=Join-Path $output "renders/$tier-$light"
        $files=@(Get-ChildItem -LiteralPath $stateDir -Filter 'capture-*.json')
        if(!$files.Count){throw 'Cannot snapshot evidence without render captures'}
        $stateCaptures=@(foreach($file in $files){Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json})
        Assert-RenderState $stateCaptures $tier $light $stateDir
        $captureRows+=$stateCaptures
        if(!$CaptureOnly){
            $metricRows+=Get-Content -LiteralPath (Join-Path $output "sheets/$tier-$light/metrics.json") -Raw | ConvertFrom-Json
            if($IncludeDiagnostics){$metricRows+=Get-Content -LiteralPath (Join-Path $output "diagnostics/$tier-$light/metrics.json") -Raw | ConvertFrom-Json}
        }
    }}
    if(@($captureRows.git_sha | Select-Object -Unique).Count -ne 1){throw 'Cannot snapshot mixed code epochs'}
    foreach($name in @('sbs_authored_overrides.json','sbs_extra_references.json','sbs_intrinsics.json','sbs_landmarks.json','sbs_photometry.json','sbs_recognition.json')){
        $source=Join-Path $sourceInputRoot $name
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
$borrowedHeavyLease=$false
$borrowedHeavyRecord=$null
$heavyOwner=(& git -C $taskRoot branch --show-current).Trim()
$heavySlot=Join-Path $mainRoot ('artifacts/locks/heavy-slots/'+($heavyOwner -replace '[^A-Za-z0-9._-]','_')+'.slot')
function Assert-BorrowedHeavyLease {
    if(!(Test-Path -LiteralPath $heavySlot -PathType Leaf)){throw 'Borrowed heavy lease is no longer held'}
    $record=(Get-Content -LiteralPath $heavySlot -Raw).Trim()
    if(($record -split '\s+')[0] -ne $HeavyLeaseOwner){throw 'Borrowed heavy lease owner differs'}
    if($borrowedHeavyRecord -and $record -ne $borrowedHeavyRecord){throw 'Borrowed heavy lease was replaced'}
}
Push-Location $taskRoot
try {
    if($HeavyLeaseOwner){
        if($HeavyLeaseOwner -ne $heavyOwner -or $Tiers.Count -ne 1 -or $Lighting.Count -ne 1){throw 'Borrowed heavy lease requires current branch owner and exactly one render state'}
        Assert-BorrowedHeavyLease
        $borrowedHeavyRecord=(Get-Content -LiteralPath $heavySlot -Raw).Trim()
        Assert-BorrowedHeavyLease
        $borrowedHeavyLease=$true
    } elseif(!$RenderOnly -and (Test-Path -LiteralPath $heavySlot)){
        throw 'Heavy lease already held by this branch; pass HeavyLeaseOwner explicitly for one ComposeOnly state'
    }
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
            $stateLeaseHeld=$false
            if($borrowedHeavyLease){Assert-BorrowedHeavyLease}
            else {
                & pwsh -NoProfile -File $slotScript -Acquire -Pool heavy -Owner $heavyOwner -PollSeconds 7 -StaleHours 87600
                if ($LASTEXITCODE -ne 0) { throw 'Heavy slot acquisition failed' }
                $stateLeaseHeld=$true
            }
            try {
                $composeArgs=@('compose','--renders',$renderDir,'--output',(Join-Path $output "sheets/$tier-$light"))
                if($inputSnapshot){$composeArgs+=@('--inputs',$inputSnapshot)}
                if($Photometry){$composeArgs+=@('--photometry',$Photometry)}
                & uv run --project tools/refs python tools/refs/sbs_gate3.py @composeArgs
                if ($LASTEXITCODE -ne 0) { throw "Incomplete evidence: $tier $light" }
                if($IncludeDiagnostics){
                    $diagnosticArgs=@('compose','--renders',$renderDir,'--output',(Join-Path $output "diagnostics/$tier-$light"),'--include-rejected')
                    if($inputSnapshot){$diagnosticArgs+=@('--inputs',$inputSnapshot)}
                    if($Photometry){$diagnosticArgs+=@('--photometry',$Photometry)}
                    & uv run --project tools/refs python tools/refs/sbs_gate3.py @diagnosticArgs
                    if($LASTEXITCODE -ne 0){throw "Incomplete diagnostic evidence: $tier $light"}
                }
                if($borrowedHeavyLease){Assert-BorrowedHeavyLease}
            } finally {
                if($stateLeaseHeld){& pwsh -NoProfile -File $slotScript -Release -Pool heavy -Owner $heavyOwner}
            }
        }
    }
    Save-EvidenceInputs -CaptureOnly:$RenderOnly
} finally {Pop-Location}
