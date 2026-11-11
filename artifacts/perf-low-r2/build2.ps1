Set-Location (Split-Path (Split-Path $PSScriptRoot))
if (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { 'LOCKED' | Out-File artifacts/perf-low-r2/build2.done; exit 1 }
pwsh -NoProfile -File scripts/build-android.ps1 -Tier Low *> artifacts/perf-low-r2/build-diag2.log
pwsh -NoProfile -File scripts/build-android.ps1 -Tier Low -Development *> artifacts/perf-low-r2/build-diag2-dev.log
git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
'done' | Out-File artifacts/perf-low-r2/build2.done
