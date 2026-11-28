# s25: po błędzie fidelity (ścieżka --art poza worktree) — powtórz samo fidelity w slocie heavy, ustaw znacznik .world
# (build_world/far_field/export-route już zakończone), potem łańcuch wznawia się od importu.
# Zabezpieczenia (review s25 #3): blokada kafla jak w Invoke-WaveTile oraz wymagane `END <etap> exit=0`
# dla build_world, far_field i export-route po ostatnim `BEGIN build_world` w logu kafla.
param([Parameter(Mandatory)][string]$Tile, [Parameter(Mandatory)][ValidatePattern('^[A-E]$')][string]$Chain)
. "$PSScriptRoot/common.ps1"
Initialize-WaveRuntime
$entry = $queue | Where-Object tile -eq $Tile
if (-not $entry -or $entry.chain -ne $Chain) { throw "Kafel $Tile nie należy do łańcucha $Chain." }
$log = "$evidenceDir/logs/tile-$Tile.log"
$worldReady = "$stateDir/tiles/$Tile.world"
$lock = Enter-WaveLock "tiles/$Tile"
try {
    if (-not (Test-Path -LiteralPath $worldReady)) {
        $lines = @(Get-Content -LiteralPath $log)
        $start = -1
        for ($i = $lines.Count - 1; $i -ge 0; $i--) { if ($lines[$i] -match 'BEGIN build_world') { $start = $i; break } }
        if ($start -lt 0) { throw "Brak BEGIN build_world w $log." }
        $tail = $lines[$start..($lines.Count - 1)]
        foreach ($step in 'build_world', 'far_field', 'export-route') {
            if (-not ($tail -match "END $step exit=0 ")) { throw "Etap $step nie zakończył się exit=0 w bieżącym przebiegu ($log)." }
        }
        Invoke-WithHeavySlot "$waveName-$Tile" $log {
            Invoke-WaveStep 'fidelity (resume s25)' $python @('tools/worldgen/fidelity/run.py', '--region', $Tile, '--art', "artifacts/$waveName/fidelity/$Tile") $log
        }
        Set-Content -LiteralPath $worldReady -Value (Get-Date -Format o)
    }
}
finally { $lock.Dispose() }
& "$PSScriptRoot/chain.ps1" -Chain $Chain
