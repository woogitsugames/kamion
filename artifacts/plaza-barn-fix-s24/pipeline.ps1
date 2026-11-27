# plaza-barn-fix-s24: build_world (PRIVATE derived, regions in parallel) -> import Win64 + visual-qa High (one Unity at a time).
# usage: pwsh artifacts/plaza-barn-fix-s24/pipeline.ps1 -Tag before [-Regions tykocin,dk65-07] [-SkipBuild] [-SkipImport]
param([Parameter(Mandatory)][string]$Tag, [string[]]$Regions = @('tykocin', 'dk65-07'), [switch]$SkipBuild, [switch]$SkipImport,
      [string]$Lighting = 'clear')
$ErrorActionPreference = 'Continue'
$wt = Split-Path (Split-Path $PSScriptRoot)
Set-Location $wt
$env:PATH = "$PSScriptRoot\shim;$env:PATH"          # uv -> allowed interpreter of worktree a492 (Smart App Control)
$logs = "$PSScriptRoot\logs"
$owner = 'plaza-barn-fix-s24'
if ((Get-Item Data\raw\derived).LinkType) { throw "Data/raw/derived is a link - private copy expected" }
if (-not $SkipBuild) {
    $jobs = foreach ($r in $Regions) {
        Start-Job -ArgumentList $wt, $PSScriptRoot, $r, $Tag, $owner -ScriptBlock {
            param($wt, $here, $r, $Tag, $owner)
            Set-Location $wt
            $env:PATH = "$here\shim;$env:PATH"
            pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner "$owner-$r" | Out-Null
            uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r *> "$here/logs/build_world-$r-$Tag.log"
            $bw = $LASTEXITCODE
            pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner "$owner-$r" | Out-Null
            "build_world $r exit $bw"
        }
    }
    $res = $jobs | Wait-Job | Receive-Job
    $res
    if ($res | Where-Object { $_ -notmatch 'exit 0$' }) { exit 1 }
}
$cams = @{ 'tykocin' = ''; 'dk65-07' = '' }
$lock = "$PSScriptRoot\unity.lock"                  # one Unity per project directory: pipelines of this worktree queue here
while (Test-Path $lock) { Start-Sleep 20 }
Set-Content $lock "$PID $Tag $($Regions -join ',')"
pwsh scripts/unity-slot.ps1 -Acquire -Owner $owner | Select-Object -Last 1
try {
    foreach ($r in $Regions) {
        if (-not $SkipImport) {
            pwsh scripts/import-region.ps1 -Region $r -BuildTarget Win64 -MaterialTier High *> "$logs/import-$r-$Tag.log"
            "import $r exit $LASTEXITCODE"
        }
        $a = @('-Scene', "World_${r}_High", '-Tier', 'High', '-Lighting', $Lighting, '-BuildTarget', 'Win64', '-OutputDir', "$PSScriptRoot\vqa-$Tag\$r")
        if ($cams[$r]) { $a += @('-Cameras', $cams[$r]) }
        pwsh scripts/visual-qa.ps1 @a *> "$logs/vqa-$r-$Tag-$Lighting.log"
        "vqa $r exit $LASTEXITCODE"
    }
} finally {
    pwsh scripts/unity-slot.ps1 -Release -Owner $owner | Select-Object -Last 1
    Remove-Item $lock -ErrorAction SilentlyContinue
    git -C $wt checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
}
"PIPELINE DONE $Tag"
