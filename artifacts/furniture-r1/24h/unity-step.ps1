param(
    [ValidateSet('import','render','sbs-sign','editmode')] [string]$Step,
    [string]$Phase='before',
    [ValidateSet('Low','High')] [string]$Tier='Low',
    [ValidateSet('clear','overcast','dusk')] [string]$Lighting='overcast'
)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../..").Path
Set-Location $root
$ev='artifacts/furniture-r1/24h'
$slotScript='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
if ($Step -eq 'import') {
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
        'render' {
            $scene=if ($Tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
            & pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $Tier -Lighting $Lighting -Gate3 "$ev/cameras.json" -OutputDir "$ev/$Phase/$Tier-$Lighting" *> "$ev/render-$Phase-$Tier-$Lighting.log"
        }
        'editmode' {
            & pwsh scripts/test.ps1 -Platform EditMode *> "$ev/editmode.log"
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
    git add -f "$ev/STATUS.md" "$ev/unity-step.ps1"
    git commit -m "wip(furniture): checkpoint Unity $Step $Phase $Tier $Lighting"
}
