$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. artifacts/vegetation-r4/checkpoint.ps1
if (-not (Test-Path artifacts/vegetation-r4/baseline.done)) { throw 'Finish fresh baseline first' }
$heavyOwner=(git branch --show-current).Trim()
if ($heavyOwner -ne 'gpt-vegetation-r4') { throw 'Wrong round branch' }
$baseline=Get-Content artifacts/vegetation-r4/snapshot-baseline/sha256.json -Raw | ConvertFrom-Json
$expected=$baseline.source_files.'tools/worldgen/streetscape/plantings.py'
if ((Get-FileHash tools/worldgen/streetscape/plantings.py).Hash.ToLowerInvariant() -ne $expected) { throw 'Production drift before RED' }
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
pwsh $slot -Acquire -Pool heavy -Owner $heavyOwner -StaleHours 1000000 -PollSeconds 2
if ($LASTEXITCODE -ne 0) { throw 'Heavy acquisition failed' }
try {
    $env:OPENBLAS_NUM_THREADS='1'
    $env:OMP_NUM_THREADS='1'
    $env:MKL_NUM_THREADS='1'
    uv run --project tools/worldgen python artifacts/vegetation-r4/review_images.py *> artifacts/vegetation-r4/review-before.log
    if ($LASTEXITCODE -ne 0) { throw 'Before evidence generation failed' }
    Add-Content artifacts/vegetation-r4/STATUS.md 'Złożono arkusze świeżego baseline i statystyki kamer w heavy, z ograniczeniem BLAS do jednego wątku. Autor musi obejrzeć arkusze przed zmianą produkcji.'
    Save-VegetationCheckpoint -Message 'wip(vegetation): r4 arkusze i statystyki świeżego baseline'
    $testPath='tests/gis/test_berberis_0109_leaf_core.py'
    if (Test-Path $testPath) { throw 'Inspect existing new test before replacing it' }
    $text=[IO.File]::ReadAllText((Join-Path (Get-Location).Path 'artifacts/vegetation-r4/pending_test_berberis_leaf_core.py'))
    $text=$text.Replace('Pending R4 regression tests. Copy to tests/gis only after fresh baseline review.','Berberis foliage-layer material and geometry regressions (ADR0109 r4).').Replace('Not yet run; every GIS pytest invocation must use pool heavy.','Run through pool heavy, like all GIS tests.')
    [IO.File]::WriteAllText((Join-Path (Get-Location).Path $testPath),$text,[Text.UTF8Encoding]::new($false))
    uv run --project tools/worldgen python -m pytest $testPath -q *> artifacts/vegetation-r4/pytest-red.log
    $redExit=$LASTEXITCODE
    $result=Get-Content artifacts/vegetation-r4/pytest-red.log -Raw
    $expectedRed=($redExit -eq 1 -and $result -match '1 failed,\s+4 passed' -and $result -match 'test_berberis_has_leaf_cover_instead_of_an_opaque_full_height_core')
    @{exit_code=$redExit;expected_red=$expectedRed;production_changed=$false} | ConvertTo-Json | Set-Content -Encoding utf8 artifacts/vegetation-r4/red-proof.json
    Add-Content artifacts/vegetation-r4/STATUS.md "Celowany RED nowego kontraktu: kod $redExit, oczekiwany RED=$expectedRed. Produkcja nadal bez zmian; to nie zielony test ani akceptacja wyglądu."
    Save-VegetationCheckpoint -Message 'wip(vegetation): r4 celowany test RED berberysu' -Paths @('artifacts/vegetation-r4/STATUS.md',$testPath,'artifacts/vegetation-r4/red-proof.json','artifacts/vegetation-r4/pytest-red.log')
    if (-not $expectedRed) { throw 'Unexpected RED result; inspect before applying candidate' }
} finally {
    pwsh $slot -Release -Pool heavy -Owner $heavyOwner
}
Set-Content artifacts/vegetation-r4/review-and-red.done 'Review all contact sheets and expected RED before applying production change.'
