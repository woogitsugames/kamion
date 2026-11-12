# Uruchamiać wyłącznie na końcu rundy, zgodnie z aktualizacją właściciela z 11.11.
$ErrorActionPreference = 'Stop'
[System.Diagnostics.Process]::GetCurrentProcess().PriorityClass = 'BelowNormal'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
# W main znajduje się aktualna wersja infrastruktury z pulą heavy. Nie zmieniamy cudzych plików w worktree.
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slotScript -Acquire -Pool heavy -Owner gpt-truck-r3 -StaleHours 100000 -PollSeconds 5
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu heavy.' }
$testExit = -1
try {
    $env:OPENBLAS_NUM_THREADS = '1'
    $env:OMP_NUM_THREADS = '1'
    $env:MKL_NUM_THREADS = '1'
    uv run --project tools/worldgen python -m pytest tests/gis -q *> artifacts/truck-r3/gis-final.log
    $testExit = $LASTEXITCODE
}
finally {
    pwsh $slotScript -Release -Pool heavy -Owner gpt-truck-r3
}
Add-Content -Encoding utf8 artifacts/truck-r3/STATUS.md "Końcowy GIS uruchomiono pod slotem heavy; exit $testExit. Wynik w gis-final.log. Następny krok: porównać niepowodzenia z bazowymi pięcioma błędami, zapisać REPORT i skopiować artefakty do main."
git add -f artifacts/truck-r3/STATUS.md
git commit --only artifacts/truck-r3/STATUS.md -m 'wip(truck): koncowy GIS pod slotem heavy'
exit $testExit
