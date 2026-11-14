# ADR 0183 evidence: import the region and render the evidence cameras (one Unity at a time, under a unity slot).
param([string]$Steps = 'import,low,high', [string]$Tag = 'r1', [string]$Region = 'bialystok-dojlidy',
      [string]$Cams = 'bollards-close-5m,bollards-detail-2m,bollards-cab-20m,bollards-along-8m,photo_P11-063')
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bollards-0183'
Set-Location $wt
$log = "artifacts/logs/run-unity-$Tag.log"
function Slot([scriptblock]$b) {
    pwsh scripts/unity-slot.ps1 -Acquire -Owner bollards-0183 *>> $log
    try { & $b *>> $log } finally { pwsh scripts/unity-slot.ps1 -Release -Owner bollards-0183 *>> $log }
}
foreach ($s in $Steps.Split(',')) {
    "== $s $(Get-Date -Format HH:mm:ss)" >> $log
    switch ($s) {
        'import' { Slot { pwsh scripts/import-region.ps1 -Region $Region; "import exit=$LASTEXITCODE" } }
        'low'    { Slot { pwsh scripts/visual-qa.ps1 -Scene "World_$Region" -Tier Low -Lighting overcast -Width 1920 -Height 1080 -Gate3 artifacts/bollards-0183/cameras.json -Cameras $Cams -OutputDir "artifacts/bollards-0183/renders/$Tag-low"; "low exit=$LASTEXITCODE" } }
        'high'   { Slot { pwsh scripts/visual-qa.ps1 -Scene "World_${Region}_High" -Tier High -Lighting overcast -Width 1920 -Height 1080 -Gate3 artifacts/bollards-0183/cameras.json -Cameras $Cams -OutputDir "artifacts/bollards-0183/renders/$Tag-high"; "high exit=$LASTEXITCODE" } }
        'editmode' { Slot { pwsh scripts/test.ps1 -Platform EditMode; "editmode exit=$LASTEXITCODE" } }
    }
}
git -C $wt checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>> $log
"DONE $Steps $(Get-Date -Format HH:mm:ss)" >> $log
