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
function Ver($cmd, $arg = '--version') { $c = Get-Command $cmd -ErrorAction SilentlyContinue; if ($c) { (& $c.Source $arg 2>&1 | Select-Object -First 1).ToString().Trim() } }

Check 'git'            { Ver git }
Check 'git-lfs'        { Ver git-lfs }
Check 'gh'             { Ver gh }
Check 'uv'             { Ver uv }
Check 'dotnet'         { Ver dotnet }
Check 'blender'        { Ver blender }
Check 'ffmpeg'         { Ver ffmpeg -version }
Check 'node'           { Ver node }
Check 'magick'         { Ver magick } -Optional
Check 'scrcpy'         { Ver scrcpy } -Optional
Check 'Unity editor'   { if (Test-Path $UnityExe) { "$UnityVersion ($UnityExe)" } }
Check 'Android SDK'    { if (Test-Path $AndroidSdk) { $AndroidSdk } }
Check 'adb'            { if (Test-Path $Adb) { (& $Adb version | Select-Object -First 1) } }
Check 'ProjectVersion' { $p = Join-Path $RepoRoot 'game/ProjectSettings/ProjectVersion.txt'; if ((Test-Path $p) -and (Select-String -Path $p -Pattern $UnityVersion -Quiet)) { 'matches' } }
Check 'phone (adb)'    { if (Test-Path $Adb) { $d = & $Adb devices | Select-String "`tdevice$"; if ($d) { ($d | Select-Object -First 1).Line } } } -Optional

if ($fail -gt 0) { Write-Host "doctor: $fail required check(s) failed"; exit 1 }
Write-Host 'doctor: all required checks green'; exit 0
