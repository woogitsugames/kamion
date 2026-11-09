# doctor.ps1 - verify the development environment for TRUCK SIM PL.
# Usage: pwsh scripts/doctor.ps1   (exit code 0 = all required checks green)
$ErrorActionPreference = 'Continue'
. "$PSScriptRoot/env.ps1"

$fail = 0
function Check([string]$name, [scriptblock]$test, [switch]$Optional) {
    try { $r = & $test } catch { $r = $null }
    if ($r) { Write-Host ("[ OK ] {0,-22} {1}" -f $name, $r) }
    elseif ($Optional) { Write-Host ("[WARN] {0,-22} missing (optional)" -f $name) }
    else { Write-Host ("[FAIL] {0,-22} missing" -f $name); $script:fail++ }
}
# Tools installed after the shell started are not on PATH yet: also look in the usual install dirs.
$extraDirs = @("$env:ProgramFiles\nodejs", "$env:ProgramFiles\dotnet", "$env:ProgramFiles\Blender Foundation\Blender*", "$env:LOCALAPPDATA\Microsoft\WinGet\Links")
function Find-Tool($cmd) {
    $c = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    foreach ($d in $extraDirs) { $f = Get-ChildItem -Path $d -Filter "$cmd.exe" -ErrorAction SilentlyContinue | Select-Object -First 1; if ($f) { return $f.FullName } }
}
function Ver($cmd, $arg = '--version') {
    $exe = Find-Tool $cmd; if (-not $exe) { return }
    $all = @(& $exe $arg 2>&1)
    $code = $LASTEXITCODE
    $out = $all | Where-Object { "$_" -notmatch 'TBBmalloc' -and "$_".Trim() } | Select-Object -First 1
    if ($code -eq 0 -and $out) { "$out".Trim() }
}

Check 'PowerShell 7'      { if ($PSVersionTable.PSVersion.Major -ge 7) { "$($PSVersionTable.PSVersion)" } }
Check 'git'               { Ver git }
Check 'git-lfs'           { Ver git-lfs }
Check 'gh'                { Ver gh }
Check 'uv'                { Ver uv }
Check 'dotnet runtime'    { Ver dotnet '--list-runtimes' }
Check '.NET SDK'          { Ver dotnet '--list-sdks' } -Optional  # needed for tools/physics-runner outside Unity
Check 'blender'           { Ver blender }
Check 'ffmpeg'            { Ver ffmpeg '-version' }
Check 'node'              { Ver node }
Check 'magick'            { Ver magick } -Optional
Check 'scrcpy'            { Ver scrcpy } -Optional
Check 'Unity editor'      { if (Test-Path $UnityExe) { "$UnityVersion ($UnityExe)" } }
Check 'Unity licence'     {
    $f = Join-Path $env:LOCALAPPDATA 'Unity\licenses\UnityEntitlementLicense.xml'
    if (Test-Path $f) { "visible ($f)" }
    elseif (Get-ChildItem "$env:LOCALAPPDATA\Packages\*\LocalCache\Local\Unity\licenses\UnityEntitlementLicense.xml" -ErrorAction SilentlyContinue) { 'in an MSIX package store only - Invoke-UnityBatch copies it on first run' }
}
Check 'Android SDK'       { if (Test-Path $AndroidSdk) { $AndroidSdk } }
Check 'Android API 36'    { if (Test-Path (Join-Path $AndroidSdk 'platforms\android-36')) { 'platforms/android-36' } }
Check 'Android NDK'       { $p = Join-Path $AndroidNdk 'source.properties'; if (Test-Path $p) { (Select-String -Path $p -Pattern 'Pkg.Revision').Line } }
Check 'OpenJDK'           { $j = Join-Path $AndroidJdk 'bin\java.exe'; if (Test-Path $j) { (& $j -version 2>&1 | Select-Object -First 1).ToString() } }
Check 'adb'               { if (Test-Path $Adb) { (& $Adb version | Select-Object -First 1) } }
Check 'ProjectVersion'    { $p = Join-Path $RepoRoot 'game/ProjectSettings/ProjectVersion.txt'; if ((Test-Path $p) -and (Select-String -Path $p -Pattern $UnityVersion -Quiet)) { 'matches' } }
Check 'Boot scene'        { if (Test-Path (Join-Path $ProjectPath 'Assets/_Project/Core/Scenes/Boot.unity')) { 'Assets/_Project/Core/Scenes/Boot.unity' } }
Check 'build entry point' { if (Select-String -Path (Join-Path $ProjectPath 'Assets/_Project/Editor/Build/BuildCommands.cs') -Pattern 'BuildAndroidApk' -Quiet) { 'Game.Editor.Build.BuildCommands.BuildAndroidApk' } }
Check 'Unity not running' { if (-not (Test-UnityProjectLocked)) { 'game/ is free' } } -Optional
Check 'phone (adb)'       {
    if (Test-Path $Adb) {
        $d = Get-AdbDevices
        if ($d) { ($d | ForEach-Object { "$_ $((& $Adb -s $_ shell getprop ro.product.model).Trim())$(if (-not (Test-DeviceUnlocked $_)) { ' [LOCKED]' })" }) -join ', ' }
    }
} -Optional

if ($fail -gt 0) { Write-Host "doctor: $fail required check(s) failed"; exit 1 }
Write-Host 'doctor: all required checks green'; exit 0
