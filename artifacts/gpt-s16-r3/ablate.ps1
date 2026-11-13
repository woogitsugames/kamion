param([string]$OnlyTier='', [string]$OnlyMode='')
$ErrorActionPreference='Stop'
$root='C:\Users\matma\Documents\Claude\kamion'
$slot=Join-Path $root 'scripts/unity-slot.ps1'
$modes=@{ 'zero-bias'='rq_shadowbias=0,rq_shadownormal=0'; 'baked-only'='rq_shadow=0'; 'no-baked'='rq_worldsun=0'; 'no-shadows'='rq_shadow=0,rq_worldsun=0' }
$cameras='sbs-g3-a-2818555625124739,sbs-g3-a-3970163613102941,putry-island-1,putry-island-2'
foreach($tier in $(if($OnlyTier){@($OnlyTier)}else{@('Low','High')})) {
 foreach($mode in $(if($OnlyMode){@($OnlyMode)}else{@('zero-bias','baked-only','no-baked','no-shadows')})) {
  $dest="artifacts/gpt-s16-r3/ablations/$tier-$mode"
  & pwsh $slot -Acquire -Owner gpt-s16
  try {
   if(Test-Path "$root/artifacts/locks/PHONE_RUN"){throw 'PHONE_RUN appeared'}
   & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting clear -Gate3 artifacts/gpt-s16-r3/qa-cameras.json -Cameras $cameras -Rq $modes[$mode] -OutputDir $dest *> "$dest.log"
   if($LASTEXITCODE -ne 0){throw "Ablation failed: $tier/$mode"}
  } finally {
   git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
   & pwsh $slot -Release -Owner gpt-s16
  }
  $outer=Get-Content "$dest.log" -Raw
  if($outer -match ' -logFile (.+?) -buildTarget ') {
   Select-String -LiteralPath $Matches[1] -Pattern '\[RQ_PIPELINE\]' | ForEach-Object Line | Select-Object -Unique | Set-Content "$dest/pipeline.txt"
  }
  Add-Content artifacts/gpt-s16-r3/STATUS.md "`nZapisano ablacją $tier/$mode ($($modes[$mode])). To diagnostyka, nie wynik produkcyjnego after. NASTĘPNY KROK: obejrzeć cztery kadry i porównać z bazą."
  git add -f artifacts/gpt-s16-r3/STATUS.md "$dest/stats.txt" "$dest/pipeline.txt" "$dest.log"
  git commit -q -m "wip(s16): diagnose Putry shadow $tier $mode"
 }
}
