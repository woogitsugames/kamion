param([string]$Stage = 'before')
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion'
$slot = Join-Path $root 'scripts/unity-slot.ps1'
foreach ($tier in @('Low','High')) {
    foreach ($light in @('clear','overcast')) {
        & pwsh $slot -Acquire -Owner gpt-s16
        try {
            if (Test-Path "$root/artifacts/locks/PHONE_RUN") { throw 'PHONE_RUN appeared after acquisition' }
            & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -OutputDir "artifacts/gpt-s16-r1/$Stage/$tier-$light" *> "artifacts/gpt-s16-r1/$Stage-$tier-$light.log"
            if ($LASTEXITCODE -ne 0) { throw "render failed: $Stage $tier $light" }
        } finally {
            git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
            & pwsh $slot -Release -Owner gpt-s16
        }
    }
}
