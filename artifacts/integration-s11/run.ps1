# s11 integration after regen b2: import, truck/trailer, tests, visual QA Low, clean APK Low.
$ErrorActionPreference = 'Continue'
Set-Location C:\Users\matma\Documents\Claude\kamion
. ./scripts/env.ps1
$L = 'artifacts/integration-s11/logs'; New-Item -ItemType Directory -Force $L | Out-Null
"START $(Get-Date -Format o) $(git rev-parse --short HEAD)"
while (-not (Select-String -Path artifacts/logs/s11-regen-b2.log -Pattern '^END ' -Quiet)) { Start-Sleep 60 }
"REGEN DONE $(Get-Date -Format o)"; Select-String -Path artifacts/logs/s11-regen-b2.log -Pattern 'rc=|passed|failed' | Select-Object -Last 8 | ForEach-Object { $_.Line }
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Priority -PollSeconds 5 -Owner lead-s11-integration
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c; "IMPORT EXIT $LASTEXITCODE"
foreach ($m in 'Game.Editor.Setup.TruckAssetBuilder.BuildBatch','Game.Editor.Setup.TrailerAssetBuilder.BuildBatch','Game.World.Import.WorldTruckInstaller.InstallBatch') {
  $c = Invoke-UnityBatch -LogFile "$PWD/$L/$($m.Split('.')[-2]).log" -Arguments @('-executeMethod', $m); "$m EXIT $c"
}
pwsh scripts/test.ps1 -Platform EditMode; "EDITMODE EXIT $LASTEXITCODE"
pwsh scripts/test.ps1 -Platform PlayMode; "PLAYMODE EXIT $LASTEXITCODE"
foreach ($lt in 'clear','overcast') { pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting $lt -OutputDir "artifacts/integration-s11/vqa/Low-$lt"; "VQA Low-$lt EXIT $LASTEXITCODE" }
git status --porcelain --untracked-files=no
$dirty = git status --porcelain --untracked-files=no -- game/Assets/_Project/Rendering/Settings
if ($dirty) { "RESERIALIZED SETTINGS (not committed yet): $dirty" }
pwsh scripts/build-android.ps1 -Tier Low; "APK EXIT $LASTEXITCODE"
pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner lead-s11-integration
"END $(Get-Date -Format o)"
