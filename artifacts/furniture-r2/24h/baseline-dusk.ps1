$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r2/24h'
# Invoke only after baseline.ps1 completes; never acquire an idempotent owner slot over our live Unity job.
$rows=@()
foreach ($tier in @('Low','High')) {
    foreach ($light in @('overcast','clear')) {
        $dir="$ev/before/$tier-$light"
        if (!(Test-Path "$dir/stats.txt")) { throw "Day baseline not complete: $dir" }
        $count=@(Get-ChildItem $dir -Filter '*.png' -File).Count
        if ($count -eq 0) { throw "Empty baseline: $dir" }
        $rows += [pscustomobject]@{tier=$tier;lighting=$light;png_count=$count}
    }
}
if (@($rows.png_count | Sort-Object -Unique).Count -ne 1) { throw 'Unequal baseline frame counts; inspect before proceeding' }
$rows | ConvertTo-Json | Set-Content "$ev/baseline-day-coverage.json" -Encoding utf8
foreach ($tier in @('Low','High')) {
    & pwsh "$ev/unity-step.ps1" -Step render -Phase before -Tier $tier -Lighting dusk
    if ($LASTEXITCODE -ne 0) { throw "Dusk baseline failed: $tier" }
}
Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): bazowy zmierzch Low/High ukończony. Preset dusk ma słońce -5 stopni: to zmierzch, nie dowód pełnej nocy ani kalibracji folii. NASTĘPNY KROK: snapshot geometrii w heavy, wdrożenie własnego zużycia/mocowań/flagi i pojedyncze testy; potem generator kandydata."
Copy-Item "$ev/STATUS.md" artifacts/furniture-r2/STATUS.md
git add -f "$ev/baseline-day-coverage.json" "$ev/STATUS.md" artifacts/furniture-r2/STATUS.md
git commit -m 'wip(furniture): preserve day and dusk baseline coverage'
