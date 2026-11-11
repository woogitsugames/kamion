$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slot -Acquire -Pool heavy -Owner gpt-cab-r1 -PollSeconds 5 -StaleHours 1000000
if ($LASTEXITCODE -ne 0) { throw 'Brak slotu heavy.' }
try {
    & 'C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe' -b --factory-startup --python-exit-code 1 --python artifacts/cab-r1/audit-seat-intersections.py *> artifacts/cab-r1/seat-intersections.log
    $code=$LASTEXITCODE
}
finally { pwsh $slot -Release -Pool heavy -Owner gpt-cab-r1 }
exit $code
