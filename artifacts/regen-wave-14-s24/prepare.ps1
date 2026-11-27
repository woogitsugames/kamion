. "$PSScriptRoot/common.ps1"
Initialize-WaveRuntime
$lock = Enter-WaveLock 'prepare'
try {
    if (Test-Path -LiteralPath "$stateDir/prepare.done") { Write-Host 'Przygotowanie już zakończone.'; return }
    if (Get-ChildItem -LiteralPath "$stateDir/tiles" -Filter '*.world') {
        throw 'Regeneracja już się zaczęła. Zachowaj istniejącą bazę visual-QA.'
    }
    if (-not (Test-Path -LiteralPath "$stateDir/before.done")) {
        Invoke-WaveStep 'audyt WN przed' $python (@('tools/worldgen/qa/hv_wires_audit.py',
            '--json', "$evidenceDir/hv_wires_before.json", '--regions') + $queue.tile) "$evidenceDir/logs/prepare.log"
        & "$waveDir/vqa.ps1" -Phase before
        Set-Content -LiteralPath "$stateDir/before.done" -Value (Get-Date -Format o)
    }
    if (-not (Test-Path -LiteralPath "$stateDir/profile.done")) {
        Invoke-WaveStep 'tree_crown_profile --write' $python @('tools/worldgen/streetscape/tree_crown_profile.py', '--write') "$evidenceDir/logs/prepare.log"
        Set-Content -LiteralPath "$stateDir/profile.done" -Value (Get-Date -Format o)
    }
    & "$waveDir/commit.ps1" -Profile
    Set-Content -LiteralPath "$stateDir/prepare.done" -Value (Get-Date -Format o)
}
finally { $lock.Dispose() }
