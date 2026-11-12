# s12 f: after 0131 merge — Fab decal retrofit, EditMode, vqa Low/High, clean APK Low.
$ErrorActionPreference = 'Continue'
Set-Location C:\Users\matma\Documents\Claude\kamion
. ./scripts/env.ps1
function Revert-Side { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null }
$L = 'artifacts/integration-s12/logs-f'; New-Item -ItemType Directory -Force $L | Out-Null
"START $(Get-Date -Format o) $(git rev-parse --short HEAD)"
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Priority -PollSeconds 5 -Owner lead-s12-f
$c = Invoke-UnityBatch -LogFile "$PWD/$L/FabDecalRetrofit.log" -Arguments @('-executeMethod','Game.World.Import.FabDecalRetrofit.RunBatch','-region','bialystok-industrial-c'); "RETROFIT EXIT $c"
Select-String -Path "$L/FabDecalRetrofit.log" -Pattern 'converted' | Select-Object -Last 3 | ForEach-Object { $_.Line }
pwsh scripts/test.ps1 -Platform EditMode; "EDITMODE EXIT $LASTEXITCODE"
foreach ($tr in 'Low','High') { foreach ($lt in 'clear','overcast','dusk') { pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tr -Lighting $lt -OutputDir "artifacts/integration-s12/vqa-f/$tr-$lt"; "VQA $tr-$lt EXIT $LASTEXITCODE" } }
Revert-Side
$dirty = git status --porcelain --untracked-files=no -- game Data art-source tools scripts
if ($dirty) { "DIRTY BEFORE APK: $dirty" }
pwsh scripts/build-android.ps1 -Tier Low; "APK EXIT $LASTEXITCODE"
pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner lead-s12-f
Revert-Side
"END $(Get-Date -Format o)"
