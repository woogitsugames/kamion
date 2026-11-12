param(
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9_-]+$')][string]$CameraId,
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9_-]+$')][string]$Label,
    [ValidateSet('Low','High')][string]$Tier = 'Low',
    [ValidateSet('overcast','clear')][string]$Lighting = 'overcast'
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $repo
$out = "artifacts/asphalt-r2/$Label/$Tier-$Lighting"
$env:KAMION_ARTIFACTS_DIR = Join-Path $repo 'artifacts'
$slotScript = 'C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
& pwsh $slotScript -Acquire -Owner gpt-asphalt -PollSeconds 5
if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
$code = 1
try {
    $env:KAMION_ASPHALT_QA_STATE = '1'
    $env:KAMION_ASPHALT_QA_DIRECTORY = [IO.Path]::GetFullPath($out, $repo)
    & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier $Tier -Lighting $Lighting -Gate3 artifacts/asphalt-r2/cameras.json -Cameras $CameraId -OutputDir $out
    $code = $LASTEXITCODE
} finally {
    $env:KAMION_ASPHALT_QA_STATE = $null
    $env:KAMION_ASPHALT_QA_DIRECTORY = $null
    & pwsh $slotScript -Release -Owner gpt-asphalt
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
Add-Content artifacts/asphalt-r2/STATUS.md "$(Get-Date -Format o): Pojedynczy probe $CameraId w $out exit=$code. Unity slot zwolniony; osobny katalog nie nadpisuje pełnych statystyk baseline."
git add -f artifacts/asphalt-r2/STATUS.md
git commit -q -m "wip(asphalt): checkpoint material probe $Label $Tier $Lighting"
exit $code
