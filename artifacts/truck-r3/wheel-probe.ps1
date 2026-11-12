param([string]$Prefix='wheel-probe-v1',[string[]]$Modes=@('flat','albedo','geonormal'))
$ErrorActionPreference='Stop'
[Diagnostics.Process]::GetCurrentProcess().PriorityClass='BelowNormal'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ($Prefix -notmatch '^[a-z0-9-]+$') { throw 'Nieprawidłowy Prefix.' }
$Modes=@($Modes | ForEach-Object {$_.Split(',')})
if (@($Modes | Where-Object {$_ -notin @('flat','albedo','geonormal','mappednormal','atlas-mask','uv')}).Count) { throw 'Nieznany kanał.' }
uv run --project tools/worldgen python art-source/truck/exterior/qa/prepare_wheel_probe_0115.py
if ($LASTEXITCODE -ne 0) { throw 'Nie przygotowano adaptera.' }
. scripts/env.ps1
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
function Fingerprint {
    ((Get-FileHash -LiteralPath @('game/Assets/_Project/Rendering/Shaders/TruckExterior.shader','game/Assets/_Generated/TruckQa0115/Editor/TruckWheelProbe0115.cs','game/Assets/_Generated/TruckQa0115/Editor/TruckWheelMeshAudit0115.cs',$PSCommandPath) -Algorithm SHA256).Hash -join "`n")
}
foreach($mode in $Modes) {
    $name="$Prefix-$mode"
    $dir="artifacts/truck-r3/$name"
    $marker="$dir/complete.ok"
    $fp=Fingerprint
    if (Test-Path $marker) {
        if ((Get-Content $marker -Raw).Trim() -ne $fp.Trim() -or @(Get-ChildItem $dir -Recurse -Filter '*.png').Count -ne 4) { throw 'Kod podglądu zmieniony lub niepełne kadry; wybierz nowy Prefix.' }
        continue
    }
    pwsh $slot -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 1
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
    $start=Get-Date
    try {
        $log="artifacts/truck-r3/$name-$(Get-Timestamp).log"
        $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckWheelProbe0115.RunBatch','-truckRound',$name,'-truckOutputRoot','artifacts/truck-r3','-truckCameras','truck-wheel-detail,truck-mudguard-detail','-truckTiers','Low,High','-truckLights','overcast','-truckMeshProbe',$mode,'-wheelAuditOutput','artifacts/truck-r3/wheel-mesh-before.json')
        $result=Select-String -LiteralPath $log -SimpleMatch "TRUCK_ROUND_RESULT: OK $name count=4" | Select-Object -Last 1
        $sha=(Get-FileHash game/Assets/_Project/Rendering/Shaders/TruckExterior.shader -Algorithm SHA256).Hash.ToLowerInvariant()
        $cleanup=Select-String -LiteralPath $log -SimpleMatch "TRUCK_ABLATION_CLEANUP: productionSHA=$sha" -Quiet
        $fresh=@(Get-ChildItem $dir -Recurse -Filter '*.png' -ErrorAction SilentlyContinue | Where-Object LastWriteTime -ge $start).Count
        if ($code -ne 0 -and $result -and $cleanup -and $fresh -eq 4) {
            $mono=Select-String -LiteralPath $log -SimpleMatch 'Cleanup mono' | Where-Object LineNumber -gt $result.LineNumber | Select-Object -First 1
            $abort=Select-String -LiteralPath $log -SimpleMatch 'abort_threads: Failed aborting' | Where-Object LineNumber -gt $result.LineNumber | Select-Object -First 1
            $fatal=Select-String -LiteralPath $log -Pattern 'Crash!!!|Obtained \d+ stack frames|Fatal Error|error CS\d+|Shader error' -Quiet
            if($mono -and $abort -and !$fatal){$code=0} # ADR0083, only after actual success and cleanup.
        }
        if($code -ne 0 -or !$result -or !$cleanup -or $fresh -ne 4 -or (Fingerprint) -ne $fp){throw "Nieudany probe $name, exit $code."}
        Set-Content -Encoding utf8 $marker $fp
    } finally {
        pwsh $slot -Release -Owner gpt-truck
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
    Add-Content -Encoding utf8 artifacts/truck-r3/STATUS.md "Zapisano podgląd $name, cztery świeże kadry Low/High overcast, materiały przywrócone. Następny krok: obejrzeć kanały w arkuszach 960 px, nie wnioskować z samych liczb."
    git add -f artifacts/truck-r3/STATUS.md
    git commit --only artifacts/truck-r3/STATUS.md -m "wip(truck): podglad kola $mode"
}
