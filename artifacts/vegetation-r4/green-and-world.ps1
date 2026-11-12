$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. ./artifacts/vegetation-r4/checkpoint.ps1
$owner=(git branch --show-current).Trim()
if ($owner -ne 'gpt-vegetation-r4') { throw 'Wrong branch' }
Add-Content artifacts/vegetation-r4/STATUS.md 'Kandydat A zmienia wyłącznie berberis_red: istniejąca geometria rdzenia używa istniejącego materiału alpha liści i UV w skali liścia. Test wysokości zachowano przez etykietowany wariant referencyjny; osobny test sprawdza identyczność geometrii. Kandydat nie jest zaakceptowany wizualnie.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 kandydat liści berberysu przed walidacją' -Paths @('artifacts/vegetation-r4/STATUS.md','tools/worldgen/streetscape/plantings.py','tests/gis/test_vegetation_0109.py','artifacts/vegetation-r4/green-and-world.ps1','artifacts/vegetation-r4/apply-candidate.ps1')
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
pwsh $slot -Acquire -Pool heavy -Owner $owner -StaleHours 1000000 -PollSeconds 2
if ($LASTEXITCODE -ne 0) { throw 'Heavy acquisition failed' }
try {
    $env:OPENBLAS_NUM_THREADS='1'
    $env:OMP_NUM_THREADS='1'
    $env:MKL_NUM_THREADS='1'
    uv run --project tools/worldgen python -m pytest tests/gis/test_berberis_0109_leaf_core.py tests/gis/test_vegetation_0109.py tests/gis/test_streetscape_r6.py -q *> artifacts/vegetation-r4/pytest-green.log
    if ($LASTEXITCODE -ne 0) { throw 'Focused tests failed; no World launched' }
    Add-Content artifacts/vegetation-r4/STATUS.md 'Celowane testy kandydata A przeszły kodem 0. Dalej pełna generacja świata w tym samym slocie heavy, sekwencyjnie.'
    Save-VegetationCheckpoint -Message 'wip(vegetation): r4 celowane testy GREEN' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/pytest-green.log')
    uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/vegetation-r4/world-candidate-a.log
    if ($LASTEXITCODE -ne 0) { throw 'Candidate World failed' }
    uv run --project tools/worldgen python artifacts/vegetation-r4/collision_digest.py *> artifacts/vegetation-r4/collision-candidate-a.log
    if ($LASTEXITCODE -ne 0) { throw 'Collision digest failed' }
    Add-Content artifacts/vegetation-r4/STATUS.md 'World kandydata A i migawka geometrii kolizji zakończone kodem 0; kolejny krok to porównanie źródeł i wyjść, import i próba wizualna.'
    Save-VegetationCheckpoint -Message 'wip(vegetation): r4 świat kandydata A wygenerowany'
} finally {
    pwsh $slot -Release -Pool heavy -Owner $owner
}
Set-Content artifacts/vegetation-r4/green-and-world.done 'Focused tests, World and collision digest exit 0'
