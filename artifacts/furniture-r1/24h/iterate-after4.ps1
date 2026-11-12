param([int]$PreviousPipelinePid=53308)
$ErrorActionPreference='Stop'
$root=(Resolve-Path "$PSScriptRoot/../../..").Path
Set-Location $root
$ev='artifacts/furniture-r1/24h'
$evRoot=(Resolve-Path $ev).Path
# The existing comparison must finish before reusing this branch's heavy slot or moving its inputs.
if (Get-Process -Id $PreviousPipelinePid -ErrorAction SilentlyContinue) {
    Wait-Process -Id $PreviousPipelinePid -ErrorAction SilentlyContinue
}
if (!(Select-String -Path "$ev/STATUS.md" -SimpleMatch 'heavy compare after3; sukces=True;')) {
    throw 'Iteration3 comparison did not report success; inspect its existing process/log before proceeding'
}
foreach ($pair in @(@('after','after-iteration3'),@('after-sbs','after-sbs-iteration3'),@('compare','iteration3/compare'))) {
    $source=(Resolve-Path -LiteralPath (Join-Path $evRoot $pair[0])).Path
    $target=[IO.Path]::GetFullPath((Join-Path $evRoot $pair[1]))
    $prefix=$evRoot+[IO.Path]::DirectorySeparatorChar
    if (!$source.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase) -or !$target.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) {
        throw 'Archive path left the owned round artifact directory'
    }
    if (Test-Path -LiteralPath $target) { throw "Archive already exists: $target" }
    Move-Item -LiteralPath $source -Destination $target
}
foreach ($name in @('after3-detail.jpg','reference-sign-after.jpg','daylight-reference-sheet-final.jpg','frame-budget.json','frame-budget.csv')) {
    Copy-Item -LiteralPath "$ev/$name" -Destination "$ev/iteration3/$name"
}
Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): pełne obrazy/arkusze iteracji3 zachowano w after-iteration3, after-sbs-iteration3 i iteration3/compare. Rozpoczyna się walidacja iteracji4, bez równoległego heavy tego samego właściciela. NASTĘPNY KROK: pojedyncze testy i generator after4."
Copy-Item "$ev/STATUS.md" artifacts/furniture-r1/STATUS.md
git add -f "$ev/STATUS.md" artifacts/furniture-r1/STATUS.md
git commit -m 'wip(furniture): archive iteration3 before validating iteration4'
foreach ($test in @('tests/gis/test_furniture_0120.py','tests/gis/test_furniture_r1.py')) {
    & pwsh "$ev/heavy-step.ps1" -Step focused -Phase after4 -TestFile $test
    if ($LASTEXITCODE -ne 0) { throw "Focused regression failed: $test" }
}
& pwsh "$ev/heavy-step.ps1" -Step world -Phase after4
if ($LASTEXITCODE -ne 0) { throw 'After4 generation failed' }
if (Select-String -Path "$ev/build-after4.log" -SimpleMatch 'fallback=True') { throw 'After4 source fallback' }
& pwsh "$ev/heavy-step.ps1" -Step geometry -Phase after
if ($LASTEXITCODE -ne 0) { throw 'Protected geometry verification failed' }
& pwsh "$ev/unity-step.ps1" -Step import -Phase after
if ($LASTEXITCODE -ne 0) { throw 'After4 import failed' }
foreach ($tier in @('Low','High')) {
    foreach ($light in @('overcast','clear')) {
        & pwsh "$ev/unity-step.ps1" -Step render -Phase after -Tier $tier -Lighting $light
        if ($LASTEXITCODE -ne 0) { throw "Render failed: $tier $light" }
    }
}
& pwsh "$ev/unity-step.ps1" -Step sbs-sign -Phase after -Tier High -Lighting overcast
if ($LASTEXITCODE -ne 0) { throw 'Reference sign render failed' }
& pwsh "$ev/heavy-step.ps1" -Step compare -Phase after4
if ($LASTEXITCODE -ne 0) { throw 'After4 all-camera comparison failed' }
Write-Output 'After4 evidence ready; inspect appearance and budgets before closing the round.'
