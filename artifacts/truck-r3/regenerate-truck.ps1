param([ValidateSet('exterior','trailer')][string]$Domain='exterior')
$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$test=Get-Content artifacts/truck-r3/atlas-seam-regression.json -Raw | ConvertFrom-Json
$a6=(Get-FileHash tools/blender/truck/exterior/a6_export.py -Algorithm SHA256).Hash.ToLowerInvariant()
if($test.result -ne 'Passed' -or $test.candidate_source_sha256 -ne $a6){throw 'Brak aktualnej zielonej regresji Atlas.'}
if(!(Test-Path artifacts/truck-r3/fixture-before.json)){throw 'Brak bazowego stanu siatek.'}
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/gpt-truck-r3.slot'){throw 'Owner heavy już zajęty; najpierw potwierdź zakończenie poprzedniego procesu.'}
$source="art-source/truck/$Domain/export"
$backup="artifacts/truck-r3/original-$Domain-export"
$marker="artifacts/truck-r3/original-$Domain-export-sha.json"
if(!(Test-Path $marker)) {
    robocopy $source $backup /E /XJ /R:1 /W:1 /NFL /NDL /NJH /NJS
    if($LASTEXITCODE -gt 7){throw 'Nie zachowano oryginalnego eksportu.'}
    Get-ChildItem $source -Recurse -File | Sort-Object FullName | Get-FileHash -Algorithm SHA256 | Select-Object Path,Hash | ConvertTo-Json | Set-Content -Encoding utf8 $marker
    if($Domain -eq 'exterior'){
        Copy-Item art-source/truck/exterior/door_interface.json,art-source/truck/exterior/glass_interface.json artifacts/truck-r3
    }
}
$env:OPENBLAS_NUM_THREADS='1';$env:OMP_NUM_THREADS='1';$env:MKL_NUM_THREADS='1'
$inputs=@(Get-ChildItem tools/blender/truck/exterior -Filter '*.py' | Sort-Object Name | ForEach-Object FullName)
$inputs+=@(Get-ChildItem tools/blender/truck/trailer -Filter '*.py' | Sort-Object Name | ForEach-Object FullName)
$inputs+=@('art-source/truck/dims.json','art-source/truck/exterior/qa/generate_and_check_0115.py')
$fp=((Get-FileHash -LiteralPath $inputs -Algorithm SHA256).Hash -join "`n")
pwsh $slot -Acquire -Pool heavy -Owner gpt-truck-r3 -StaleHours 100000 -PollSeconds 1
if($LASTEXITCODE -ne 0){throw 'Nie uzyskano slotu heavy.'}
$start=Get-Date
try {
    if(((Get-FileHash -LiteralPath $inputs -Algorithm SHA256).Hash -join "`n") -ne $fp){throw 'Źródła zmienione podczas oczekiwania.'}
    $log="artifacts/truck-r3/generate-$Domain-$($start.ToString('yyyyMMdd-HHmmss')).log"
    & 'C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe' -b --factory-startup --threads 2 --python-exit-code 1 --python art-source/truck/exterior/qa/generate_and_check_0115.py -- --domain $Domain *> $log
    $code=$LASTEXITCODE
    if($code -ne 0 -or !(Select-String -LiteralPath $log -SimpleMatch "TRUCK_GENERATOR_AND_CHECK: OK $Domain" -Quiet)){throw "Nieudana regeneracja/validator $Domain, exit $code. Nie importuj częściowego eksportu."}
    if(((Get-FileHash -LiteralPath $inputs -Algorithm SHA256).Hash -join "`n") -ne $fp){throw 'Źródła zmienione podczas generowania.'}
    $outputs=@(Get-ChildItem $source -Recurse -File | Where-Object {$_.Extension -in @('.fbx','.png','.json')} | Sort-Object FullName | Get-FileHash -Algorithm SHA256 | ForEach-Object {[ordered]@{path=$_.Path;sha256=$_.Hash}})
    [ordered]@{domain=$Domain;result='Passed';seconds=((Get-Date)-$start).TotalSeconds;source_fingerprint=$fp;log=$log;threads=2;pool='heavy';owner='gpt-truck-r3';validated=$true;cache="artifacts/truck-r3/cache/$Domain.blend";outputs=$outputs} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 "artifacts/truck-r3/generate-$Domain-result.json"
} finally {
    pwsh $slot -Release -Pool heavy -Owner gpt-truck-r3
}
Add-Content -Encoding utf8 artifacts/truck-r3/STATUS.md "Regeneracja $Domain i natywny validator FBX przeszły pod heavy, Blender dwa wątki; cache i oryginalne pliki zachowane. To nie PASS wyglądu. Następny krok: po obu eksportach kanoniczny installer pod Unity, test piast i kadry kandydata."
git add -f artifacts/truck-r3/STATUS.md "artifacts/truck-r3/generate-$Domain-result.json"
git commit --only artifacts/truck-r3/STATUS.md "artifacts/truck-r3/generate-$Domain-result.json" -m "wip(truck): regeneracja i walidacja FBX $Domain"
