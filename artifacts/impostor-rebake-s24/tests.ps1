param([string]$Label = 'editmode', [string]$Filter = '')
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
$wt = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$main = 'C:\Users\matma\Documents\Claude\kamion'
$L = "$wt\artifacts\impostor-rebake-s24\logs"
Set-Location $wt
while (Test-Path "$main\artifacts\locks\PHONE_RUN") { Start-Sleep 60 }
pwsh -NoProfile -File "$wt\scripts\unity-slot.ps1" -Acquire -Owner impostor-rebake-s24 *>> "$L\tests-$Label.log"
try {
    $a = @{Platform = 'EditMode'; BuildTarget = 'Win64'}
    if ($Filter) { $a.Filter = $Filter }
    pwsh -NoProfile -File scripts/test.ps1 @a *>> "$L\tests-$Label.log"; $c = $LASTEXITCODE
} finally {
    pwsh -NoProfile -File "$wt\scripts\unity-slot.ps1" -Release -Owner impostor-rebake-s24 *>> "$L\tests-$Label.log"
}
Add-Content "$L\tests-$Label.status" "exit=$c DONE"
