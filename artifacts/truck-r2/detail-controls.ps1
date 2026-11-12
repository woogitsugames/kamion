param([string]$Prefix = 'detail-before', [string[]]$Cases = @('washed','fleet','dirty'))
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ($Prefix -notmatch '^[a-z0-9-]+$') { throw 'Nieprawidłowa nazwa kontroli.' }
$Cases = @($Cases | ForEach-Object { $_.Split(',') })
$amounts = @{washed='0';fleet='0.5';dirty='1'}
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
uv run --project tools/worldgen python art-source/truck/exterior/qa/prepare_detail_0115.py
if ($LASTEXITCODE -ne 0) { throw 'Nie przygotowano kontroli.' }
. scripts/env.ps1
function Fingerprint {
    ((Get-FileHash -Algorithm SHA256 -LiteralPath @('game/Assets/_Project/Rendering/Shaders/TruckExterior.shader','game/Assets/_Project/Rendering/Shaders/TruckGlass.shader','game/Assets/_Project/Vehicle/Runtime/TruckLights.cs','game/Assets/_Project/Editor/VisualQA/TruckPaintRound.cs','art-source/truck/exterior/qa/prepare_round_0115.py','art-source/truck/exterior/qa/prepare_detail_0115.py',$PSCommandPath)).Hash -join "`n")
}
foreach ($case in $Cases) {
    if (!$amounts.ContainsKey($case)) { throw 'Nieznany poziom zabrudzenia.' }
    $round = "$Prefix-$case"
    $marker = "artifacts/truck-r2/$round/complete.ok"
    $fingerprint = Fingerprint
    if (Test-Path $marker) {
        if ((Get-Content $marker -Raw).Trim() -ne $fingerprint.Trim()) { throw 'Kod kontroli zmieniony; wybierz nowy Prefix.' }
        if (@(Get-ChildItem "artifacts/truck-r2/$round" -Recurse -Filter '*.png').Count -ne 12) { throw 'Niekompletny zapis kontroli.' }
        continue
    }
    pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 1
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
    try {
        $runStart = Get-Date
        $log = "artifacts/truck-r2/$round-$(Get-Timestamp).log"
        $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.TruckDetail0115.RunBatch','-truckRound',$round,'-truckOutputRoot','artifacts/truck-r2','-truckCameras','truck-step-detail,truck-mudguard-detail,truck-wheel-detail','-truckTiers','Low,High','-truckLights','overcast,clear','-truckDirt',$amounts[$case])
        $result = Select-String -LiteralPath $log -Pattern ("^TRUCK_ROUND_RESULT: OK " + [regex]::Escape($round) + " count=12$") | Select-Object -Last 1
        $fresh = @(Get-ChildItem "artifacts/truck-r2/$round" -Recurse -Filter '*.png' -ErrorAction SilentlyContinue | Where-Object LastWriteTime -ge $runStart).Count
        $productionSha = (Get-FileHash game/Assets/_Project/Rendering/Shaders/TruckExterior.shader -Algorithm SHA256).Hash.ToLowerInvariant()
        $cleanup = Select-String -LiteralPath $log -SimpleMatch "TRUCK_ABLATION_CLEANUP: productionSHA=$productionSha" -Quiet
        # Only the same two documented post-success shutdown flakes as visual-qa / ADR 0051 and 0083.
        if ($code -eq -1073741819 -and $result -and $cleanup -and $fresh -eq 12 -and (Select-String -LiteralPath $log -SimpleMatch 'D3D12PipelineCacheLibrary::SaveCache' -Quiet)) { $code = 0 }
        if ($code -ne 0 -and $result -and $cleanup -and $fresh -eq 12) {
            $mono = Select-String -LiteralPath $log -SimpleMatch 'Cleanup mono' | Where-Object LineNumber -gt $result.LineNumber | Select-Object -First 1
            $abort = Select-String -LiteralPath $log -SimpleMatch 'abort_threads: Failed aborting' | Where-Object LineNumber -gt $result.LineNumber | Select-Object -First 1
            $crash = Select-String -LiteralPath $log -Pattern 'Crash!!!|Obtained \d+ stack frames|Fatal Error|error CS\d+' -Quiet
            if ($mono -and $abort -and !$crash) { $code = 0 }
        }
        if ($code -ne 0 -or !$result -or !$cleanup -or $fresh -ne 12 -or (Fingerprint) -ne $fingerprint) { throw "Nieudana kontrola $round, exit $code." }
    }
    finally {
        pwsh $slotScript -Release -Owner gpt-truck
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
    $fingerprint | Set-Content -Encoding utf8 $marker
    Add-Content -Encoding utf8 artifacts/truck-r2/STATUS.md "Zapisano $round, ilość brudu $($amounts[$case]), 12 świeżych kadrów. Materiały przywrócone. Następny krok: porównać pas zabrudzenia, błotniki i plandekę ze zdjęciami."
    git add -f artifacts/truck-r2/STATUS.md
    git commit --only artifacts/truck-r2/STATUS.md -m "wip(truck): kontrola zabrudzenia $round"
}
