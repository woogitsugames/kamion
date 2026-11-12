$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if (!(Select-String -LiteralPath artifacts/truck-r3/STATUS.md -SimpleMatch 'Import bieżącej bazy zakończony' -Quiet)) { throw 'Najpierw zakończ przygotowanie bazy; nie wolno współdzielić Owner heavy.' }
$env:OPENBLAS_NUM_THREADS='1'; $env:OMP_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$blender='C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe'
$inputs=@('tools/blender/truck/exterior/a6_export.py','art-source/truck/exterior/qa/check_round_atlas_seams_0115.py')
$before=((Get-FileHash -LiteralPath $inputs -Algorithm SHA256).Hash -join "`n")
pwsh $slot -Acquire -Pool heavy -Owner gpt-truck-r3 -StaleHours 100000 -PollSeconds 1
if($LASTEXITCODE -ne 0){throw 'Nie uzyskano slotu heavy.'}
$start=Get-Date
try {
    $log="artifacts/truck-r3/atlas-seam-regression-$($start.ToString('yyyyMMdd-HHmmss')).log"
    & $blender -b --factory-startup --threads 2 --python-exit-code 1 --python art-source/truck/exterior/qa/check_round_atlas_seams_0115.py *> $log
    $code=$LASTEXITCODE
    $after=((Get-FileHash -LiteralPath $inputs -Algorithm SHA256).Hash -join "`n")
    if($code -ne 0 -or !(Select-String -LiteralPath $log -SimpleMatch 'TRUCK_ATLAS_SEAM_TEST: OK cases=4' -Quiet) -or $after -ne $before){throw "Nieudana regresja Atlas, exit $code."}
    if((Get-Item artifacts/truck-r3/atlas-seam-regression.json).LastWriteTime -lt $start){throw 'Nieświeży wynik regresji.'}
} finally {
    pwsh $slot -Release -Pool heavy -Owner gpt-truck-r3
}
Add-Content -Encoding utf8 artifacts/truck-r3/STATUS.md 'Regresja czterech syntetycznych Atlas seams w Blenderze przeszła pod heavy, dwa wątki. Poprzednia funkcja odtworzyła błąd, nowa nie mostkuje wysp. To nie akceptacja pełnych FBX ani budżetu. Następny krok: pełna regeneracja zewnętrza do osobnego katalogu kandydata pod heavy, sprawdzenie budżetu i podglądy.'
git add -f artifacts/truck-r3/STATUS.md
git commit --only artifacts/truck-r3/STATUS.md -m 'wip(truck): wynik regresji wysp atlasu'
