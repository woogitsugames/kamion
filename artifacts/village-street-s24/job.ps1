# village-street-s24 (ADR 0349): import + visual-qa High clear (PC tier) of dw671-tykocin-03 / -04, and the rebuild.
#   pwsh artifacts/village-street-s24/job.ps1 -Phase before            # import the derived tiles as they are + renders
#   pwsh artifacts/village-street-s24/job.ps1 -Phase rebuild           # build_world --context (heavy slot)
#   pwsh artifacts/village-street-s24/job.ps1 -Phase after             # import + renders
param([Parameter(Mandatory)][ValidateSet('before', 'rebuild', 'after')][string]$Phase,
      [string]$Tiles = 'dw671-tykocin-03,dw671-tykocin-04', [switch]$NoImport)
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\agent-a4f5b23b7d6760aa7'
Set-Location $wt
$owner = 'village-street-s24'
$a = 'artifacts/village-street-s24'
New-Item -ItemType Directory -Force "$a/logs" | Out-Null
$cams = @{ 'dw671-tykocin-03' = 'vs_cab_t2590,vs_street_left_t2590,vs_street_right_t2590,vs_above_t2590,vs_cab_koscielne,vs_cab_village_start,vs_cab_seam_04,route_s1409,route_s1722';
           'dw671-tykocin-04' = 'vs_cab_seam_03,vs_cab_village_end,vs_above_village_end' }
# cab view of the real truck (dash, mirrors) at the pose of frame t2590: E,N,heading
$pose = @{ 'dw671-tykocin-03' = '205.99,-600.21,201.9' }
function Restore-Side {
    git checkout -q -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat 2>$null
    git checkout -q -- game/Assets/Resources.meta 2>$null
}
while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
if ($Phase -eq 'rebuild') {
    pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner
    try {
        foreach ($t in $Tiles.Split(',')) {
            uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $t --context *> "$a/logs/build-$t.log"
            "build_world $t exit $LASTEXITCODE"
        }
    } finally { pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner }
    "DONE rebuild"
    exit 0
}
pwsh scripts/unity-slot.ps1 -Acquire -Owner $owner
try {
    foreach ($t in $Tiles.Split(',')) {
        if (-not $NoImport) {
            pwsh scripts/import-region.ps1 -Region $t -BuildTarget Win64 -Tiers High -MaterialTier High *> "$a/logs/import-$Phase-$t.log"
            "import $Phase $t exit $LASTEXITCODE"; Restore-Side
        }
        $out = "$a/vqa/$Phase/$t"
        pwsh scripts/visual-qa.ps1 -Scene "World_${t}_High" -Tier High -Lighting clear -BuildTarget Win64 -Pc -Width 1920 -Height 1080 `
            -Gate3 "$a/cams_$t.json" -Cameras $cams[$t] -OutputDir $out *> "$a/logs/vqa-$Phase-$t.log"
        "vqa $Phase $t exit $LASTEXITCODE"; Restore-Side
        if ($pose[$t]) {
            pwsh scripts/visual-qa.ps1 -Scene "World_${t}_High" -Tier High -Lighting clear -BuildTarget Win64 -Pc -Width 1920 -Height 1080 `
                -TruckPose $pose[$t] -Cameras 'cab-view-b-fov70' -OutputDir "$out-cab" *> "$a/logs/vqa-$Phase-$t-cab.log"
            "vqa cab $Phase $t exit $LASTEXITCODE"; Restore-Side
        }
    }
} finally { pwsh scripts/unity-slot.ps1 -Release -Owner $owner }
"DONE $Phase"
