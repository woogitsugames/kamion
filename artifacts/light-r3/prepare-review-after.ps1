param([Parameter(Mandatory)][int]$AfterProcessId)
$ErrorActionPreference = 'Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
$prior = Get-CimInstance Win32_Process -Filter "ProcessId=$AfterProcessId"
if ($prior -and ($prior.Name -ne 'pwsh.exe' -or $prior.CommandLine -notlike '*artifacts/light-r3/regenerate-baseline.ps1*')) {
    throw 'Predecessor is not this round baseline pipeline'
}
while (Get-Process -Id $AfterProcessId -ErrorAction SilentlyContinue) { Start-Sleep -Seconds 5 }
$log = Get-ChildItem $PSScriptRoot -Filter 'baseline.*.log' | Sort-Object LastWriteTime | Select-Object -Last 1
if ($null -eq $log -or -not (Select-String -Path $log.FullName -SimpleMatch -Pattern 'LIGHT_QA_RESULT: OK jobs=14 rendered=40' -Quiet)) {
    throw 'Complete baseline40 required before contacts; inspect original pipeline, do not restart blindly'
}
& pwsh "$PSScriptRoot/review-baseline.ps1"
if ($LASTEXITCODE) { throw 'Contact preparation failed' }
Add-Content "$PSScriptRoot/STATUS.md" 'Baseline ma komplet 40 PNG i sprawdzone stany. Kontaktówki przygotowane po faktycznym końcu pipeline, bez dodatkowego Pythona lub Unity. Następny krok: obejrzeć wszystkie 36 wet0/0,5/1 i cztery clear; nie deklarować poprawy przed oględzinami.'
git add -f artifacts/light-r3/STATUS.md
git commit -m 'WIP light r3: record complete baseline review sheets'
exit 0
