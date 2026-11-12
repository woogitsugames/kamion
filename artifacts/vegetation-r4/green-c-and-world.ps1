$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. ./artifacts/vegetation-r4/checkpoint.ps1
$owner=(git branch --show-current).Trim()
if ($owner -ne 'gpt-vegetation-r4') { throw 'Wrong branch' }
Add-Content artifacts/vegetation-r4/STATUS.md 'B3: niezalezna deterministyczna pokrywa kart na cap, rozstaw0.28m/min0.14m, wysokosc0.07-0.14m WORKING_VALUE. Geometria B2 zachowana, istniejacy material sprig. Nowe testy probek, wysokosci i waskiego E1. Celowane GIS oraz World tylko pod heavy.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 pokrywa C przed testami' -Paths @('artifacts/vegetation-r4/STATUS.md','tools/worldgen/streetscape/plantings.py','tests/gis/test_berberis_0109_rings.py','artifacts/vegetation-r4/green-c-and-world.ps1','artifacts/vegetation-r4/candidate-c-probe.ps1')
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
pwsh $slot -Acquire -Pool heavy -Owner $owner -StaleHours 1000000 -PollSeconds 2
if ($LASTEXITCODE -ne 0) { throw 'Heavy acquisition failed' }
try {
    $env:OPENBLAS_NUM_THREADS='1'
    $env:OMP_NUM_THREADS='1'
    $env:MKL_NUM_THREADS='1'
    uv run --project tools/worldgen python -m pytest tests/gis/test_berberis_0109_rings.py tests/gis/test_berberis_0109_leaf_core.py tests/gis/test_vegetation_0109.py tests/gis/test_streetscape_r6.py -q *> artifacts/vegetation-r4/pytest-green-c.log
    if ($LASTEXITCODE -ne 0) { throw 'Focused C tests failed; no World launched' }
    Add-Content artifacts/vegetation-r4/STATUS.md 'Celowane testy C kod0. World i dekodowanie kolizji dalej sekwencyjnie w tym samym heavy.'
    Save-VegetationCheckpoint -Message 'wip(vegetation): r4 celowane testy C zielone' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/pytest-green-c.log')
    uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/vegetation-r4/world-candidate-c.log
    if ($LASTEXITCODE -ne 0) { throw 'Candidate C World failed' }
    uv run --project tools/worldgen python artifacts/vegetation-r4/collision_digest.py *> artifacts/vegetation-r4/collision-candidate-c.log
    if ($LASTEXITCODE -ne 0) { throw 'Collision digest C failed' }
    Add-Content artifacts/vegetation-r4/STATUS.md 'World C i dekodowana kolizja zakończone0. Lekkie piny i porównanie potem, bez kolejnego oczekiwania heavy.'
    Save-VegetationCheckpoint -Message 'wip(vegetation): r4 świat C wygenerowany'
} finally {
    pwsh $slot -Release -Pool heavy -Owner $owner
}
Set-Content artifacts/vegetation-r4/green-c-and-world.done 'Focused tests, World and collision digest exit0'
