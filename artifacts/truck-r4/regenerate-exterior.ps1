param([ValidatePattern('^[a-z0-9-]+$')][string]$Stage='regular-front-v1')
$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if((git branch --show-current) -ne 'gpt-truck-r4'){throw 'Ten wrapper należy do rundy 4.'}
foreach($path in @('fixture-before.json','before/Low-overcast/complete.ok','before/High-clear/complete.ok','before-all/High-overcast/stats.txt','detail-before-fleet/complete.ok')){
    if(!(Test-Path "artifacts/truck-r4/$path")){throw "Najpierw kompletny świeży baseline: $path"}
}
$folder="artifacts/truck-r4/$Stage"
if(Test-Path $folder){throw 'Nie nadpisuj wcześniejszej próby; wybierz nowy Stage.'}
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$mine='C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/gpt-truck-r4.slot'
if(Test-Path $mine){throw 'Własny heavy zajęty; potwierdź zakończenie poprzedniego procesu.'}
$source='art-source/truck/exterior/export'
$backup='artifacts/truck-r4/original-exterior-export'
if(!(Test-Path 'artifacts/truck-r4/original-exterior-export-sha.json')){
    robocopy $source $backup /E /XJ /R:1 /W:1 /NFL /NDL /NJH /NJS
    if($LASTEXITCODE -gt 7){throw 'Nie zachowano oryginalnych eksportów.'}
    Get-ChildItem $source -Recurse -File | Sort-Object FullName | Get-FileHash -Algorithm SHA256 | Select-Object Path,Hash | ConvertTo-Json | Set-Content artifacts/truck-r4/original-exterior-export-sha.json -Encoding utf8
    Copy-Item art-source/truck/exterior/door_interface.json,art-source/truck/exterior/glass_interface.json artifacts/truck-r4
}
New-Item -ItemType Directory -Path $folder | Out-Null
$inputs=@(Get-ChildItem tools/blender/truck/exterior,tools/blender/truck/trailer -Filter '*.py' | Sort-Object FullName | ForEach-Object FullName)
$inputs+=@('art-source/truck/dims.json','art-source/truck/exterior/qa/generate_and_check_0115.py','art-source/truck/exterior/qa/check_round_atlas_seams_0115.py','art-source/truck/exterior/qa/check_disc_blender_0115.py',$PSCommandPath)
$fp=((Get-FileHash -LiteralPath $inputs -Algorithm SHA256).Hash -join "`n")
$env:OPENBLAS_NUM_THREADS='1';$env:OMP_NUM_THREADS='1';$env:MKL_NUM_THREADS='1'
$acquired=$false
for($attempt=1;$attempt -le 3;$attempt++){
    $ErrorActionPreference='Continue'
    $acquireLog="$folder/acquire-$attempt.log"
    pwsh $slot -Acquire -Pool heavy -Owner gpt-truck-r4 -StaleHours 100000 -PollSeconds 60 2>&1 | Tee-Object -FilePath $acquireLog
    $slotCode=$LASTEXITCODE
    $ErrorActionPreference='Stop'
    if($slotCode -eq 0){$acquired=$true;break}
    if(!(Select-String -LiteralPath $acquireLog -Pattern 'used by another process|cannot access the file' -Quiet)){throw 'Nie uzyskano heavy; sprawdź log.'}
    Start-Sleep -Seconds 2
}
if(!$acquired){throw 'Trzy terminalne błędy biletu heavy; nie uruchomiono Blendera.'}
$start=Get-Date
$result=[ordered]@{generation_id=$Stage;domain='exterior';result='Failed';validated=$false;pool='heavy';owner='gpt-truck-r4';threads=2;source_fingerprint=$fp;regular_front_wheels=$true}
try {
    if(((Get-FileHash -LiteralPath $inputs -Algorithm SHA256).Hash -join "`n") -ne $fp){throw 'Źródła zmienione w kolejce.'}
    $log="$folder/generate.log"
    & 'C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe' -b --factory-startup --threads 2 --python-exit-code 1 --python art-source/truck/exterior/qa/generate_and_check_0115.py -- --domain exterior --artifact-root $folder --regular-front-wheels *> $log
    $code=$LASTEXITCODE
    foreach($marker in @('TRUCK_ATLAS_SEAM_TEST: OK','TRUCK_DISC_NATIVE_SMOKE: OK','TRUCK_GENERATOR_AND_CHECK: OK exterior')){
        if($code -ne 0 -or !(Select-String -LiteralPath $log -SimpleMatch $marker -Quiet)){throw "Nieudany preflight/generator/validator, exit $code, brak $marker"}
    }
    if(((Get-FileHash -LiteralPath $inputs -Algorithm SHA256).Hash -join "`n") -ne $fp){throw 'Źródła zmienione w trakcie generowania.'}
    $manifest=Get-Content "$source/truck_exterior_manifest.json" -Raw | ConvertFrom-Json
    if(!$manifest.regular_front_wheels){throw 'Eksport nie zawiera wybranego wariantu.'}
    $files=@(Get-ChildItem $source -Recurse -File | Where-Object {$_.Extension -in @('.fbx','.png','.json')})
    $files+=@(Get-Item art-source/truck/exterior/door_interface.json,art-source/truck/exterior/glass_interface.json)
    $result.outputs=@($files | Sort-Object FullName | Get-FileHash -Algorithm SHA256 | ForEach-Object {[ordered]@{path=$_.Path;sha256=$_.Hash}})
    $result.result='Passed';$result.validated=$true
} catch {
    $result.error=$_.Exception.Message
} finally {
    pwsh $slot -Release -Pool heavy -Owner gpt-truck-r4
    $result.seconds=((Get-Date)-$start).TotalSeconds
    $result.log="$folder/generate.log";$result.cache="$folder/cache/exterior.blend"
    $result | ConvertTo-Json -Depth 6 | Set-Content "$folder/result.json" -Encoding utf8
    $result | ConvertTo-Json -Depth 6 | Set-Content artifacts/truck-r4/generate-exterior-result.json -Encoding utf8
}
Add-Content artifacts/truck-r4/STATUS.md "Generowanie $Stage`: $($result.result), validated=$($result.validated). Preflight i pełny bake/check w jednym slotowanym cyklu, Blender dwa wątki. Native wynik nie jest PASS wyglądu. Przy błędzie nie instaluj częściowych plików. Następny krok: odczytać wynik; po Passed installer i te same kamery, po Failed poprawić konkretną przyczynę."
git add -f artifacts/truck-r4/STATUS.md artifacts/truck-r4/generate-exterior-result.json
git commit --only artifacts/truck-r4/STATUS.md artifacts/truck-r4/generate-exterior-result.json -m "wip(truck): wynik generowania $Stage"
if($result.result -ne 'Passed'){throw $result.error}
