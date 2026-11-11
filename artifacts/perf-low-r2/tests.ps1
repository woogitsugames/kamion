Set-Location (Split-Path (Split-Path $PSScriptRoot))
while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode *> artifacts/perf-low-r2/test-editmode.log
pwsh -NoProfile -File scripts/test.ps1 -Platform PlayMode *> artifacts/perf-low-r2/test-playmode.log
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
'done' | Out-File artifacts/perf-low-r2/tests.done
