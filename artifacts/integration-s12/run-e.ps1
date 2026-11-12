# s12 integration e: after batch D + 0126 (+0124) + SBS pose promotion. regen -> commit generated -> import -> truck -> tests -> vqa Low/High -> SBS Low (+diag) -> clean APK Low.
$ErrorActionPreference = 'Continue'
Set-Location C:\Users\matma\Documents\Claude\kamion
. ./scripts/env.ps1
function Revert-Side { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null }
$L = 'artifacts/integration-s12/logs-e'; New-Item -ItemType Directory -Force $L | Out-Null
"START $(Get-Date -Format o) $(git rev-parse --short HEAD)"
bash artifacts/integration-s12/regen.sh e *> artifacts/logs/s12-regen-e.log
"REGEN DONE $(Get-Date -Format o)"; Select-String -Path artifacts/logs/s12-regen-e.log -Pattern 'rc=|passed|failed' | Select-Object -Last 8 | ForEach-Object { $_.Line }
git add Data/Regions/bialystok-industrial-c/generated Data/SourceManifests art-source/world/props art-source/world/materials art-source/world/landmarks 2>$null
git commit -qm "chore(world): regenerate after batch D + 0126 + 0124 + SBS poses (s12 regen e)`n`nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"; "GENCOMMIT $(git rev-parse --short HEAD)"
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Priority -PollSeconds 5 -Owner lead-s12-integration-e
pwsh scripts/import-region.ps1 -Region bialystok-industrial-c; "IMPORT EXIT $LASTEXITCODE"
foreach ($m in 'Game.Editor.Setup.TruckAssetBuilder.BuildBatch','Game.Editor.Setup.TrailerAssetBuilder.BuildBatch','Game.World.Import.WorldTruckInstaller.InstallBatch') {
  $c = Invoke-UnityBatch -LogFile "$PWD/$L/$($m.Split('.')[-2]).log" -Arguments @('-executeMethod', $m); "$m EXIT $c"
}
pwsh scripts/test.ps1 -Platform EditMode; "EDITMODE EXIT $LASTEXITCODE"
pwsh scripts/test.ps1 -Platform PlayMode; "PLAYMODE EXIT $LASTEXITCODE"
foreach ($tr in 'Low','High') { foreach ($lt in 'clear','overcast') { pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tr -Lighting $lt -OutputDir "artifacts/integration-s12/vqa-e/$tr-$lt"; "VQA $tr-$lt EXIT $LASTEXITCODE" } }
pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner lead-s12-integration-e
Revert-Side
git status --porcelain --untracked-files=no -- game Data art-source tools scripts
& ./scripts/sbs-gate3.ps1 -Tiers @('Low') -Lighting @('overcast','clear') -IncludeDiagnostics -RenderOnly -SlotOwner lead-s12-sbs -OutputRoot artifacts/integration-s12/sbs-e; "SBS EXIT $LASTEXITCODE"
Revert-Side
$dirty = git status --porcelain --untracked-files=no -- game Data art-source tools scripts
if ($dirty) { "DIRTY BEFORE APK: $dirty" }
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Priority -PollSeconds 5 -Owner lead-s12-apk
pwsh scripts/build-android.ps1 -Tier Low; "APK EXIT $LASTEXITCODE"
pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner lead-s12-apk
Revert-Side
"END $(Get-Date -Format o)"
