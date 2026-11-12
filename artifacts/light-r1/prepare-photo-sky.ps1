$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
Set-Location $repo
. "$repo/scripts/env.ps1"
$slot = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Owner gpt-light
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity' }
git diff --quiet HEAD -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
if ($LASTEXITCODE -ne 0) { & pwsh $slot -Release -Owner gpt-light; throw 'Zacommituj zamierzone ustawienia przed Unity' }
$log = Join-Path $PSScriptRoot "prepare-photo-sky-$(Get-Timestamp).log"
try {
    $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Rendering.Editor.PhotographicSkyAssets.PrepareBatch')
    if ($code -ne 0 -or -not (Select-String -Path $log -SimpleMatch -Pattern 'SKY_ASSETS_RESULT: OK' -Quiet)) {
        Show-UnityLogErrors $log
        throw "Import tekstury nieba nieudany: $code, $log"
    }
    Select-String -Path $log -SimpleMatch -Pattern 'SKY_ASSETS_RESULT: OK' | ForEach-Object { $_.Line }
}
finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner gpt-light
}
git add game/Assets/_Project/Rendering/Resources/Sky
if (Test-Path game/Assets/_Project/Rendering/Resources/Sky.meta) { git add game/Assets/_Project/Rendering/Resources/Sky.meta }
Add-Content artifacts/light-r1/STATUS.md 'Import fotograficznej mapy nieba zakończony: linear, mipmapy, ASTC 6x6, oś źródłowego słońca zweryfikowana. Następny krok: cloud-photo.json i oględziny.'
git add -f artifacts/light-r1/STATUS.md
git commit -m 'wip(light): utrwal import fotograficznej mapy nieba'
& pwsh artifacts/light-r1/run-light-batch.ps1 -Jobs artifacts/light-r1/cloud-photo.json
exit $LASTEXITCODE
