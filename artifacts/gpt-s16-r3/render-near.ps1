$ErrorActionPreference='Stop'
$root='C:\Users\matma\Documents\Claude\kamion'
$slot=Join-Path $root 'scripts/unity-slot.ps1'
foreach($tier in @('Low','High')) {
 $dest="artifacts/gpt-s16-r3/final-near/$tier-clear"
 New-Item -ItemType Directory -Path $dest -Force | Out-Null
 & pwsh $slot -Acquire -Owner gpt-s16
 try {
  if(Test-Path "$root/artifacts/locks/PHONE_RUN"){throw 'PHONE_RUN appeared'}
  & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting clear -Gate3 artifacts/gpt-s16-r3/diagnostic-cameras.json -Cameras putry-island-near -OutputDir $dest *> "$dest.log"
  if($LASTEXITCODE -ne 0){throw "Near render failed: $tier"}
 } finally {
  git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  & pwsh $slot -Release -Owner gpt-s16
 }
 git add -f "$dest/stats.txt" "$dest.log"
 git commit -q -m "wip(s16): verify production policy in close island $tier view"
}
