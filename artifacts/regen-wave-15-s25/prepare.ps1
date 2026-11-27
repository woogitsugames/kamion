param([switch]$Full)

. "$PSScriptRoot/common.ps1"
Initialize-WaveRuntime
$lock = Enter-WaveLock 'prepare'
try {
    $requested = if ($Full) { 'full' } else { 'targeted' }
    if (Test-Path -LiteralPath $scopeFile) {
        if ((Get-Content -LiteralPath $scopeFile -Raw).Trim() -ne $requested) {
            throw 'Zakres został już wybrany. Wznów prepare.ps1 z tym samym przełącznikiem.'
        }
    }
    else { Set-Content -LiteralPath $scopeFile -Value $requested }
    if (Test-Path -LiteralPath "$stateDir/prepare.done") { Write-Host 'Przygotowanie już zakończone.'; return }
    if (Get-ChildItem -LiteralPath "$stateDir/tiles" -Filter '*.world') {
        throw 'Regeneracja już się zaczęła. Zachowaj istniejącą bazę visual-QA.'
    }
    $log = "$evidenceDir/logs/prepare.log"
    if (-not (Test-Path -LiteralPath "$stateDir/before.done")) {
        Invoke-WaveStep 'audyt WN przed' $python (@('tools/worldgen/qa/hv_wires_audit.py',
            '--json', "$evidenceDir/hv_wires_before.json", '--regions') + $fullQueue.tile) $log
        & "$waveDir/vqa.ps1" -Phase before
        Set-Content -LiteralPath "$stateDir/before.done" -Value (Get-Date -Format o)
    }
    if (-not (Test-Path -LiteralPath "$stateDir/sources.done")) {
        if (@($sourcePaths | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) }).Count) {
            throw 'Brakuje co najmniej jednego pliku źródeł streetscape z fali 14.'
        }
        Invoke-WithHeavySlot "$waveName-sources" $log {
            Invoke-WaveStep 'migracja źródeł OSM' $python (@('tools/worldgen/streetscape/sources.py',
                '--refresh-power', '--regions') + $fullQueue.tile) $log
            foreach ($path in $sourcePaths) {
                $source = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json -AsHashtable
                if ($source.schema -ne 'truck-sim-pl/streetscape-sources/2') {
                    throw "Migracja nie uaktualniła schematu w $path."
                }
            }
        }
        Set-Content -LiteralPath "$stateDir/sources.done" -Value (Get-Date -Format o)
    }
    & "$waveDir/commit.ps1" -Sources
    Set-Content -LiteralPath "$stateDir/prepare.done" -Value (Get-Date -Format o)
}
finally { $lock.Dispose() }
