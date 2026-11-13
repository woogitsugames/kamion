param([ValidateSet('after','before')][string]$Stage='after',[switch]$SkipImport,[string]$Tiers='Low,High',[string]$Lights='clear')
# review-0155: import (policy on = after, policy moved away = before) + render clear Low/High on the same generated world.
$ErrorActionPreference='Stop'
$root='C:\Users\matma\Documents\Claude\kamion'
$wt="$root\.claude\worktrees\review-0155"
Set-Location $wt
$slot="$root\scripts\unity-slot.ps1"
$out="$wt\artifacts\review-0155"
function WaitPhone { while(Test-Path "$root\artifacts\locks\PHONE_RUN"){ Start-Sleep 60 } }
if(-not $SkipImport){
  WaitPhone
  & pwsh $slot -Acquire -Owner review-0155
  try {
    $t=[Diagnostics.Stopwatch]::StartNew()
    & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "$out\import-$Stage.log"
    if($LASTEXITCODE -ne 0){ throw "import failed $Stage" }
    "import $Stage $($t.Elapsed.TotalSeconds) s"
  } finally {
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner review-0155
  }
}
foreach($tier in $Tiers.Split(',')){ foreach($light in $Lights.Split(',')){
  WaitPhone
  & pwsh $slot -Acquire -Owner review-0155
  try {
    & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -Gate3 "$out\cameras.json" -OutputDir "$out\$Stage\$tier-$light" *> "$out\render-$Stage-$tier-$light.log"
    if($LASTEXITCODE -ne 0){ throw "render failed $Stage $tier $light" }
    "render $Stage $tier $light OK"
  } finally {
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner review-0155
  }
}}
"DONE $Stage"
