# monuments-s24: import a region and render its QA cameras under one Unity slot (never committed output; logs next to it)
param([Parameter(Mandatory)][string]$Region, [Parameter(Mandatory)][string]$Out, [string]$Cameras = '', [switch]$SkipImport, [string]$Lighting = 'clear')
$ErrorActionPreference = 'Continue'
$wt = Split-Path (Split-Path $PSScriptRoot)
Set-Location $wt
pwsh scripts/unity-slot.ps1 -Acquire -Owner monuments-s24 | Select-Object -Last 1
try {
    if (-not $SkipImport) {
        pwsh scripts/import-region.ps1 -Region $Region -BuildTarget Win64 -MaterialTier High *> "artifacts/monuments-s24/logs/import-$Region.log"
        "import exit $LASTEXITCODE"
    }
    $a = @('-Scene', "World_${Region}_High", '-Tier', 'High', '-Lighting', $Lighting, '-BuildTarget', 'Win64', '-OutputDir', $Out)
    if ($Cameras) { $a += @('-Cameras', $Cameras) }
    pwsh scripts/visual-qa.ps1 @a *> "artifacts/monuments-s24/logs/vqa-$Region-$(Split-Path $Out -Leaf).log"
    "vqa exit $LASTEXITCODE"
} finally {
    pwsh scripts/unity-slot.ps1 -Release -Owner monuments-s24 | Select-Object -Last 1
    git -C $wt checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
}
