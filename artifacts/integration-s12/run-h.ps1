# s12 h: after 0134 tail + 0137 audio — tests, clean APK Low for owner Fold test.
$ErrorActionPreference = 'Continue'
Set-Location C:\Users\matma\Documents\Claude\kamion
. ./scripts/env.ps1
function Revert-Side { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null }
"START $(Get-Date -Format o) $(git rev-parse --short HEAD)"
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Priority -PollSeconds 5 -Owner lead-s12-h
Revert-Side
pwsh scripts/test.ps1 -Platform EditMode; "EDITMODE EXIT $LASTEXITCODE"
pwsh scripts/test.ps1 -Platform PlayMode; "PLAYMODE EXIT $LASTEXITCODE"
Revert-Side
$dirty = git status --porcelain --untracked-files=no -- game Data art-source tools scripts
if ($dirty) { "DIRTY BEFORE APK: $dirty" }
pwsh scripts/build-android.ps1 -Tier Low; "APK EXIT $LASTEXITCODE"
pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner lead-s12-h
Revert-Side
"END $(Get-Date -Format o)"
