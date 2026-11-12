param([Parameter(Mandatory=$true)][int]$GeometryPid)
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r2/24h'
$geometry=Get-CimInstance Win32_Process -Filter "ProcessId=$GeometryPid"
if ($geometry) {
    if ($geometry.CommandLine -notmatch 'furniture-r2/24h/heavy-step.ps1.*-Step geometry') {
        throw 'Refuse to wait on a process outside the owned geometry step'
    }
    # Only one heavy task of this owner may acquire at once; same-owner acquisition refreshes a slot.
    Wait-Process -Id $GeometryPid -ErrorAction SilentlyContinue
}
Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): proces własnego porównania geometrii zakończony. Jego wynik wymaga odczytu; teraz kolejno przygotowanie arkuszy w slocie heavy, bez równoległego ciężkiego zadania tego samego właściciela."
Copy-Item "$ev/STATUS.md" artifacts/furniture-r2/STATUS.md
git add -f "$ev/STATUS.md" artifacts/furniture-r2/STATUS.md
git commit -m 'wip(furniture): serialize sheet preparation after geometry process'
& pwsh "$ev/heavy-step.ps1" -Step compare -Phase after3
if ($LASTEXITCODE -ne 0) { throw 'Comparison sheets failed; inspect compare-after3.log' }
