$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$owner = (git branch --show-current).Trim()
if ($owner -ne 'gpt-light-r3') { throw 'Expected round3 branch' }
$slot = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$env:PYTHONUNBUFFERED='1'
$env:OMP_NUM_THREADS='1'; $env:OPENBLAS_NUM_THREADS='1'; $env:MKL_NUM_THREADS='1'; $env:NUMEXPR_NUM_THREADS='1'
& pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 5
if ($LASTEXITCODE) { throw 'No heavy slot' }
$code=1
try {
    & uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$PSScriptRoot/build-world.log"
    if ($LASTEXITCODE) { throw 'build_world failed' }
    if (Select-String "$PSScriptRoot/build-world.log" -SimpleMatch 'fallback=True' -Quiet) { throw 'Megascans fallback forbidden' }
    & uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c --art "$PSScriptRoot/fidelity" *> "$PSScriptRoot/fidelity-preimport.log"
    if ($LASTEXITCODE) { throw 'fidelity failed' }
    # Import may build missing material sets first: retain heavy for that nested sequential Python work.
    & pwsh $slot -Acquire -Owner gpt-light
    if ($LASTEXITCODE) { throw 'No Unity slot' }
    git diff --quiet HEAD -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    if ($LASTEXITCODE) {
        & pwsh $slot -Release -Owner gpt-light
        throw 'Import settings changed before Unity; refuse automatic cleanup'
    }
    try {
        & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "$PSScriptRoot/import-wrapper.log"
        if ($LASTEXITCODE) { throw 'Import failed' }
    }
    finally {
        git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
        & pwsh $slot -Release -Owner gpt-light
    }
    $code=0
}
catch { $_ | Out-String | Add-Content "$PSScriptRoot/regeneration-error.log"; Write-Output $_ }
finally { & pwsh $slot -Release -Pool heavy -Owner $owner }
Add-Content "$PSScriptRoot/STATUS.md" "Regeneracja i import r3 zakończone kodem $code; build-world.log, fidelity-preimport.log, import-wrapper.log. Baseline dopiero po sukcesie; bez deklaracji jakości z kodu wyjścia."
git add -f artifacts/light-r3/STATUS.md
git commit -m 'WIP light r3: record regenerated baseline import result'
if ($code) { exit $code }
& pwsh "$PSScriptRoot/run-light-batch.ps1" -Jobs artifacts/light-r3/baseline.json -Gate3 artifacts/light-r3/qa-cameras.json
exit $LASTEXITCODE
