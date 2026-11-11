param([ValidateSet('before','after')] [string]$Stage='before')
$ErrorActionPreference='Stop'
$repo=(Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $repo
$phoneLock='C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
foreach($tier in @('Low','High')) {
  foreach($light in @('overcast','clear')) {
    while(Test-Path $phoneLock) { Write-Output "PHONE_RUN: waiting before $Stage $tier $light"; Start-Sleep -Seconds 60 }
    & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -Cameras 'cab-driver,cab-dash,cab-left,cab-right,cab-mirrors-left,cab-mirrors-right,cab-mirror-front' -OutputDir "artifacts/cab-r1/$Stage/$tier-$light"
    if($LASTEXITCODE -ne 0) { throw "Render failed: $Stage $tier $light" }
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    Add-Content artifacts/cab-r1/STATUS.md "Rendered $Stage $tier $light. NEXT: continue audit matrix / inspect artifacts/cab-r1/$Stage"
    git add -f artifacts/cab-r1/STATUS.md
    git commit -m "wip(cab): render $Stage $tier $light"
  }
}
