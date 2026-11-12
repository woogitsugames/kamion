param([string]$Stage = 'after')
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion'
$slot = Join-Path $root 'scripts/unity-slot.ps1'
$cameras = (Get-Content artifacts/gpt-s16-r1/clear-cameras.json -Raw | ConvertFrom-Json).cameras.id -join ','
foreach ($tier in @('Low','High')) {
    foreach ($light in @('clear','overcast')) {
        & pwsh $slot -Acquire -Owner gpt-s16
        try {
            if (Test-Path "$root/artifacts/locks/PHONE_RUN") { throw 'PHONE_RUN appeared' }
            & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $tier -Lighting $light -Gate3 artifacts/gpt-s16-r1/clear-cameras.json -Cameras $cameras -OutputDir "artifacts/gpt-s16-r1/clear/$Stage/$tier-$light" *> "artifacts/gpt-s16-r1/clear-$Stage-$tier-$light.log"
            if ($LASTEXITCODE -ne 0) { throw "clear $Stage $tier $light failed" }
        } finally {
            git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
            & pwsh $slot -Release -Owner gpt-s16
        }
        Add-Content artifacts/gpt-s16-r1/STATUS.md "`nDodatkowe kamery: $Stage/$tier-$light zapisane."
        git add -f artifacts/gpt-s16-r1/STATUS.md "artifacts/gpt-s16-r1/clear/$Stage/$tier-$light/stats.txt"
        git commit -m "wip(s16): capture unobstructed supplement $Stage $tier $light"
        Copy-Item artifacts/gpt-s16-r1/STATUS.md "$root/artifacts/gpt-s16/PRZEKAZANIE.md"
        Add-Content "$root/artifacts/gpt-s16/PRZEKAZANIE.md" "SHA: $(git rev-parse HEAD)"
    }
}
