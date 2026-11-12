# Resume only the missing end-round stages; the product and already completed suites stay frozen.
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((& git branch --show-current).Trim() -ne 'gpt-asphalt-r2') { throw 'Wrong round' }
$live = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -eq 'pwsh.exe' -and $_.ProcessId -ne $PID -and
    $_.CommandLine -match 'artifacts[/\\]asphalt-r2[/\\](end-validation|run-heavy|run-gis|run-unity-stage)\.ps1'
})
if ($live.Count) { throw 'Another own validation wrapper is live; do not duplicate it.' }
$path = 'artifacts/asphalt-r2/validation-progress.json'
$results = Get-Content $path -Raw | ConvertFrom-Json -AsHashtable
if ($results.gis_exit -ne 0 -or $results.physics_gate3_exit -ne 1) { throw 'Unexpected completed-suite state; inspect before resuming.' }
$physics = Get-Content artifacts/asphalt-r2/physics-result.json -Raw | ConvertFrom-Json
if ($physics.passed -ne 47 -or $physics.failed -ne 1 -or @($physics.changed).Count) { throw 'Known physics result was not verified.' }
$inputs = @(& git diff --name-only 6832f50b -- game/Assets/_Project tools/worldgen art-source/world/materials/_src tests)
if ($inputs.Count) { throw "Product or test inputs changed since validation: $($inputs -join ', ')" }
if ($results.ContainsKey('fidelity_exit') -or $results.ContainsKey('editmode_exit')) { throw 'A remaining stage already has a result; inspect it instead of repeating.' }
$results.resumed_at = Get-Date -Format o
$results.resumed_reason = 'Own waiting wrapper rescheduled after more than one hour without a heavy slot; no running Python task interrupted.'
$results | ConvertTo-Json | Set-Content $path
& pwsh artifacts/asphalt-r2/run-heavy.ps1 -Stage Fidelity -Label candidate2-final -ReserveNext
$results.fidelity_exit = $LASTEXITCODE
$results | ConvertTo-Json | Set-Content $path
if ($results.fidelity_exit -ne 0) { throw 'Fidelity failed; read log before retrying or continuing.' }
$testStarted = Get-Date
& pwsh artifacts/asphalt-r2/run-unity-stage.ps1 -Stage Test -Label candidate2-final *> artifacts/asphalt-r2/candidate2-final-editmode.log
$results.editmode_exit = $LASTEXITCODE
$xml = Get-ChildItem artifacts/tests -Filter 'editmode-*.xml' | Where-Object LastWriteTime -ge $testStarted | Sort-Object LastWriteTime | Select-Object -Last 1
if ($xml) { Copy-Item -LiteralPath $xml.FullName artifacts/asphalt-r2/candidate2-final-editmode.xml }
else { $results.editmode_xml_missing = $true }
$results.finished = Get-Date -Format o
$results | ConvertTo-Json | Set-Content $path
Add-Content artifacts/asphalt-r2/STATUS.md "$(Get-Date -Format o): Pozostała sekwencja fidelity/EditMode zakończona. Surowe wyniki w validation-progress; przed przekazaniem wymagane odczytanie logów/XML i audyt."
git add -f artifacts/asphalt-r2/STATUS.md $path
git commit -q -m 'wip(asphalt): checkpoint remaining end-round validation results' 2> artifacts/asphalt-r2/git-checkpoint-warnings.log
if ($results.editmode_exit -ne 0 -or $results.editmode_xml_missing) { exit 1 }
exit 0
