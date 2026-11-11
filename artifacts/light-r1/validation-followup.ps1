param([int]$RcasProcessId = 93600)
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
if (Get-Process -Id $RcasProcessId -ErrorAction SilentlyContinue) {
    Write-Output "Czekam na własny proces ablacji RCAS: $RcasProcessId"
    Wait-Process -Id $RcasProcessId
}
foreach ($lighting in @('clear','overcast')) {
    foreach ($sharp in @('0','0.25','0.5','0.75')) {
        $dir = "artifacts/light-r1/rcas/High-$lighting-$sharp"
        if (-not (Test-Path "$dir/stats.txt") -or @(Get-ChildItem $dir -Filter '*.png' -ErrorAction SilentlyContinue).Count -ne 5) {
            throw "Niepełna ablacja: $dir. Nie uruchamiam importu przed wyjaśnieniem wyniku."
        }
    }
}
& pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-light
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu importu' }
try {
    & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c
    if ($LASTEXITCODE -ne 0) { throw "Import nieudany: $LASTEXITCODE" }
}
finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-light
}
Add-Content artifacts/light-r1/STATUS.md 'Import świeżego świata zakończony. Następny krok: cloud-smoke.json w LightQaBatch i testy EditMode.'
git add -f artifacts/light-r1/STATUS.md
git commit -m 'wip(light): zaimportuj swiezy swiat przed weryfikacja nieba'
& pwsh artifacts/light-r1/run-light-batch.ps1 -Jobs artifacts/light-r1/cloud-smoke.json
if ($LASTEXITCODE -ne 0) { throw "Smoke batch nieudany: $LASTEXITCODE" }
& pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-light
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu EditMode' }
try {
    & pwsh scripts/test.ps1 -Platform EditMode
    if ($LASTEXITCODE -ne 0) { throw "EditMode nieudany: $LASTEXITCODE" }
}
finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-light
}
Add-Content artifacts/light-r1/STATUS.md 'EditMode zakończony bez błędów. Następny krok: obejrzeć wszystkie PNG smoke, porównać niebo ze zdjęciami i wybrać dalszą poprawkę.'
git add -f artifacts/light-r1/STATUS.md
git commit -m 'wip(light): zapisz pelne EditMode po zmianie nieba'
