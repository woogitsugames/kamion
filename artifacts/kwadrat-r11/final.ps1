# Kwadrat Park r11 final chain: build_world -> import -> renders -> PlayMode barrier tests -> EditMode.
$root = Resolve-Path "$PSScriptRoot/../.."
Set-Location $root
$lock = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
$logs = "artifacts/kwadrat-r11/logs"
$env:KAMION_BLENDER = 'C:\Users\matma\AppData\Local\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe'
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$logs/build_world_after.log"
"BW EXIT $LASTEXITCODE"
pwsh artifacts/kwadrat-r11/cycle.ps1 -Phase after -TimeFrames 30
while (Test-Path $lock) { Start-Sleep 60 }
pwsh scripts/test.ps1 -Platform PlayMode -Filter "WorldCBarrierTests|DepotBarrierTests" *> "$logs/playmode_barrier.log"
"PLAYMODE EXIT $LASTEXITCODE"
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
while (Test-Path $lock) { Start-Sleep 60 }
pwsh scripts/test.ps1 -Platform EditMode *> "$logs/editmode.log"
"EDITMODE EXIT $LASTEXITCODE"
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
"FINAL DONE"
