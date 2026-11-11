param([string]$Phase = 'before', [string]$Rq = '', [switch]$LowSunOnly, [switch]$Targeted)
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
$main = 'C:/Users/matma/Documents/Claude/kamion'
function Assert-UnitySlot {
    if (Test-Path "$main/artifacts/locks/PHONE_RUN") { throw 'Main PHONE_RUN lock exists; do not launch Unity.' }
    $ours = Get-CimInstance Win32_Process -Filter "Name='Unity.exe'" | Where-Object { $_.CommandLine -like "*$repo/game*" -or $_.CommandLine -like "*$($repo.Replace('/','\'))\game*" }
    if ($ours) { throw 'Unity is already running for this worktree.' }
}
$cameras = 'driver-andersa-to-putry,route-putry-approach,photo-biezenstwa-ground,dk8-dk19-exit,stretch-04,stretch-05-docks,r10_house_2,r10_block_3,r10_block_4,r10_hall_2,r10_hall_3'
foreach ($tier in @('Low','High')) {
    $conditions = if ($LowSunOnly) { @('lowsun') } else { @('clear','overcast') }
    foreach ($light in $conditions) {
        Assert-UnitySlot
        $scene = if ($tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
        $argsQa = @('-Scene', $scene, '-Tier', $tier, '-Lighting', $light, '-Gate3', 'Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json', '-OutputDir', "artifacts/light-r12/$Phase/$tier-$light")
        if ($Rq) { $argsQa += @('-Rq', $Rq) }
        if ($LowSunOnly -or $Targeted) { $argsQa += @('-Cameras', $cameras) }
        & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/visual-qa.ps1 @argsQa
        if ($LASTEXITCODE -ne 0) { throw "Capture failed: $tier $light" }
        # Preserve intentionally baked policy assets; restore only known QA side effects.
        git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat
        if ($LASTEXITCODE -ne 0) { throw 'Settings restore failed.' }
    }
}
