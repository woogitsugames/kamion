param([ValidateSet('before','after')][string]$Stage='before',[string]$OnlyTier='',[string]$OnlyLighting='')
$ErrorActionPreference='Stop'
$root='C:\Users\matma\Documents\Claude\kamion'
$slot=Join-Path $root 'scripts/unity-slot.ps1'
foreach($tier in $(if($OnlyTier){@($OnlyTier)}else{@('Low','High')})) {
 foreach($light in $(if($OnlyLighting){@($OnlyLighting)}else{@('clear','overcast')})) {
  & pwsh $slot -Acquire -Owner gpt-s16
  try {
   if(Test-Path "$root/artifacts/locks/PHONE_RUN"){throw 'PHONE_RUN appeared'}
   & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -Gate3 artifacts/gpt-s16-r3/qa-cameras.json -OutputDir "artifacts/gpt-s16-r3/$Stage/$tier-$light" *> "artifacts/gpt-s16-r3/$Stage-$tier-$light.log"
   if($LASTEXITCODE -ne 0){throw "Render failed: $Stage/$tier-$light"}
  } finally {
   git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
   & pwsh $slot -Release -Owner gpt-s16
  }
  $outer = Get-Content "artifacts/gpt-s16-r3/$Stage-$tier-$light.log" -Raw
  if ($outer -match ' -logFile (.+?) -buildTarget ') {
   Select-String -LiteralPath $Matches[1] -Pattern '\[RQ_PIPELINE\]' | ForEach-Object Line | Select-Object -Unique | Set-Content "artifacts/gpt-s16-r3/$Stage/$tier-$light/pipeline.txt"
  }
  git add -f "artifacts/gpt-s16-r3/$Stage/$tier-$light/pipeline.txt"
  Add-Content artifacts/gpt-s16-r3/STATUS.md "`nZapisano $Stage/$tier-$light; każda kamera w stats.txt. Oględziny pozostają wymagane."
  git add -f artifacts/gpt-s16-r3/STATUS.md "artifacts/gpt-s16-r3/$Stage/$tier-$light/stats.txt"
  git commit -q -m "wip(s16): render putry-shadow $Stage $tier $light"
  & pwsh artifacts/gpt-s16-r3/handoff.ps1 -Step "render.ps1 completed step"
 }
}
