$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. ./artifacts/vegetation-r4/checkpoint.ps1
$owner=(git branch --show-current).Trim()
if ($owner -ne 'gpt-vegetation-r4') { throw 'Wrong branch' }
foreach ($path in @('pytest-green-d.log','world-candidate-d.log','green-d-and-world.done','green-d-pipeline-resume.log')) {
    if (Test-Path "artifacts/vegetation-r4/$path") { throw "Prior D result/log exists: $path. Inspect state before any retry." }
}
Start-Transcript -Path artifacts/vegetation-r4/green-d-pipeline-resume.log -NoClobber | Out-Null
Add-Content artifacts/vegetation-r4/STATUS.md 'D: ta sama liczba probek i kart co C, nizsza i bardziej pozioma pokrywa. Dane dlugosci/szerokosci/tilt/bury WORKING_VALUE. Nowy test emitowanej geometrii sprawdza niski profil, podstawe i rzut XY bez wzrostu tris/zmiany UV. Celowane testy i warunkowy World tylko przez heavy.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 niska pokrywa D przed testami' -Paths @('artifacts/vegetation-r4/STATUS.md','tools/worldgen/streetscape/plantings.py','tests/gis/test_berberis_0109_rings.py','artifacts/vegetation-r4/green-d-and-world.ps1','artifacts/vegetation-r4/candidate-d-probe.ps1')
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
pwsh $slot -Acquire -Pool heavy -Owner $owner -StaleHours 1000000 -PollSeconds 2
if ($LASTEXITCODE -ne 0) { throw 'Heavy acquisition failed' }
try {
    $env:OPENBLAS_NUM_THREADS='1'
    $env:OMP_NUM_THREADS='1'
    $env:MKL_NUM_THREADS='1'
    uv run --project tools/worldgen python -m pytest tests/gis/test_berberis_0109_rings.py tests/gis/test_berberis_0109_leaf_core.py tests/gis/test_vegetation_0109.py tests/gis/test_streetscape_r6.py -q *> artifacts/vegetation-r4/pytest-green-d.log
    if ($LASTEXITCODE -ne 0) { throw 'Focused D tests failed; no World launched' }
    Add-Content artifacts/vegetation-r4/STATUS.md 'Celowane testy D kod0. World i dekodowanie kolizji dalej sekwencyjnie w tym samym heavy.'
    Save-VegetationCheckpoint -Message 'wip(vegetation): r4 celowane testy D zielone' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/pytest-green-d.log')
    uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/vegetation-r4/world-candidate-d.log
    if ($LASTEXITCODE -ne 0) { throw 'Candidate D World failed' }
    uv run --project tools/worldgen python artifacts/vegetation-r4/collision_digest.py *> artifacts/vegetation-r4/collision-candidate-d.log
    if ($LASTEXITCODE -ne 0) { throw 'Collision digest D failed' }
    Add-Content artifacts/vegetation-r4/STATUS.md 'World D i dekodowana kolizja zakończone0. Lekkie piny i porównanie potem, bez kolejnego oczekiwania heavy.'
    Save-VegetationCheckpoint -Message 'wip(vegetation): r4 świat D wygenerowany'
} finally {
    pwsh $slot -Release -Pool heavy -Owner $owner
}
Set-Content artifacts/vegetation-r4/green-d-and-world.done 'Focused tests, World and collision digest exit0'
Stop-Transcript | Out-Null
