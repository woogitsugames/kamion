$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\gpt-vegetation'
. ./artifacts/vegetation-r4/checkpoint.ps1
$owner=(git branch --show-current).Trim()
if ($owner -ne 'gpt-vegetation-r4') { throw 'Wrong branch' }
Add-Content artifacts/vegetation-r4/STATUS.md 'B naprawia offsety ringów berberysu i ich próbkowanie, bez zmiany tekstur A. Lekka analiza0,81s: osiem capów poprawnych, najdłuższa krawędź<0,98m zamiast16–20m; część wąskich capów prawidłowo ma tylko punkty brzegu. Dla E2/A/C wróciło odpowiednio6/4/1 punktów wewnętrznych. To nie akceptacja wizualna; sprawdzić paski, prześwit rdzenia i koszty.'
Save-VegetationCheckpoint -Message 'wip(vegetation): r4 poprawne offsety berberysu przed walidacją B' -Paths @('artifacts/vegetation-r4/STATUS.md','tools/worldgen/streetscape/plantings.py','tests/gis/test_berberis_0109_rings.py','artifacts/vegetation-r4/inspect_cap.py','artifacts/vegetation-r4/cap-study-b-initial.json','artifacts/vegetation-r4/green-b-and-world.ps1')
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
pwsh $slot -Acquire -Pool heavy -Owner $owner -StaleHours 1000000 -PollSeconds 2
if ($LASTEXITCODE -ne 0) { throw 'Heavy acquisition failed' }
try {
    $env:OPENBLAS_NUM_THREADS='1'
    $env:OMP_NUM_THREADS='1'
    $env:MKL_NUM_THREADS='1'
    uv run --project tools/worldgen python -m pytest tests/gis/test_berberis_0109_rings.py tests/gis/test_berberis_0109_leaf_core.py tests/gis/test_vegetation_0109.py tests/gis/test_streetscape_r6.py -q *> artifacts/vegetation-r4/pytest-green-b.log
    if ($LASTEXITCODE -ne 0) { throw 'Focused B tests failed; no World launched' }
    Add-Content artifacts/vegetation-r4/STATUS.md 'Celowane testy B kod0. World i dekodowanie kolizji dalej sekwencyjnie w tym samym heavy.'
    Save-VegetationCheckpoint -Message 'wip(vegetation): r4 celowane testy B zielone' -Paths @('artifacts/vegetation-r4/STATUS.md','artifacts/vegetation-r4/pytest-green-b.log')
    uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/vegetation-r4/world-candidate-b.log
    if ($LASTEXITCODE -ne 0) { throw 'Candidate B World failed' }
    uv run --project tools/worldgen python artifacts/vegetation-r4/collision_digest.py *> artifacts/vegetation-r4/collision-candidate-b.log
    if ($LASTEXITCODE -ne 0) { throw 'Collision digest B failed' }
    Add-Content artifacts/vegetation-r4/STATUS.md 'World B i dekodowana kolizja zakończone0. Lekkie piny i porównanie potem, bez kolejnego oczekiwania heavy.'
    Save-VegetationCheckpoint -Message 'wip(vegetation): r4 świat B wygenerowany'
} finally {
    pwsh $slot -Release -Pool heavy -Owner $owner
}
Set-Content artifacts/vegetation-r4/green-b-and-world.done 'Focused tests, World and collision digest exit0'
