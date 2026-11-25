# fields2-s24: import + visual-qa High (clear, overcast) of knyszyn-w and dk65-07; -Phase names the output folder.
param([string]$Phase = 'after', [string]$Tiles = 'knyszyn-w,dk65-07', [string]$Lightings = 'clear,overcast', [switch]$NoImport,
      [string]$CamsOverride = '')
$ErrorActionPreference = 'Continue'
Set-Location C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\fields2-s24
$cams = @{ 'knyszyn-w' = 'dk65_fields_nw,dk65_polna,tykocka_dw671_out,goniadzka_above,route_s0710,route_s1278,ortho_tile';
           'dk65-07'   = 'route_s0144,route_s0433,route_s0721,top_kozince,drive_kozince,drive_wood,ortho_tile' }
function Restore-Side { git checkout -q -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat 2>$null
    if (Test-Path game/Assets/Resources) { if (-not (Get-ChildItem game/Assets/Resources)) { Remove-Item game/Assets/Resources, game/Assets/Resources.meta -Force -ErrorAction SilentlyContinue } } }
while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Owner fields2-s24
try {
    foreach ($t in $Tiles.Split(',')) {
        if (-not $NoImport) {
            pwsh scripts/import-region.ps1 -Region $t -BuildTarget Win64 -MaterialTier High *> "artifacts/fields2-s24/logs/import-$Phase-$t.log"
            "import $Phase $t exit $LASTEXITCODE"; Restore-Side
        }
        foreach ($l in $Lightings.Split(',')) {
            $out = "artifacts/fields2-s24/vqa/$Phase/$t-$l"
            $c = if ($CamsOverride) { $CamsOverride } else { $cams[$t] }
            pwsh scripts/visual-qa.ps1 -Scene "World_${t}_High" -Tier High -Lighting $l -BuildTarget Win64 -Pc -Width 1920 -Height 1080 -Cameras $c -OutputDir $out *> "artifacts/fields2-s24/logs/vqa-$Phase-$t-$l.log"
            "vqa $Phase $t $l exit $LASTEXITCODE"; Restore-Side
        }
    }
} finally { pwsh scripts/unity-slot.ps1 -Release -Owner fields2-s24 }
"DONE $Phase"
