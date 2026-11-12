param([ValidatePattern('^[a-z0-9-]+$')][string]$Prefix='glass-before',[string[]]$Cases=@('baseline','no-pane','radiance-off','transmission'))
$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$Cases=@($Cases | ForEach-Object {$_.Split(',')})
if(@($Cases | Where-Object {$_ -notin @('baseline','no-pane','radiance-off','transmission')}).Count){throw 'Nieznana kontrola szyby.'}
$env:OPENBLAS_NUM_THREADS='1';$env:OMP_NUM_THREADS='1';$env:MKL_NUM_THREADS='1'
uv run --project tools/worldgen python art-source/truck/exterior/qa/prepare_glass_0115.py
if($LASTEXITCODE -ne 0){throw 'Nie przygotowano adaptera szkła.'}
. scripts/env.ps1
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
function Fingerprint {
    $files=@('game/Assets/_Project/Rendering/Shaders/TruckGlass.shader','game/Assets/_Project/Rendering/Shaders/KamionVehicleEnv.hlsl','game/Assets/_Generated/TruckQa0115/Editor/TruckGlassRound0115.cs','art-source/truck/exterior/qa/prepare_glass_0115.py',$PSCommandPath)
    ((Get-FileHash -LiteralPath $files -Algorithm SHA256).Hash -join "`n")
}
foreach($case in $Cases){
    $stage="$Prefix-$case";$dir="artifacts/truck-r4/$stage";$fp=Fingerprint
    if(Test-Path "$dir/complete.ok"){throw 'Nie nadpisuj dowodu; wybierz nowy Prefix lub Cases.'}
    if(Test-Path $dir){throw 'Istnieje częściowy etap; zbadaj log i wybierz nowy Prefix.'}
    $argsList=@('-executeMethod','Game.Editor.VisualQA.TruckGlassRound0115.RunBatch','-truckRound',$stage,'-truckOutputRoot','artifacts/truck-r4','-truckCameras','truck-front,truck-34,cab-driver','-truckTiers','Low,High','-truckLights','overcast,clear','-truckGlassAudit','1')
    if($case -eq 'no-pane'){$argsList+=@('-truckNoPane','windscreen')}
    if($case -eq 'radiance-off'){$argsList+=@('-truckGlassProbe','near-radiance-off')}
    if($case -eq 'transmission'){$argsList+=@('-truckGlassProbe','near-transmission')}
    pwsh $slot -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 1
    if($LASTEXITCODE -ne 0){throw 'Nie uzyskano slotu Unity.'}
    try {
        $log="artifacts/truck-r4/$stage-$(Get-Timestamp).log"
        $code=Invoke-UnityBatch -LogFile $log -Arguments $argsList
        if($code -ne 0 -or !(Select-String -LiteralPath $log -SimpleMatch 'TRUCK_ROUND: OK' -Quiet)){throw "Nieudana kontrola $case."}
        if((Fingerprint) -ne $fp){throw 'Kod zmieniony podczas kontroli.'}
        if(@(Get-ChildItem $dir -Recurse -Filter '*.png').Count -ne 12){throw 'Niepełne świeże kadry kontroli szkła.'}
        foreach($condition in @('Low-overcast','High-overcast','Low-clear','High-clear')){
            foreach($name in @('glass-mesh-audit.json','glass-material-bindings.json')){
                if(!(Test-Path "$dir/$condition/$name")){throw "Brak rzeczywistego audytu: $condition/$name"}
            }
        }
    } finally {
        pwsh $slot -Release -Owner gpt-truck
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
    $fp | Set-Content "$dir/complete.ok" -Encoding utf8
    Add-Content artifacts/truck-r4/STATUS.md "Kontrola szkła $stage: 12 świeżych kadrów, obie ścieżki, audyty materiałów po renderze. Przywrócenie materiałów w finally adaptera, ustawień w wrapperze. Kanały High po postprocessingu, bez twierdzenia o surowej transmisji. Następny krok: pary i odczyt parametrów."
    git add -f artifacts/truck-r4/STATUS.md
    git commit --only artifacts/truck-r4/STATUS.md -m "wip(truck): kontrola szkla $case"
    if($LASTEXITCODE -ne 0){throw 'Nie zapisano kontroli.'}
}
