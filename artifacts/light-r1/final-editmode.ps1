$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$slot = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Owner gpt-light
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity' }
git diff --quiet HEAD -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
if ($LASTEXITCODE -ne 0) {
    & pwsh $slot -Release -Owner gpt-light
    throw 'Odmowa: niezacommitowane ustawienia sprzed Unity'
}
try {
    & pwsh scripts/test.ps1 -Platform EditMode *> artifacts/light-r1/final-editmode.log
    $code = $LASTEXITCODE
}
finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner gpt-light
}
Get-Content artifacts/light-r1/final-editmode.log -Tail 18
Add-Content artifacts/light-r1/STATUS.md "Końcowe EditMode: kod $code; szczegóły final-editmode.log i XML artifacts/tests. Następny krok: odczytać liczbę testów i ewentualne porażki."
git add -f artifacts/light-r1/STATUS.md
git commit -m 'WIP light r1: record final EditMode exit'
exit $code
