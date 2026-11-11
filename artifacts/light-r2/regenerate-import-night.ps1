param([Parameter(Mandatory)][int]$AfterProcessId)
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$prior = Get-CimInstance Win32_Process -Filter "ProcessId=$AfterProcessId"
if ($prior -and ($prior.Name -ne 'pwsh.exe' -or $prior.CommandLine -notlike '*-Task Analyze -Script artifacts/light-r2/measure-lamps.py*')) {
    throw 'Proces poprzedzający nie jest własną analizą baseline r2'
}
if ($prior) { Wait-Process -Id $AfterProcessId }
if (-not (Test-Path -LiteralPath artifacts/light-r2/dusk-baseline-metrics.json)) { throw 'Brak ukończonej analizy baseline' }
$owner = (& git branch --show-current).Trim()
if ($owner -ne 'gpt-light-r2') { throw 'Niewłaściwa gałąź' }
$slot = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 5
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano heavy' }
$code = 1
try {
    & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> artifacts/light-r2/build-world.log
    if ($LASTEXITCODE -ne 0) { throw 'build_world nieudany' }
    if (Select-String -Path artifacts/light-r2/build-world.log -SimpleMatch 'fallback=True' -Quiet) { throw 'Niedozwolony fallback Megascans' }
    & uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art artifacts/light-r2/fidelity *> artifacts/light-r2/fidelity-preimport.log
    if ($LASTEXITCODE -ne 0) { throw 'fidelity nieudane' }
    & pwsh $slot -Acquire -Owner gpt-light
    if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano Unity' }
    git diff --quiet HEAD -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    if ($LASTEXITCODE -ne 0) {
        & pwsh $slot -Release -Owner gpt-light
        throw 'Import odmówiony: ustawienia zmienione przed Unity'
    }
    try {
        # import-region may invoke build_all; every nested Python invocation remains inside this heavy slot.
        & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> artifacts/light-r2/import-wrapper.log
        if ($LASTEXITCODE -ne 0) { throw 'Import nieudany' }
    }
    finally {
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
        & pwsh $slot -Release -Owner gpt-light
    }
    $code = 0
}
catch {
    $_ | Out-String | Add-Content artifacts/light-r2/regeneration-error.log
    Write-Output $_
}
finally { & pwsh $slot -Release -Pool heavy -Owner $owner }
Add-Content artifacts/light-r2/STATUS.md "Generator, fidelity i import r2: kod $code. Logi build-world.log, fidelity-preimport.log, import-wrapper.log. Następny krok: obejrzeć ablację Night, jeśli kod0; inaczej wyjaśnić błąd bez ponownego startu w ciemno."
git add -f artifacts/light-r2/STATUS.md
git commit -m 'WIP light r2: record generator and five-preset import result'
if ($code -ne 0) { exit $code }
& pwsh artifacts/light-r2/run-light-batch.ps1 -Jobs artifacts/light-r2/night-ablation.json
exit $LASTEXITCODE
