# env.ps1 - single source of truth for tool paths and shared helpers. Dot-source from other scripts:
#   . "$PSScriptRoot/env.ps1"
$RepoRoot     = (Resolve-Path "$PSScriptRoot/..").Path
$UnityVersion = (Get-Content "$RepoRoot/game/ProjectSettings/ProjectVersion.txt" -ErrorAction SilentlyContinue | Select-String 'm_EditorVersion:' | ForEach-Object { ($_ -split ':\s*')[1].Trim() })
if (-not $UnityVersion) { $UnityVersion = '6000.3.28f1' }
$UnityRoot    = if ($env:UNITY_EDITOR_ROOT) { $env:UNITY_EDITOR_ROOT } else { "C:\Program Files\Unity\Hub\Editor\$UnityVersion" }
$UnityExe     = Join-Path $UnityRoot 'Editor\Unity.exe'
# One documented Android toolchain: the SDK/NDK/JDK shipped with the Unity editor Android module.
$AndroidPlayer = Join-Path $UnityRoot 'Editor\Data\PlaybackEngines\AndroidPlayer'
$AndroidSdk   = Join-Path $AndroidPlayer 'SDK'
$AndroidNdk   = Join-Path $AndroidPlayer 'NDK'
$AndroidJdk   = Join-Path $AndroidPlayer 'OpenJDK'
$Adb          = Join-Path $AndroidSdk 'platform-tools\adb.exe'
# Three different adb.exe builds live on this PC (Unity SDK, scrcpy, WinGet platform-tools). A client whose
# build differs from the running daemon kills and restarts it, which drops the A16 into `offline` mid-run.
# Put the Unity SDK adb first so a bare `adb` in any script that dot-sources this file is the same binary.
$env:PATH = (Split-Path $Adb) + [IO.Path]::PathSeparator + $env:PATH
$env:ADB = $Adb   # scrcpy honours ADB: use the same binary instead of its bundled one
$ProjectPath  = Join-Path $RepoRoot 'game'
$ArtifactsDir = if ($env:KAMION_ARTIFACTS_DIR) { $env:KAMION_ARTIFACTS_DIR } else { Join-Path $RepoRoot 'artifacts' }   # worktrees: point at the main checkout so evidence survives worktree removal
$LogsDir      = Join-Path $ArtifactsDir 'logs'

# App identity (must match Game.Editor.Setup.ProjectSetup).
$PackageName  = 'com.woogitsugames.kamion'

function Get-Timestamp { (Get-Date).ToString('yyyyMMdd-HHmmss') }

function Get-GitShortSha { (& git -C $RepoRoot rev-parse --short=10 HEAD 2>$null) }

# Returns serials of attached, authorised devices (state "device").
function Start-AdbServer {
    # Start the adb daemon in its own hidden console so it never inherits (and holds open) the
    # stdout pipe of whoever runs these scripts - otherwise `pwsh script.ps1 | ...` never ends.
    $p = Start-Process -FilePath $Adb -ArgumentList 'start-server' -WindowStyle Hidden -PassThru
    $null = $p.Handle; [void]$p.WaitForExit(30000)
}

function Get-AdbDevices {
    if (-not (Test-Path $Adb)) { return @() }
    Start-AdbServer
    @(& $Adb devices | Select-String "`tdevice$" | ForEach-Object { ($_.Line -split "`t")[0] })
}

# Resolves the target device list for -Serial / -AllDevices; missing devices are skipped with a warning.
function Resolve-TargetDevices([string[]]$Serial, [switch]$AllDevices) {
    $attached = Get-AdbDevices
    if ($AllDevices) { return $attached }
    if ($Serial) {
        $ok = @()
        foreach ($s in $Serial) {
            if ($attached -contains $s) { $ok += $s } else { Write-Warning "device $s not attached - skipped" }
        }
        return $ok
    }
    if ($attached.Count -eq 1) { return $attached }
    if ($attached.Count -eq 0) { Write-Warning 'no adb device attached'; return @() }
    throw "several devices attached ($($attached -join ', ')): pass -Serial <s> or -AllDevices"
}

