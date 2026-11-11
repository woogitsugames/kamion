param(
    [ValidatePattern('^[a-z0-9-]+$')] [string]$Prefix = 'control',
    [string[]]$Cases = @('white-on', 'white-off', 'dark-on', 'dark-off', 'no-pane')
)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
uv run --project tools/worldgen python art-source/truck/exterior/qa/prepare_round_0115.py
if ($LASTEXITCODE -ne 0) { throw 'Nie przygotowano diagnostyki.' }
. scripts/env.ps1
function SourceFingerprint {
    ((Get-FileHash -Algorithm SHA256 -LiteralPath @('game/Assets/_Project/Rendering/Shaders/TruckExterior.shader','game/Assets/_Project/Rendering/Shaders/TruckGlass.shader','game/Assets/_Project/Vehicle/Runtime/TruckLights.cs')).Hash -join "`n")
}
foreach ($case in $Cases) {
    if ($case -notin @('white-on','white-off','dark-on','dark-off','no-pane')) { throw "Nieznana kontrola: $case" }
    $round = "$Prefix-$case"
    $fingerprint = SourceFingerprint
    $marker = "artifacts/truck-r1/$round/complete.ok"
    if (Test-Path $marker) {
        if ((Get-Content -LiteralPath $marker -Raw).Trim() -ne $fingerprint.Trim()) { throw "Zmienił się kod wejściowy istniejącej kontroli $round; użyj nowego Prefix." }
        continue
    }
    $lighting = if ($case -eq 'no-pane') { 'overcast' } else { 'overcast,clear' }
    $argsForUnity = @('-executeMethod', 'Game.Editor.VisualQA.TruckRound0115.RunBatch', '-truckRound', $round, '-truckOutputRoot', 'artifacts/truck-r1', '-truckCameras', 'truck-34,truck-side,truck-front', '-truckTiers', 'Low,High', '-truckLights', $lighting)
    if ($case.StartsWith('dark')) { $argsForUnity += @('-truckPigment', '0.08') }
    if ($case.EndsWith('off')) { $argsForUnity += @('-truckCoatRadianceOff', '1') }
    if ($case -eq 'no-pane') { $argsForUnity += @('-truckNoPane', 'windscreen') }
    pwsh $slotScript -Acquire -Owner gpt-truck -StaleHours 100000 -PollSeconds 5
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity.' }
    try {
        $log = "artifacts/truck-r1/$round-$(Get-Timestamp).log"
        $runStart = Get-Date
        $code = Invoke-UnityBatch -LogFile $log -Arguments $argsForUnity
        $expected = if ($case -eq 'no-pane') { 6 } else { 12 }
        $result = Select-String -LiteralPath $log -Pattern ("^TRUCK_ROUND_RESULT: OK " + [regex]::Escape($round) + " count=$expected$") | Select-Object -Last 1
        $resultOk = $null -ne $result
        $fresh = @(Get-ChildItem "artifacts/truck-r1/$round" -Recurse -Filter '*.png' -ErrorAction SilentlyContinue | Where-Object LastWriteTime -ge $runStart).Count
        $productionSha = (Get-FileHash game/Assets/_Project/Rendering/Shaders/TruckExterior.shader -Algorithm SHA256).Hash.ToLowerInvariant()
        $cleanup = Select-String -LiteralPath $log -SimpleMatch "TRUCK_ABLATION_CLEANUP: productionSHA=$productionSha" -Quiet
        # Same narrowly documented exception as visual-qa.ps1 / ADR 0051. No generic crash acceptance.
        if ($code -eq -1073741819 -and $resultOk -and $cleanup -and $fresh -eq $expected -and
            (Select-String -LiteralPath $log -SimpleMatch 'D3D12PipelineCacheLibrary::SaveCache' -Quiet)) { $code = 0 }
        # ADR 0083: the second documented shutdown flake, AFTER the result and mono cleanup, with no crash stack.
        if ($code -ne 0 -and $resultOk -and $cleanup -and $fresh -eq $expected) {
            $mono = Select-String -LiteralPath $log -SimpleMatch 'Cleanup mono' | Where-Object LineNumber -gt $result.LineNumber | Select-Object -First 1
            $abort = Select-String -LiteralPath $log -SimpleMatch 'abort_threads: Failed aborting' | Where-Object LineNumber -gt $result.LineNumber | Select-Object -First 1
            $crash = Select-String -LiteralPath $log -Pattern 'Crash!!!|Obtained \d+ stack frames|Fatal Error|error CS\d+' -Quiet
            if ($mono -and $abort -and !$crash) { $code = 0 }
        }
        if ($code -ne 0 -or !$resultOk -or !$cleanup -or $fresh -ne $expected -or (SourceFingerprint) -ne $fingerprint) {
            throw "Nieudana kontrola $case; exit $code. Zachowano log."
        }
    }
    finally {
        pwsh $slotScript -Release -Owner gpt-truck
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
    $fingerprint | Set-Content -Encoding utf8 -LiteralPath $marker
    Add-Content -Encoding utf8 artifacts/truck-r1/STATUS.md "Zapisano kontrolę pigmentu $case. Następny krok: porównać amplitudę odbicia ON/OFF i wybrać poprawkę lakieru na podstawie wyniku."
    git add -f artifacts/truck-r1/STATUS.md
    git commit -m "wip(truck): kontrola pigmentu $case"
}
