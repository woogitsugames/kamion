# s12 integration b: after GPT batch B merges. regen -> commit generated -> import -> truck -> tests -> vqa Low/High -> SBS Low (+diag) -> clean APK Low.
$ErrorActionPreference = 'Continue'
Set-Location C:\Users\matma\Documents\Claude\kamion
. ./scripts/env.ps1
$L = 'artifacts/integration-s12/logs-b'; New-Item -ItemType Directory -Force $L | Out-Null
"START $(Get-Date -Format o) $(git rev-parse --short HEAD)"
bash artifacts/integration-s12/regen.sh b *> artifacts/logs/s12-regen-b.log
"REGEN DONE $(Get-Date -Format o)"; Select-String -Path artifacts/logs/s12-regen-b.log -Pattern 'rc=|passed|failed' | Select-Object -Last 8 | ForEach-Object { $_.Line }
git add Data/Regions/bialystok-industrial-c/generated Data/SourceManifests art-source/world/props art-source/world/materials 2>$null
git commit -qm "chore(world): regenerate after GPT batch B merges (s12 regen b)`n`nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"; "GENCOMMIT $(git rev-parse --short HEAD)"
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Priority -PollSeconds 5 -Owner lead-s12-integration-b
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c; "IMPORT EXIT $LASTEXITCODE"
foreach ($m in 'Game.Editor.Setup.TruckAssetBuilder.BuildBatch','Game.Editor.Setup.TrailerAssetBuilder.BuildBatch','Game.World.Import.WorldTruckInstaller.InstallBatch') {
  $c = Invoke-UnityBatch -LogFile "$PWD/$L/$($m.Split('.')[-2]).log" -Arguments @('-executeMethod', $m); "$m EXIT $c"
}
pwsh scripts/test.ps1 -Platform EditMode; "EDITMODE EXIT $LASTEXITCODE"
pwsh scripts/test.ps1 -Platform PlayMode; "PLAYMODE EXIT $LASTEXITCODE"
foreach ($tr in 'Low','High') { foreach ($lt in 'clear','overcast') { pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tr -Lighting $lt -OutputDir "artifacts/integration-s12/vqa-b/$tr-$lt"; "VQA $tr-$lt EXIT $LASTEXITCODE" } }
pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner lead-s12-integration-b
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset 2>$null
pwsh scripts/sbs-gate3.ps1 -Tiers Low -Lighting overcast,clear -IncludeDiagnostics -SlotOwner lead-s12-sbs -OutputRoot artifacts/integration-s12/sbs-b; "SBS EXIT $LASTEXITCODE"
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset 2>$null
$dirty = git status --porcelain --untracked-files=no -- game Data art-source tools
if ($dirty) { "DIRTY BEFORE APK: $dirty" }
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Priority -PollSeconds 5 -Owner lead-s12-apk
pwsh scripts/build-android.ps1 -Tier Low; "APK EXIT $LASTEXITCODE"
pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner lead-s12-apk
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset 2>$null
"END $(Get-Date -Format o)"
