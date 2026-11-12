$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/heavy-slots/gpt-truck-r3.slot'){throw 'Własny heavy zajęty; najpierw potwierdź koniec poprzedniego zadania.'}
$inputs=@(Get-ChildItem tools/blender/truck/exterior,tools/blender/truck/trailer -Filter '*.py' | Sort-Object FullName | ForEach-Object FullName)
$inputs+=@('art-source/truck/exterior/qa/reexport_lod2_0115.py','art-source/truck/exterior/qa/check_round_atlas_seams_0115.py','artifacts/truck-r3/cache-v2-sha.json')
$fp=((Get-FileHash -LiteralPath $inputs -Algorithm SHA256).Hash -join "`n")
$env:OPENBLAS_NUM_THREADS='1';$env:OMP_NUM_THREADS='1';$env:MKL_NUM_THREADS='1'
pwsh $slot -Acquire -Pool heavy -Owner gpt-truck-r3 -StaleHours 100000 -PollSeconds 1
if($LASTEXITCODE -ne 0){throw 'Nie uzyskano slotu heavy.'}
try {
    foreach($domain in @('exterior','trailer')) {
        if(((Get-FileHash -LiteralPath $inputs -Algorithm SHA256).Hash -join "`n") -ne $fp){throw 'Źródła zmienione podczas oczekiwania.'}
        $start=Get-Date
        $log="artifacts/truck-r3/reexport-$domain-$($start.ToString('yyyyMMdd-HHmmss')).log"
        & 'C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe' -b --factory-startup --threads 2 --python-exit-code 1 --python art-source/truck/exterior/qa/reexport_lod2_0115.py -- --domain $domain *> $log
        $code=$LASTEXITCODE
        if($code -ne 0 -or !(Select-String -LiteralPath $log -SimpleMatch "TRUCK_LOD2_REEXPORT: OK $domain" -Quiet)){throw "Nieudany reexport $domain, exit $code; nie instaluj częściowego LOD2."}
        if(((Get-FileHash -LiteralPath $inputs -Algorithm SHA256).Hash -join "`n") -ne $fp){throw 'Źródła zmienione podczas eksportu.'}
        $outputs=@(Get-ChildItem "art-source/truck/$domain/export" -Recurse -File | Where-Object {$_.Extension -in @('.fbx','.png','.json')} | Sort-Object FullName | Get-FileHash -Algorithm SHA256 | ForEach-Object {[ordered]@{path=$_.Path;sha256=$_.Hash}})
        [ordered]@{domain=$domain;result='Passed';seconds=((Get-Date)-$start).TotalSeconds;source_fingerprint=$fp;log=$log;threads=2;pool='heavy';owner='gpt-truck-r3';validated=$true;generation_id='disc-v3';regeneration_type='LOD2-only from verified full cache';outputs=$outputs} | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 "artifacts/truck-r3/generate-$domain-result.json"
        Add-Content -Encoding utf8 artifacts/truck-r3/STATUS.md "Reexport LOD2 $domain disc-v3 i natywny validator przeszły. Mapy i LOD0/1 byte-identyczne z v2. Następny krok: drugi pojazd, potem capture i oględziny zmiany tarcz oraz reszty geometrii."
        git add -f artifacts/truck-r3/STATUS.md "artifacts/truck-r3/generate-$domain-result.json"
        git commit --only artifacts/truck-r3/STATUS.md "artifacts/truck-r3/generate-$domain-result.json" -m "wip(truck): reexport tarcz Low $domain disc-v3"
    }
} finally {
    pwsh $slot -Release -Pool heavy -Owner gpt-truck-r3
}
