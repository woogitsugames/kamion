# ADR 0113 final: clean build, gate3 Low A/B, same-APK before (forest off + no PSO warm-up), PSO-only A/B (pso_warm 0).
Set-Location (Split-Path (Split-Path $PSScriptRoot))
$d = $PSScriptRoot
while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
pwsh -NoProfile -File scripts/build-android.ps1 -Tier Low *> "$d/build-final.log"
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
$apk = (Select-String -Path "$d/build-final.log" -Pattern '^APK\s+(\S+\.apk)').Matches[0].Groups[1].Value
"apk=$apk" | Out-File "$d/final.apk.txt"
pwsh -NoProfile -File "$d/gate-final.ps1" -Apk $apk -Tag final
pwsh -NoProfile -File "$d/phone-diag.ps1" -OutTag final -Segment A -Runs "nopso-Low-A=pso_warm=0"
pwsh -NoProfile -File "$d/phone-diag.ps1" -OutTag final -Segment B -Runs "nopso-Low-B=pso_warm=0"
'done' | Out-File "$d/final.done"
