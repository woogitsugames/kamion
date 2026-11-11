$ErrorActionPreference='Stop'
Set-Location "$PSScriptRoot/../.."
function Check-PhoneLock {
    while (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') { Start-Sleep -Seconds 45 }
}
function Save-Progress([string]$Text,[string]$Commit) {
    Add-Content artifacts/megascans-r1/STATUS.md "`n$Text"
    git add -f artifacts/megascans-r1/STATUS.md
    git commit -m $Commit
}
Check-PhoneLock
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> artifacts/megascans-r1/round4-import.log
if($LASTEXITCODE -ne 0){throw 'Final import failed'}
New-Item -ItemType Directory -Force artifacts/megascans-r1/round4 | Out-Null
Copy-Item artifacts/world/bialystok-industrial-c-import.json artifacts/megascans-r1/round4/import-report.json
Save-Progress '- Krok25: import rundy4 Low+High OK; albedo roślin skalibrowane, fotograficzna baza trawy zachowuje WorldPBR. NASTĘPNY: pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -OutputDir artifacts/megascans-r1/round4/Low-overcast' 'wip(megascans): import final calibrated licensed materials'
foreach($tier in @('Low','High')){
    Check-PhoneLock
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting overcast -OutputDir "artifacts/megascans-r1/round4/$tier-overcast" *> "artifacts/megascans-r1/round4-$tier.log"
    if($LASTEXITCODE -ne 0){throw "Final $tier QA failed"}
    Save-Progress "- Krok26$tier`: 28 PNG rundy4 $tier zapisane. NASTĘPNY: pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting overcast -OutputDir artifacts/megascans-r1/round4/High-overcast; następnie kamery detali." "wip(megascans): capture final $tier fixed cameras"
    Check-PhoneLock
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting overcast -Gate3 artifacts/megascans-r1/detail-cameras.json -Cameras 'megascans_eye_manhole_s0928,megascans_eye_gully_s0482,megascans_eye_verge_s0523' -OutputDir "artifacts/megascans-r1/detail-after/$tier-overcast" *> "artifacts/megascans-r1/detail-after-$tier.log"
    if($LASTEXITCODE -ne 0){throw "Final detail $tier failed"}
}
Check-PhoneLock
pwsh artifacts/megascans-r1/run-camera-proof.ps1 -Stage after *> artifacts/megascans-r1/detail-after-proof.log
if($LASTEXITCODE -ne 0){throw 'Final camera raycast failed'}
Check-PhoneLock
pwsh scripts/test.ps1 -Platform EditMode *> artifacts/megascans-r1/editmode-round4.log
$nativeTestExit=$LASTEXITCODE
Set-Content artifacts/megascans-r1/editmode-round4-exit.txt $nativeTestExit
uv run --project tools/worldgen python artifacts/megascans-r1/compare.py round4 *> artifacts/megascans-r1/round4-comparison.log
uv run --project tools/worldgen python artifacts/megascans-r1/make-montages.py round4
Save-Progress "- Krok27: końcowe56PNG+6detali oraz raycast gotowe; EditMode wrapper exit=$nativeTestExit (sprawdzić XML). NASTĘPNY: obejrzeć artifacts/megascans-r1/round4/Low-contact.jpg i High-contact.jpg, przeprowadzić niezależną krytykę." 'wip(megascans): record final camera and test evidence'
