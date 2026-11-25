# fields2-s24: visual-qa High of the extra field cameras (cams_<tile>.json via -Gate3), no import.
param([string]$Phase = 'after', [string]$Tiles = 'knyszyn-w,dk65-07', [string]$Lightings = 'clear,overcast', [string]$Only = '')
$ErrorActionPreference = 'Continue'
Set-Location C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\fields2-s24
function Restore-Side { git checkout -q -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat 2>$null
    git checkout -q -- game/Assets/Resources.meta 2>$null }
while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Owner fields2-s24
try {
    foreach ($t in $Tiles.Split(',')) {
        $file = "artifacts/fields2-s24/cams_$t.json"
        $ids = (Get-Content $file -Raw | ConvertFrom-Json).cameras.id
        if ($Only) { $ids = $ids | Where-Object { $_ -match $Only } }
        foreach ($l in $Lightings.Split(',')) {
            $out = "artifacts/fields2-s24/vqa/$Phase/$t-$l-extra"
            pwsh scripts/visual-qa.ps1 -Scene "World_${t}_High" -Tier High -Lighting $l -BuildTarget Win64 -Pc -Width 1920 -Height 1080 -Gate3 $file -Cameras ($ids -join ',') -OutputDir $out *> "artifacts/fields2-s24/logs/vqa-$Phase-$t-$l-extra.log"
            "vqa extra $Phase $t $l exit $LASTEXITCODE"; Restore-Side
        }
    }
} finally { pwsh scripts/unity-slot.ps1 -Release -Owner fields2-s24 }
"DONE extra $Phase"
