# vqa.ps1 -Label <name> [-Probe off] [-SkipImport]   renders cams.json (q_far, q_far2) clear+overcast High 1920x1080 Win64
param([Parameter(Mandatory)][string]$Label,[ValidateSet('','off')][string]$Probe='',[switch]$SkipImport,[string]$Cams='q_far,q_far2',[string[]]$Lights=@('clear','overcast'))
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1'
$wt='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\rut-far-s24'
Set-Location $wt
$a="$wt\artifacts\rut-far-s24"
$region='dw671-tykocin-01'; $scene="World_${region}_High"
$shader='game/Assets/_Project/Environment/Shaders/WorldPBR.shader'
$owner='rut-far-s24-u'
& pwsh -NoProfile -File "$wt\scripts\unity-slot.ps1" -Acquire -Pool unity -Owner $owner
try {
  if (-not $SkipImport) {
    & pwsh -NoProfile -File "$wt\scripts\import-region.ps1" -Region $region -Tiers High -BuildTarget Win64
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  }
  $bak="$a\WorldPBR.bak"
  if ($Probe -eq 'off') {
    Copy-Item $shader $bak -Force
    $t=Get-Content $shader -Raw
    $t=$t -replace '(#pragma shader_feature_local _ROADWEAR\r?\n)', "`$1            #define KAMION_RUT_PROBE_OFF 1`n"
    Set-Content $shader $t -NoNewline -Encoding UTF8
  }
  try {
    foreach ($lt in $Lights) {
      & pwsh -NoProfile -File "$wt\scripts\visual-qa.ps1" -Scene $scene -Tier High -Width 1920 -Height 1080 -Lighting $lt -Gate3 "$a\cams.json" -Cameras $Cams -OutputDir "$a\vqa\$Label-$lt" -BuildTarget Win64
      if ($LASTEXITCODE -ne 0) { "visual-qa exit $LASTEXITCODE"; exit $LASTEXITCODE }
    }
  } finally { if (Test-Path $bak) { Copy-Item $bak $shader -Force; Remove-Item $bak -Force } }
} finally {
  & git checkout -- game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat 2>$null
  & pwsh -NoProfile -File "$wt\scripts\unity-slot.ps1" -Release -Pool unity -Owner $owner
}
