param([string]$Filter='Game.Tests.EditMode.CabBacklightTests',[switch]$Full)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slot -Acquire -Owner gpt-cab -PollSeconds 5 -StaleHours 1000000
if ($LASTEXITCODE -ne 0) { throw 'Brak slotu Unity.' }
try {
    $argsTests=@('scripts/test.ps1','-Platform','EditMode')
    if (-not $Full) { $argsTests+=@('-Filter',$Filter) }
    & pwsh @argsTests
    $code=$LASTEXITCODE
}
finally { pwsh $slot -Release -Owner gpt-cab; git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
exit $code

