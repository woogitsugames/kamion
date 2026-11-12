# s13 final: waits for 'build exit=0' then import -> SBS + control renders (Low overcast, clear) -> EditMode.
param([string]$Name = 'merged')
$st = Join-Path $PSScriptRoot 'final-heavy.status'
$us = Join-Path $PSScriptRoot 'final-unity.status'
while (-not ((Test-Path $st) -and (Select-String -Path $st -Pattern '^build exit=' -Quiet))) { Start-Sleep 20 }
if (-not (Select-String -Path $st -Pattern '^build exit=0' -Quiet)) { 'build failed - unity chain skipped' | Add-Content $us; exit 1 }
$log = Join-Path $PSScriptRoot 'cycle-2.log'
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-import.ps1') -Log 'import-2.log' *> $log; "import done $(Get-Date -Format HH:mm:ss)" | Add-Content $us
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-sbs.ps1') -Name $Name -Lighting overcast *>> $log; "sbs overcast done $(Get-Date -Format HH:mm:ss)" | Add-Content $us
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-control.ps1') -Name $Name -Lighting overcast *>> $log; "control overcast done $(Get-Date -Format HH:mm:ss)" | Add-Content $us
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-sbs.ps1') -Name $Name -Lighting clear *>> $log
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-control.ps1') -Name $Name -Lighting clear *>> $log; "clear done $(Get-Date -Format HH:mm:ss)" | Add-Content $us
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-editmode.ps1') *>> $log; "editmode done $(Get-Date -Format HH:mm:ss)" | Add-Content $us
'done' | Set-Content (Join-Path $PSScriptRoot 'cycle-2.done')
