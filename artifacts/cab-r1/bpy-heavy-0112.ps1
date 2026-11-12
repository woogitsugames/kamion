param([Parameter(Mandatory)][string]$PythonFile,[Parameter(Mandatory)][string]$RunLog)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$owner=(git branch --show-current).Trim()
if ($owner -notmatch '^gpt-cab-r\d+$') { throw 'Tylko sesja cab.' }
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 5 -StaleHours 1000000
if ($LASTEXITCODE -ne 0) { throw 'Brak slotu heavy.' }
try {
    & 'C:/Users/matma/AppData/Local/Programs/Blender4.2/blender-4.2.9-windows-x64/blender.exe' -b --factory-startup --python-exit-code 1 --python $PythonFile *> $RunLog
    $code=$LASTEXITCODE
}
finally { pwsh $slot -Release -Pool heavy -Owner $owner }
exit $code
