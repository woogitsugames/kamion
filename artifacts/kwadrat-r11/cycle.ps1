# Kwadrat Park r11: import the generated region and render the control cameras (ADR 0071 r11).
# pwsh artifacts/kwadrat-r11/cycle.ps1 -Phase before|after [-SkipImport] [-Combos 'Medium-clear,Medium-overcast,Low-overcast']
param([string]$Phase = 'after', [switch]$SkipImport, [string]$Combos = 'Medium-overcast,Medium-clear,Low-overcast',
      [int]$TimeFrames = 0)
$root = Resolve-Path "$PSScriptRoot/../.."
Set-Location $root
$lock = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
$logs = "artifacts/kwadrat-r11/logs"
New-Item -ItemType Directory -Force $logs | Out-Null
function Wait-Phone { while (Test-Path $lock) { "PHONE_RUN lock - waiting 60 s"; Start-Sleep 60 } }
function Undo-SideEffects {
    git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
    if ((Test-Path game/Assets/Resources) -and -not (Get-ChildItem game/Assets/Resources -Force)) { Remove-Item game/Assets/Resources, game/Assets/Resources.meta -Force -ErrorAction SilentlyContinue }
}
if (-not $SkipImport) {
    Wait-Phone
    pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "$logs/import_$Phase.log"
    "IMPORT $Phase EXIT $LASTEXITCODE"
    Undo-SideEffects
}
$cams = 'g3a_eye_s0012,g3a_eye_s0062,g3a_eye_s0112,g3a_ext34_s0040,kwadrat_park_gate,stretch_05_docks,g3a_eye_s0162,g3a_eye_s0212'
foreach ($c in $Combos.Split(',')) {
    $tier, $light = $c.Split('-')
    Wait-Phone
    $out = "artifacts/kwadrat-r11/$Phase/$c"
    $extra = @()
    if ($TimeFrames -gt 0 -and $tier -eq 'Low') { $extra = @('-TimeFrames', $TimeFrames) }
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -Gate3 Data/Regions/bialystok-industrial-c/gate3_cameras.json -Cameras $cams -OutputDir $out @extra *> "$logs/vqa_${Phase}_$c.log"
    "VQA $Phase $c EXIT $LASTEXITCODE"
    Get-ChildItem $out -Filter *.png -ErrorAction SilentlyContinue | ForEach-Object { magick $_.FullName -resize 960x ($_.FullName -replace '\.png$', '.jpg') 2>$null }
    Undo-SideEffects
}
"CYCLE $Phase DONE"