# True when the phone shows no keyguard (lock screen). A locked phone pauses the app immediately,
# so measurements are meaningless; scripts never type PINs - the owner must unlock the phone.
function Test-DeviceUnlocked([string]$Serial) {
    & $Adb -s $Serial shell input keyevent KEYCODE_WAKEUP | Out-Null
    $kg = (& $Adb -s $Serial shell dumpsys window) | Select-String 'isKeyguardShowing=(\w+)' | Select-Object -First 1
    return -not ($kg -and $kg.Matches[0].Groups[1].Value -eq 'true')
}

function Test-UnityProjectLocked {
    $lock = Join-Path $ProjectPath 'Temp\UnityLockfile'
    if (-not (Test-Path $lock)) { return $false }
    try { $fs = [IO.File]::Open($lock, 'Open', 'ReadWrite', 'None'); $fs.Close(); return $false } catch { return $true }
}

# Runs Unity in batchmode against game/ and returns the exit code. Only one Unity per project.
function Invoke-UnityBatch {
    param(
        [Parameter(Mandatory)] [string]$LogFile,
        [string[]]$Arguments = @(),
        [switch]$NoGraphics,
        [switch]$NoQuit,
        [string]$BuildTarget = 'Android'
    )
    if (Test-UnityProjectLocked) { throw "game/ is open in another Unity process (Temp/UnityLockfile locked). One Unity per project." }
    New-Item -ItemType Directory -Force (Split-Path $LogFile) | Out-Null
    $argList = @('-batchmode', '-projectPath', $ProjectPath, '-logFile', $LogFile, '-buildTarget', $BuildTarget)
    if (-not $NoQuit) { $argList += '-quit' }
    if ($NoGraphics) { $argList += '-nographics' }
    $argList += $Arguments
    Write-Host "unity: $UnityExe $($argList -join ' ')"
    Repair-UnityLicenseVisibility
    $env:JAVA_HOME = $AndroidJdk
    # Wait for Unity.exe itself only: Unity may start long-lived children (adb server, licensing
    # client) that inherit pipes, so neither piping its output nor Start-Process -Wait (waits for
    # the whole tree) is safe. Progress goes to the -logFile.
    $p = Start-Process -FilePath $UnityExe -ArgumentList $argList -NoNewWindow -PassThru
    $null = $p.Handle  # cache the handle so ExitCode is available after exit
    $p.WaitForExit()
    $code = $p.ExitCode
    if ($code -eq 198) { Write-Warning 'Unity exit 198 = no licence visible to this process. See docs/ENVIRONMENT_AUDIT.md (MSIX AppData virtualisation).' }
    return $code
}

# Unity Hub, Claude desktop and Store PowerShell are MSIX apps: each sees its own virtualised
# %LOCALAPPDATA%, so the Unity entitlement licence written by one (e.g. Unity Hub) is invisible to
# Unity launched from another (exit code 198). If the licence is not visible here, copy the newest
# licence file of this machine from the package stores into the view of this process. Logged.
function Repair-UnityLicenseVisibility {
    $target = Join-Path $env:LOCALAPPDATA 'Unity\licenses\UnityEntitlementLicense.xml'
    if (Test-Path $target) { return }
    $src = Get-ChildItem "$env:LOCALAPPDATA\Packages\*\LocalCache\Local\Unity\licenses\UnityEntitlementLicense.xml" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $src) { Write-Warning 'No Unity licence found. Activate Unity (Hub → Licences) first.'; return }
    New-Item -ItemType Directory -Force (Split-Path $target) | Out-Null
    Copy-Item $src.FullName $target
    Write-Warning "Unity licence was not visible to this process; copied $($src.FullName) → $target"
}

# Prints C# compiler errors and other error lines from a Unity log.
function Show-UnityLogErrors([string]$LogFile, [int]$Max = 40) {
    if (-not (Test-Path $LogFile)) { return }
    Select-String -Path $LogFile -Pattern 'error CS\d+|BUILD_ERROR|Exception:|Error building|FAILED|Scripts have compiler errors' |
        Select-Object -First $Max | ForEach-Object { Write-Host "  $($_.Line)" -ForegroundColor Red }
}
