param(
    [ValidateSet('import','render','side-render','sbs-sign','editmode','plinth-probe','sign-probe','shelter-policy-probe','night-rig')] [string]$Step,
    [string]$Phase='before',
    [ValidateSet('Low','High')] [string]$Tier='Low',
    [ValidateSet('clear','overcast','dusk')] [string]$Lighting='overcast',
    [string]$Cameras='',
    [string]$CameraFile='',
    [switch]$OwnedPauseBypass
)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../..").Path
Set-Location $root
$ev='artifacts/furniture-r3/24h'
$slotScript='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
# Owned scheduling marker: serialize the baseline with a separate, explicitly invoked shader probe.
if ($OwnedPauseBypass -and ($Step -ne 'import' -or !(Test-Path "$ev/PAUSE_UNITY"))) {
    throw 'The preview bypass requires its own scheduling marker and an import step'
}
if ($Step -in @('import','render','sbs-sign') -and !$OwnedPauseBypass) {
    while (Test-Path "$ev/PAUSE_UNITY") { Start-Sleep -Seconds 2 }
}
if ($Step -eq 'import') {
    if ($Phase -eq 'before') {
        # Small JSON-only camera preparation, after world generation and before any baseline rendering.
        & uv run --project tools/worldgen python "$ev/prepare_shelter_cameras.py"
        if ($LASTEXITCODE -ne 0) { throw 'Shelter diagnostic camera preparation failed' }
    }
    # import-region can otherwise launch heavy generators implicitly, outside their pool.
    $region='Data/raw/derived/bialystok-industrial-c/world/chunk_0_0.glb'
    if (!(Test-Path $region) -or !(Test-Path Data/Regions/bialystok-industrial-c/route_start.json)) {
        throw 'Prepare world/route products before acquiring Unity; heavy generation needs its own pool'
    }
    $matRoot='art-source/world/materials'
    $spec=Get-Content "$matRoot/materials_spec.json" -Raw | ConvertFrom-Json
    $newest=(Get-ChildItem "$matRoot/_src" -Filter *.py | Measure-Object LastWriteTimeUtc -Maximum).Maximum
    foreach ($set in $spec.sets.PSObject.Properties) {
        $files=$set.Value.files.Medium
        if (!$files) { continue }
        foreach ($name in $files.files) {
            $file=Join-Path $matRoot "$($files.dir)/$name"
            if (!(Test-Path $file) -or (Get-Item $file).LastWriteTimeUtc -lt $newest) {
                throw 'Prepare PBR cache with heavy-step.ps1 -Step pbr; implicit unslotted generation is forbidden'
            }
        }
    }
}
# Never clean another owner's slot, including an old slot. The protocol owns release.
& pwsh $slotScript -Acquire -Owner gpt-furniture -StaleHours 876000 -PollSeconds 10
if ($LASTEXITCODE -ne 0) { throw 'Could not acquire Unity slot' }
$ok=$false
try {
    switch ($Step) {
        'import' {
            & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "$ev/import-$Phase.log"
        }
        {$_ -in @('render','side-render')} {
            $scene=if ($Tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
            $cameraInput=if($CameraFile){$CameraFile}else{"$ev/cameras.json"}
            $renderDir="$ev/$Phase/$Tier-$Lighting"
            $priorStats=@()
            if ($Cameras -and (Test-Path "$renderDir/stats.txt")) {
                $priorStats=@(Get-Content "$renderDir/stats.txt")
                Copy-Item "$renderDir/stats.txt" "$renderDir/stats-before-diagnostic-correction.txt"
            }
            & pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $Tier -Lighting $Lighting -Gate3 $cameraInput -Cameras $Cameras -OutputDir $renderDir *> "$ev/render-$Phase-$Tier-$Lighting.log"
            $renderCode=$LASTEXITCODE
            if ($renderCode -eq 0 -and $priorStats.Count) {
                $ids=$Cameras.Split(',') | ForEach-Object { [regex]::Escape($_) }
                $pattern='^\s*(?:'+($ids -join '|')+')(?::| instanced)'
                $freshStats=@(Get-Content "$renderDir/stats.txt" | Where-Object { $_ -match $pattern })
                @($priorStats | Where-Object { $_ -notmatch $pattern })+$freshStats | Set-Content "$renderDir/stats.txt"
            }
            $global:LASTEXITCODE=$renderCode
        }
        'editmode' {
            & pwsh scripts/test.ps1 -Platform EditMode *> "$ev/editmode.log"
        }
        'plinth-probe' {
            & pwsh scripts/test.ps1 -Platform EditMode -Filter Game.Tests.FurniturePlinthTests *> "$ev/plinth-probe.log"
        }
        'sign-probe' {
            & pwsh scripts/test.ps1 -Platform EditMode -Filter Game.Tests.FurnitureSignTests *> "$ev/sign-probe-$Phase.log"
        }
        'shelter-policy-probe' {
            & pwsh scripts/test.ps1 -Platform EditMode -Filter Game.Tests.FurnitureShelterPolicyTests *> "$ev/shelter-policy-probe-$Phase.log"
        }
        'night-rig' {
            . ./scripts/env.ps1
            $nightOut=[IO.Path]::GetFullPath("$ev/night-rig/$Phase/$Tier",$root)
            New-Item -ItemType Directory -Force $nightOut | Out-Null
            $nightCode=Invoke-UnityBatch -LogFile "$nightOut/unity.log" -BuildTarget Android -Arguments @(
                '-executeMethod','Game.World.Import.FurnitureSignNightQa.Run',
                '-furnitureQaTier',$Tier,'-furnitureQaOutput',$nightOut)
            $global:LASTEXITCODE=[int]$nightCode
        }
        'sbs-sign' {
            $scene=if ($Tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
            $reference=(Get-Content Data/Regions/bialystok-industrial-c/sbs_references.json -Raw | ConvertFrom-Json).references |
                Where-Object camera -eq 'sbs-g3-b-297817221966185'
            $height=[int](1280 * $reference.height / $reference.width)
            & pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $Tier -Lighting $Lighting -Width 1280 -Height $height -Gate3 Data/Regions/bialystok-industrial-c/sbs_cameras.json -Cameras $reference.camera -OutputDir "$ev/$Phase-sbs/$Tier-$Lighting" *> "$ev/sbs-sign-$Phase-$Tier-$Lighting.log"
        }
    }
    if ($LASTEXITCODE -ne 0) { throw "Unity $Step failed: $LASTEXITCODE" }
    $ok=$true
} finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slotScript -Release -Owner gpt-furniture
    Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): Unity $Step $Phase $Tier $Lighting; sukces=$ok. Slot zwolniony. NASTĘPNY KROK: sprawdzić logi i obejrzeć PNG."
    Copy-Item "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md
    git add -f "$ev/STATUS.md" "$ev/unity-step.ps1" artifacts/furniture-r3/STATUS.md
    git commit -m "wip(furniture): checkpoint Unity $Step $Phase $Tier $Lighting"
}


