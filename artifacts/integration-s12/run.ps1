# s12 integration after regen a (s11 merges + GPT batch A): import, truck/trailer, tests, visual QA Low, clean APK Low.
$ErrorActionPreference = 'Continue'
Set-Location C:\Users\matma\Documents\Claude\kamion
. ./scripts/env.ps1
$L = 'artifacts/integration-s12/logs'; New-Item -ItemType Directory -Force $L | Out-Null
"START $(Get-Date -Format o) $(git rev-parse --short HEAD)"
while (-not (Select-String -Path artifacts/logs/s12-regen-a.log -Pattern '^END ' -Quiet)) { Start-Sleep 60 }
"REGEN DONE $(Get-Date -Format o)"; Select-String -Path artifacts/logs/s12-regen-a.log -Pattern 'rc=|passed|failed' | Select-Object -Last 8 | ForEach-Object { $_.Line }
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Priority -PollSeconds 5 -Owner lead-s12-integration
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c; "IMPORT EXIT $LASTEXITCODE"
foreach ($m in 'Game.Editor.Setup.TruckAssetBuilder.BuildBatch','Game.Editor.Setup.TrailerAssetBuilder.BuildBatch','Game.World.Import.WorldTruckInstaller.InstallBatch') {
  $c = Invoke-UnityBatch -LogFile "$PWD/$L/$($m.Split('.')[-2]).log" -Arguments @('-executeMethod', $m); "$m EXIT $c"
}
pwsh scripts/test.ps1 -Platform EditMode; "EDITMODE EXIT $LASTEXITCODE"
pwsh scripts/test.ps1 -Platform PlayMode; "PLAYMODE EXIT $LASTEXITCODE"
foreach ($tr in 'Low','High') { foreach ($lt in 'clear','overcast') { pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tr -Lighting $lt -OutputDir "artifacts/integration-s12/vqa/$tr-$lt"; "VQA $tr-$lt EXIT $LASTEXITCODE" } }
git status --porcelain --untracked-files=no
$dirty = git status --porcelain --untracked-files=no -- game/Assets/_Project/Rendering/Settings
if ($dirty) { "RESERIALIZED SETTINGS (not committed yet): $dirty" }
pwsh scripts/build-android.ps1 -Tier Low; "APK EXIT $LASTEXITCODE"
pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner lead-s12-integration
"END $(Get-Date -Format o)"
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat 2>$null
