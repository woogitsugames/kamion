param([Parameter(Mandatory)][string]$Region, [Parameter(Mandatory)][string]$Round, [string]$Cams = '', [switch]$Build)
# forest-height-s24: one region at a time (visual-qa picks the scene by name): [build_world] -> import -> High clear + overcast
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest-height-s24'
Set-Location $wt
$out = Join-Path $wt "artifacts\forest-height-s24\$Round\$Region"
New-Item -ItemType Directory -Force $out | Out-Null
$owner = 'forest-height-s24'
if ($Build) {
    pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $owner
    uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $Region *> (Join-Path $out 'build_world.log')
    "build_world exit $LASTEXITCODE"
    pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $owner
}
pwsh scripts/unity-slot.ps1 -Acquire -Owner $owner
try {
    Get-ChildItem game/Assets/_Generated/World -Directory -ErrorAction SilentlyContinue | Where-Object Name -ne $Region | ForEach-Object {
        Remove-Item $_.FullName -Recurse -Force; Remove-Item ($_.FullName + '.meta') -Force -ErrorAction SilentlyContinue }
    pwsh scripts/import-region.ps1 -Region $Region *> (Join-Path $out 'import.log')
    "import exit $LASTEXITCODE"
    if ($LASTEXITCODE -eq 0 -and $Cams) {
        foreach ($l in 'clear', 'overcast') {
            pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier High -Lighting $l -Width 1920 -Height 1080 -Gate3 $Cams -Cameras ((Get-Content $Cams -Raw | ConvertFrom-Json).cameras.id -join ',') -OutputDir (Join-Path $out "High-$l") *> (Join-Path $out "vqa-$l.log")
            "vqa $l exit $LASTEXITCODE"
        }
    }
}
finally {
    git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
    pwsh scripts/unity-slot.ps1 -Release -Owner $owner
}
"DONE $Region $Round"
