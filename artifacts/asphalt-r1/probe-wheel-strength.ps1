param([double]$Strength = 0.8, [string]$Label = 'probe-y080')
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$material = [IO.Path]::GetFullPath('game/Assets/_Generated/World/bialystok-industrial-c/Materials/M_road_asphalt.mat')
$bytes = [IO.File]::ReadAllBytes($material)
$text = [IO.File]::ReadAllText($material)
$before = '_AsphaltWear: {r: 0.9, g: 0.45, b: 1, a: 0.75}'
if (-not $text.Contains($before)) { throw 'Unexpected source material; refusing an ambiguous ablation.' }
$value = $Strength.ToString([Globalization.CultureInfo]::InvariantCulture)
$out = "artifacts/asphalt-r1/$Label/Low-overcast"
& pwsh $slotScript -Acquire -Owner gpt-asphalt -PollSeconds 5
if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
$code = 1
try {
    [IO.File]::WriteAllText($material, $text.Replace($before, "_AsphaltWear: {r: 0.9, g: $value, b: 1, a: 0.75}"))
    $env:KAMION_ASPHALT_QA_STATE = '1'
    $env:KAMION_ASPHALT_QA_DIRECTORY = [IO.Path]::GetFullPath($out)
    & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Gate3 artifacts/asphalt-r1/cameras.json -Cameras d_wear_lane_old -OutputDir $out
    $code = $LASTEXITCODE
} finally {
    [IO.File]::WriteAllBytes($material, $bytes)
    $env:KAMION_ASPHALT_QA_STATE = $null
    $env:KAMION_ASPHALT_QA_DIRECTORY = $null
    & pwsh $slotScript -Release -Owner gpt-asphalt
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content artifacts/asphalt-r1/STATUS.md "$(Get-Date -Format o): Próba siły śladów $value w $out exit=$code. Wygenerowany materiał przywrócony bajt w bajt; źródłowa wartość 0,45 pozostaje bez zmian. Slot Unity zwolniony. To diagnostyka, nie nowy wybrany wariant."
git add -f artifacts/asphalt-r1/STATUS.md
git commit -q -m "wip(asphalt): checkpoint reversible wheel strength probe $Label"
exit $code
