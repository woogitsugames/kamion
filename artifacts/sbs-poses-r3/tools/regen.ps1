# ADR 0143: regenerate the world in this worktree (heavy slot) and import it (Unity slot); restores Unity side effects.
$ErrorActionPreference='Stop'
$w='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\sbs-poses-r3'; $m='C:\Users\matma\Documents\Claude\kamion'
Set-Location $w
& pwsh -NoProfile -File "$m/scripts/unity-slot.ps1" -Acquire -Pool heavy -Owner claude-sbs-poses-r3 -PollSeconds 15
try { & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c; if($LASTEXITCODE -ne 0){throw "build_world $LASTEXITCODE"} }
finally { & pwsh -NoProfile -File "$m/scripts/unity-slot.ps1" -Release -Pool heavy -Owner claude-sbs-poses-r3 }
"BUILD_WORLD_DONE $(Get-Date -Format HH:mm)"
while(Test-Path "$m\artifacts\locks\PHONE_RUN"){Start-Sleep 60}
& pwsh -NoProfile -File "$m/scripts/unity-slot.ps1" -Acquire -Owner claude-sbs-poses-r3 -PollSeconds 15
try { & pwsh -NoProfile -File scripts/import-region.ps1 -Region bialystok-industrial-c; if($LASTEXITCODE -ne 0){throw "import $LASTEXITCODE"} }
finally {
  & git -C $w checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
  & pwsh -NoProfile -File "$m/scripts/unity-slot.ps1" -Release -Owner claude-sbs-poses-r3 }
"IMPORT_DONE $(Get-Date -Format HH:mm)"
