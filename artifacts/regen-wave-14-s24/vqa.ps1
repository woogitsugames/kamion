param([Parameter(Mandatory)][ValidateSet('before','after')][string]$Phase)

. "$PSScriptRoot/common.ps1"
Initialize-WaveRuntime
foreach ($tile in $qaTiles) {
    if ($Phase -eq 'after' -and -not (Test-Path -LiteralPath "$stateDir/tiles/$tile.done")) {
        throw "Brak ukończonego kafla $tile."
    }
    $log = "$evidenceDir/logs/vqa-$Phase-$tile.log"
    $scene = if ($tile -eq 'bialystok-industrial-c') { 'WorldC_High' } else { "World_${tile}_High" }
    Invoke-WaveUnity "$waveName-vqa" $log {
        if ($Phase -eq 'before') { Invoke-WaveImport $tile $log }
        foreach ($lighting in @('clear','overcast')) {
            $destination = "$evidenceDir/vqa/$Phase/$tile/High-$lighting"
            Invoke-WaveStep "visual-qa $lighting" 'pwsh' @('-NoProfile', '-File', 'scripts/visual-qa.ps1', '-Scene', $scene,
                '-BuildTarget', 'Win64', '-Tier', 'High', '-Pc', '-Width', '1920', '-Height', '1080',
                '-Neighbours', 'none', '-Lighting', $lighting, '-OutputDir', $destination) $log
            if (-not (Get-ChildItem -LiteralPath $destination -Filter '*.png' -File)) {
                throw "Visual-QA nie zapisał PNG w $destination."
            }
        }
    }
}
