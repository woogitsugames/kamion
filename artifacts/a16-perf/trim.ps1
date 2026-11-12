# ADR 0136: impostor trim in the a16-perf worktree under the unity FIFO slot: bake (Instances.asset in place), EditMode tests,
# Low APK. Usage: pwsh artifacts/a16-perf/trim.ps1 [-Tag trim1] [-SkipBuild] [-SkipTests]
param([string]$Tag = 'trim1', [switch]$SkipBuild, [switch]$SkipTests, [switch]$SkipVqa)
$wt = Split-Path (Split-Path $PSScriptRoot)
$log = Join-Path $PSScriptRoot "trim-$Tag.log"
Set-Location $wt
. (Join-Path $wt 'scripts/env.ps1')
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner claude-a16-perf *>> $log
try {
    function Vqa([string]$out) {
        if ($SkipVqa) { return }
        pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Gate3 Data/Regions/bialystok-industrial-c/gate3_cameras.json -OutputDir (Join-Path $PSScriptRoot "vqa/$out") *>> $log
        "VQA $out EXIT $LASTEXITCODE" | Add-Content $log
    }
    Vqa 'before'
    $ulog = Join-Path $wt "artifacts/logs/imptrim-$Tag.log"
    "$(Get-Date -Format s) bake -> $ulog" | Add-Content $log
    $p = Start-Process $UnityExe -ArgumentList @('-batchmode', '-projectPath', (Join-Path $wt 'game'), '-logFile', $ulog, '-buildTarget', 'Android',
        '-executeMethod', 'Game.World.Import.ImpostorTrimBake.RunBatch') -PassThru -NoNewWindow -Wait
    "BAKE EXIT $($p.ExitCode)" | Add-Content $log
    Select-String -Path $ulog -Pattern '\[IMPTRIM\]|error CS' | ForEach-Object { $_.Line } | Add-Content $log
    if ($p.ExitCode -ne 0) { throw "bake failed $($p.ExitCode)" }
    Vqa 'after'
    if (-not $SkipTests) {
        pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode *>> $log
        "TESTS EXIT $LASTEXITCODE" | Add-Content $log
    }
    if (-not $SkipBuild) {
        pwsh -NoProfile -File scripts/build-android.ps1 -Tier Low *>> $log
        "BUILD EXIT $LASTEXITCODE" | Add-Content $log
    }
}
catch { "ERROR $_" | Add-Content $log }
finally {
    pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner claude-a16-perf *>> $log
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>&1 | Add-Content $log
    if (Test-Path game/Assets/Resources) { git status --short game/Assets/Resources* | Add-Content $log }
    "TRIM DONE $Tag" | Add-Content $log
}
