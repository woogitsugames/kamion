# tykocin-plaza-s24: import a region and render its QA cameras under one Unity slot (logs next to it)
param([Parameter(Mandatory)][string]$Region, [Parameter(Mandatory)][string]$Out, [string]$Cameras = '', [switch]$SkipImport, [string]$Lighting = 'clear')
$ErrorActionPreference = 'Continue'
$wt = Split-Path (Split-Path $PSScriptRoot)
Set-Location $wt
$owner = 'tykocin-plaza-s24'
New-Item -ItemType Directory -Force "artifacts/tykocin-plaza-s24/logs" | Out-Null
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Owner $owner | Select-Object -Last 1
try {
    if (-not $SkipImport) {
        pwsh scripts/import-region.ps1 -Region $Region -BuildTarget Win64 -MaterialTier High *> "artifacts/tykocin-plaza-s24/logs/import-$Region-$(Split-Path $Out -Leaf).log"
        "import exit $LASTEXITCODE"
    }
    $a = @('-Scene', "World_${Region}_High", '-Tier', 'High', '-Lighting', $Lighting, '-BuildTarget', 'Win64', '-OutputDir', $Out)
    if ($Cameras) { $a += @('-Cameras', $Cameras) }
    pwsh scripts/visual-qa.ps1 @a *> "artifacts/tykocin-plaza-s24/logs/vqa-$Region-$(Split-Path $Out -Leaf)-$Lighting.log"
    "vqa exit $LASTEXITCODE"
} finally {
    pwsh scripts/unity-slot.ps1 -Release -Owner $owner | Select-Object -Last 1
    git -C $wt checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
}
