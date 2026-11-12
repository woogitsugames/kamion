$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r2/24h'
foreach ($step in @('pbr','world')) {
    & pwsh "$ev/heavy-step.ps1" -Step $step -Phase before
    if ($LASTEXITCODE -ne 0) { throw "Baseline $step failed; inspect log before resuming" }
}
if (Select-String -Path "$ev/build-before.log" -SimpleMatch 'fallback=True') {
    throw 'Baseline world source fallback; do not import'
}
& pwsh "$ev/unity-step.ps1" -Step import -Phase before
if ($LASTEXITCODE -ne 0) { throw 'Baseline import failed' }
foreach ($tier in @('Low','High')) {
    foreach ($light in @('overcast','clear')) {
        & pwsh "$ev/unity-step.ps1" -Step render -Phase before -Tier $tier -Lighting $light
        if ($LASTEXITCODE -ne 0) { throw "Baseline render failed: $tier $light" }
    }
}
Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): bazowe obrazy po scaleniu main gotowe. NASTĘPNY KROK: policzyć kompletność kamer i obejrzeć znaki przed zmianą."
Copy-Item "$ev/STATUS.md" artifacts/furniture-r2/STATUS.md
git add -f "$ev/STATUS.md" artifacts/furniture-r2/STATUS.md
git commit -m 'wip(furniture): checkpoint round two baseline renders'
