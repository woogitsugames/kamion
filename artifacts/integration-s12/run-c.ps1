# s12: SBS Low (overcast+clear, diagnostics) on main + clean APK Low.
$ErrorActionPreference = 'Continue'
Set-Location C:\Users\matma\Documents\Claude\kamion
. ./scripts/env.ps1
function Revert-Side { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null }
"START $(Get-Date -Format o) $(git rev-parse --short HEAD)"
Revert-Side
& ./scripts/sbs-gate3.ps1 -Tiers @('Low') -Lighting @('overcast','clear') -IncludeDiagnostics -SlotOwner lead-s12-sbs -OutputRoot artifacts/integration-s12/sbs-b; "SBS EXIT $LASTEXITCODE"
Revert-Side
$dirty = git status --porcelain --untracked-files=no -- game Data art-source tools scripts
if ($dirty) { "DIRTY BEFORE APK: $dirty" }
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Priority -PollSeconds 5 -Owner lead-s12-apk
pwsh scripts/build-android.ps1 -Tier Low; "APK EXIT $LASTEXITCODE"
pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner lead-s12-apk
Revert-Side
"END $(Get-Date -Format o)"
