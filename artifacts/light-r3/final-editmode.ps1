param([string]$Filter)
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$slot = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$label = if ($Filter) { 'targeted-editmode' } else { 'final-editmode' }
$log = "artifacts/light-r3/$label.log"
& pwsh $slot -Acquire -Owner gpt-light -PollSeconds 1 -StaleHours 87600
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity' }
git diff --quiet HEAD -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
if ($LASTEXITCODE -ne 0) {
    & pwsh $slot -Release -Owner gpt-light
    throw 'Odmowa: niezacommitowane ustawienia sprzed Unity'
}
try {
    & pwsh scripts/test.ps1 -Platform EditMode -Filter $Filter *> $log
    $code = $LASTEXITCODE
}
finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner gpt-light
}
Get-Content $log -Tail 18
Add-Content artifacts/light-r3/STATUS.md "EditMode (filtr='$Filter'): kod $code; szczegóły $log i XML artifacts/tests. Następny krok: odczytać liczbę testów i ewentualne porażki."
git add -f artifacts/light-r3/STATUS.md
git commit -m 'WIP light r3: record EditMode exit'
exit $code





