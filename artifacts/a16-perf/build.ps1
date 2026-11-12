# ADR 0136: build Low APK in the a16-perf worktree under the unity FIFO slot. Usage: pwsh artifacts/a16-perf/build.ps1 -Tag diag1
param([string]$Tag = 'diag1', [switch]$Development)
$wt = Split-Path (Split-Path $PSScriptRoot)
$log = Join-Path $PSScriptRoot "build-$Tag.log"
Set-Location $wt
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner claude-a16-perf *>> $log
try {
    $a = @('-NoProfile', '-File', 'scripts/build-android.ps1', '-Tier', 'Low')
    if ($Development) { $a += '-Development' }
    pwsh @a *>> $log
    "EXIT $LASTEXITCODE" | Add-Content $log
}
finally {
    pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner claude-a16-perf *>> $log
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>&1 | Add-Content $log
    if (Test-Path game/Assets/Resources) { git status --short game/Assets/Resources* | Add-Content $log }
    "BUILD DONE $Tag" | Add-Content $log
}
