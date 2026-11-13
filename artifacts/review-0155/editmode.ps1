# review-0155: reimport with policy (after state) then full EditMode.
$ErrorActionPreference='Stop'
$root='C:\Users\matma\Documents\Claude\kamion'; $wt="$root\.claude\worktrees\review-0155"; Set-Location $wt
$slot="$root\scripts\unity-slot.ps1"; $out="$wt\artifacts\review-0155"
while(Test-Path "$root\artifacts\locks\PHONE_RUN"){ Start-Sleep 60 }
& pwsh $slot -Acquire -Owner review-0155
try {
  & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "$out\import-after2.log"
  if($LASTEXITCODE -ne 0){ throw 'import failed' }
  "reimport OK"
  & pwsh scripts/test.ps1 -Platform EditMode *> "$out\editmode.log"
  "editmode exit $LASTEXITCODE"
} finally {
  git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  & pwsh $slot -Release -Owner review-0155
}
