$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r2/24h'
foreach ($tier in @('Low','High')) {
    foreach ($light in @('clear','overcast','dusk')) {
        & pwsh "$ev/unity-step.ps1" -Step render -Phase after -Tier $tier -Lighting $light
        if ($LASTEXITCODE -ne 0) { throw "Candidate render failed: $tier $light" }
    }
}
foreach ($light in @('clear','overcast','dusk')) {
    & pwsh "$ev/exact-stats.ps1" -Phase after -Tier Low -Lighting $light
    if ($LASTEXITCODE -ne 0) { throw "Candidate exact counter failed: $light" }
}
# This path reads only small statistics/JSON files, and does not compose images.
& uv run --project tools/worldgen python "$ev/compare_frames.py" --metrics-only --label after1
if ($LASTEXITCODE -ne 0) { throw 'Counter comparison failed' }
Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): komplet standardowych obrazów po zmianie i dokładne liczniki Low zapisane. NASTĘPNY KROK: odczytać wszystkie delty, kontrolowany night-rig Low/High i arkusze porównawcze w heavy; geometrię raportować osobno według jej wyniku."
Copy-Item "$ev/STATUS.md" artifacts/furniture-r2/STATUS.md
git add -f "$ev/STATUS.md" artifacts/furniture-r2/STATUS.md "$ev/frame-budget.json" "$ev/frame-budget.csv" "$ev/frame-coverage.json"
git commit -m 'wip(furniture): checkpoint complete candidate camera coverage and CPU counters'
