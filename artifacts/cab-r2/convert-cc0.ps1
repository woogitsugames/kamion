$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$owner=(git branch --show-current).Trim()
if ($owner -ne 'gpt-cab-r2') { throw 'Tylko runda cab r2.' }
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 5 -StaleHours 1000000
if ($LASTEXITCODE -ne 0) { throw 'Brak slotu heavy.' }
try {
    $env:UV_PROJECT_ENVIRONMENT='.venv-cab'
    uv run --project tools/worldgen python tools/blender/truck/interior/cc0_leather.py --output artifacts/cab-r2/cc0-candidate *> artifacts/cab-r2/cc0-convert.log
    $code=$LASTEXITCODE
}
finally { pwsh $slot -Release -Pool heavy -Owner $owner }
exit $code
