param([ValidatePattern('^(baseline|result-0112(?:-[A-Za-z0-9-]+)?)$')][string]$Stage='baseline')
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((git branch --show-current) -ne 'gpt-cab-r2') { throw 'Tylko runda cab r1.' }
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slot -Acquire -Owner gpt-cab -PollSeconds 5 -StaleHours 1000000
if ($LASTEXITCODE -ne 0) { throw 'Brak slotu Unity.' }
try {
    pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Width 1920 -Height 1080 -Gate3 Data/Regions/bialystok-industrial-c/gate3_cameras.json -OutputDir "artifacts/cab-r2/$Stage/Low-route-all"
    $code=$LASTEXITCODE
}
finally { pwsh $slot -Release -Owner gpt-cab; git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
if ($code -ne 0) { throw "Błąd pełnej macierzy kamer: $code" }
Add-Content artifacts/cab-r2/STATUS.md "Zapisano ${Stage}: pełna macierz Low overcast z kamerami Gate3, osobne draws instancji w stats.txt. Następny krok: porównać pełne stats baseline/result-0112 i obejrzeć arkusze."
git add -f artifacts/cab-r2/STATUS.md
git commit -m "wip(cab): capture $Stage complete Low route camera budget"

