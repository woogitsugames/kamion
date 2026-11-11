$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((git branch --show-current) -ne "gpt-cab-r1") { throw "Run this evidence/WIP script only in the gpt-cab-r1 worktree, never main." }
function Wait-CabUnity {
 while((Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') -or (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\GPT_UNITY_HOLD')) { Start-Sleep -Seconds 60 }
}
foreach($tier in @('Low','High')) {
 $scene=if($tier -eq 'High') {'WorldC_High'} else {'WorldC'}
 foreach($light in @('overcast','clear')) {
  Wait-CabUnity
  & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $light -Cameras 'cab-seat-entry,cab-grain' -OutputDir "artifacts/cab-r1/after-details/$tier-$light"
  $code=$LASTEXITCODE
  git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  if($code -ne 0) { throw 'Detail render failed' }
  Add-Content artifacts/cab-r1/STATUS.md "Inspections captured: $tier $light seat-entry/grain. NEXT COMMAND: pwsh scripts/test.ps1 -Platform EditMode (after detail matrix ends)"
  git add -f artifacts/cab-r1/STATUS.md
  git commit -m "wip(cab): capture $tier $light interior inspection details"
 }
}
Wait-CabUnity
$env:KAMION_ARTIFACTS_DIR=Join-Path (Get-Location).Path 'artifacts/cab-r1/validation'
& pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode
$code=$LASTEXITCODE
git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
exit $code

