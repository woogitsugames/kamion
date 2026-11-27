# s25: po błędzie fidelity (ścieżka --art poza worktree) — powtórz samo fidelity w slocie heavy, ustaw znacznik .world
# (build_world/far_field/export-route już zakończone), potem łańcuch wznawia się od importu.
param([Parameter(Mandatory)][string]$Tile, [Parameter(Mandatory)][ValidatePattern('^[A-E]$')][string]$Chain)
. "$PSScriptRoot/common.ps1"
Initialize-WaveRuntime
$log = "$evidenceDir/logs/tile-$Tile.log"
$worldReady = "$stateDir/tiles/$Tile.world"
if (-not (Test-Path -LiteralPath $worldReady)) {
    Invoke-WithHeavySlot "$waveName-$Tile" $log {
        Invoke-WaveStep 'fidelity (resume s25)' $python @('tools/worldgen/fidelity/run.py', '--region', $Tile, '--art', "artifacts/$waveName/fidelity/$Tile") $log
    }
    Set-Content -LiteralPath $worldReady -Value (Get-Date -Format o)
}
& "$PSScriptRoot/chain.ps1" -Chain $Chain
