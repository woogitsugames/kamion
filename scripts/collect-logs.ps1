<#
.SYNOPSIS
  Tester helper (ADR 0271): pack the Kamion player logs, crash reports and basic PC info into one zip on the Desktop.
.DESCRIPTION
  Runs on a tester's PC, not in the repo: it does NOT dot-source scripts/env.ps1 and works in Windows PowerShell 5.1
  (shipped with Windows 10/11) as well as PowerShell 7. scripts/package-windows.py copies it into the player zip
  as collect-logs.ps1 together with Zbierz-logi.cmd (double-click launcher).
  Collected (only what exists):
    %USERPROFILE%\AppData\LocalLow\<Company>\<Product>\Player.log, Player-prev.log, diag\ (summary.json, frametimes.csv)
      (Unity manual 6000.3 "Log files reference": Windows player log location)
    %TMP%\<Company>\<Product>\Crashes\  (newest -MaxCrashes folders; Unity 6000.3 CrashReporting.crashReportFolder)
    %LOCALAPPDATA%\CrashDumps\Kamion*.dmp (newest -MaxDumps files up to -MaxDumpMB each; Windows Error Reporting
      LocalDumps, off by default; larger / older ones are only listed in system.txt)
    system.txt: Windows version, CPU, RAM, GPU name/driver/VRAM, displays, free disk space, game folder + exe SHA256
    dxdiag.txt only with -DxDiag (slow, ~30 s; contains more hardware detail)
  Privacy: the Windows user name and the computer name are replaced by <user> / <pc> in every text file;
  nothing is uploaded anywhere — the tester sends the zip manually. Crash dumps (*.dmp) are binary and are NOT
  anonymized (they can contain the Windows user name in paths); -NoCrashes leaves them out (review #134 P2-2).
  The build identity (build-id.json next to the exe, ADR 0276: git sha + content hash) goes into system.txt.
.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File collect-logs.ps1
  powershell -NoProfile -ExecutionPolicy Bypass -File collect-logs.ps1 -DxDiag -OutDir D:\
.NOTES
  Exit 0 = zip written (even if no log exists yet: then system.txt says so); 1 = could not write the zip.
#>
param(
    [string]$Company = 'woogitsugames',   # ProjectSettings.asset companyName
    [string]$Product = 'Kamion',          # ProjectSettings.asset productName
    [string]$OutDir = '',                 # default: Desktop
    [int]$MaxCrashes = 5,
    [string]$DumpDir = '',                # default: %LOCALAPPDATA%\CrashDumps (Windows Error Reporting LocalDumps)
    [int]$MaxDumps = 2,
    [int]$MaxDumpMB = 1024,               # larger dumps (full dumps) are listed in system.txt, not copied
    [switch]$NoCrashes,                   # review #134 P2-2: crash dumps are not anonymized
    [switch]$DxDiag,
    [switch]$NoAnonymize
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2

$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
if (-not $OutDir) { $OutDir = [Environment]::GetFolderPath('Desktop') }
if (-not (Test-Path $OutDir)) { $OutDir = $env:TEMP }
$stage = Join-Path $env:TEMP "kamion-logs-$ts"
New-Item -ItemType Directory -Force $stage | Out-Null

$logDir = Join-Path $env:USERPROFILE "AppData\LocalLow\$Company\$Product"
$crashDir = Join-Path $env:TEMP "$Company\$Product\Crashes"
$notes = New-Object System.Collections.Generic.List[string]

function Copy-IfExists([string]$src, [string]$dst) {
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force
        $notes.Add("copied  $src")
        return $true
    }
    $notes.Add("missing $src")
    return $false
}

# ---------------------------------------------------------------- logs
$logOut = Join-Path $stage 'logs'
New-Item -ItemType Directory -Force $logOut | Out-Null
foreach ($f in 'Player.log', 'Player-prev.log') { [void](Copy-IfExists (Join-Path $logDir $f) (Join-Path $logOut $f)) }
[void](Copy-IfExists (Join-Path $logDir 'diag') (Join-Path $logOut 'diag'))

# ---------------------------------------------------------------- crash reports (newest first)
if ($NoCrashes) { $notes.Add("skipped $crashDir (-NoCrashes)") }
elseif (Test-Path -LiteralPath $crashDir) {
    $crashOut = Join-Path $stage 'crashes'
    New-Item -ItemType Directory -Force $crashOut | Out-Null
    Get-ChildItem -LiteralPath $crashDir -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First $MaxCrashes |
        ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $crashOut $_.Name) -Recurse -Force; $notes.Add("crash   $($_.Name)") }
} else { $notes.Add("missing $crashDir (no crash so far)") }

# ---------------------------------------------------------------- Windows crash dumps (WER LocalDumps, newest first)
# JAK-GRAC-PC: the D3D12 crash of 16.11 left only %LOCALAPPDATA%\CrashDumps\Kamion.exe.<pid>.dmp. WER writes there only
# when LocalDumps is enabled (Microsoft: off by default). Same privacy rule as above: binary, not anonymized.
if (-not $DumpDir) { $DumpDir = Join-Path $env:LOCALAPPDATA 'CrashDumps' }
if ($NoCrashes) { $notes.Add("skipped $DumpDir (-NoCrashes)") }
elseif (Test-Path -LiteralPath $DumpDir) {
    $dumps = @(Get-ChildItem -LiteralPath $DumpDir -File -Filter 'Kamion*.dmp' | Sort-Object LastWriteTime -Descending)
    if ($dumps.Count -eq 0) { $notes.Add("none    $DumpDir\Kamion*.dmp") }
    $dumpOut = Join-Path $stage 'crashdumps'
    $taken = 0
    foreach ($d in $dumps) {
        $mb = [math]::Round($d.Length / 1MB, 1)
        if ($taken -ge $MaxDumps) { $notes.Add("dump    $($d.Name) $mb MB $($d.LastWriteTime.ToString('s')) not copied (-MaxDumps $MaxDumps)"); continue }
        if ($d.Length -gt ($MaxDumpMB * 1MB)) { $notes.Add("dump    $($d.Name) $mb MB not copied (> -MaxDumpMB $MaxDumpMB; send it separately)"); continue }
        if (-not (Test-Path -LiteralPath $dumpOut)) { New-Item -ItemType Directory -Force $dumpOut | Out-Null }
        Copy-Item -LiteralPath $d.FullName -Destination (Join-Path $dumpOut $d.Name) -Force
        $notes.Add("dump    $($d.Name) $mb MB $($d.LastWriteTime.ToString('s'))")
        $taken++
    }
} else { $notes.Add("missing $DumpDir (Windows crash dumps off or none so far)") }

# ---------------------------------------------------------------- system info
$sys = New-Object System.Collections.Generic.List[string]
$sys.Add("Kamion log bundle $ts")
try {
    $os = Get-CimInstance Win32_OperatingSystem
    $sys.Add("OS       $($os.Caption) $($os.Version) build $($os.BuildNumber) $($os.OSArchitecture)")
    $sys.Add(("RAM      {0:N1} GB total, {1:N1} GB free" -f ($os.TotalVisibleMemorySize / 1MB), ($os.FreePhysicalMemory / 1MB)))
} catch { $sys.Add("OS       unavailable: $($_.Exception.Message)") }
try {
    Get-CimInstance Win32_Processor | ForEach-Object { $sys.Add("CPU      $($_.Name.Trim()) ($($_.NumberOfCores) cores / $($_.NumberOfLogicalProcessors) threads)") }
} catch { $sys.Add("CPU      unavailable") }
try {
    Get-CimInstance Win32_VideoController | ForEach-Object {
        # AdapterRAM is a 32-bit field (caps at 4 GB); the player log [BOOT] line has the real VRAM.
        $sys.Add(("GPU      {0} driver {1} ({2}) AdapterRAM~{3:N1} GB, {4}x{5}" -f $_.Name, $_.DriverVersion, $_.DriverDate,
            ($_.AdapterRAM / 1GB), $_.CurrentHorizontalResolution, $_.CurrentVerticalResolution))
    }
} catch { $sys.Add("GPU      unavailable") }
try {
    Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | ForEach-Object {
        $sys.Add(("DISK     {0} {1:N1} GB free of {2:N1} GB" -f $_.DeviceID, ($_.FreeSpace / 1GB), ($_.Size / 1GB)))
    }
} catch { $sys.Add("DISK     unavailable") }
$exe = Join-Path $PSScriptRoot 'Kamion.exe'
if (Test-Path -LiteralPath $exe) {
    $sys.Add("GAME     $PSScriptRoot")
    $sys.Add("EXE      SHA256 $((Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash.ToLower())")
    $buildId = Join-Path $PSScriptRoot 'build-id.json'
    if (Test-Path -LiteralPath $buildId) {
        try { $bid = Get-Content -LiteralPath $buildId -Raw | ConvertFrom-Json; $sys.Add("BUILD    git $($bid.gitSha) content $($bid.contentHash)") }
        catch { $sys.Add("BUILD    build-id.json unreadable") }
    }
    $readme = Join-Path $PSScriptRoot 'README.txt'
    if (Test-Path -LiteralPath $readme) { $sys.Add("PACKAGE  $((Get-Content -LiteralPath $readme -TotalCount 2)[1])") }
} else { $sys.Add("GAME     collect-logs.ps1 is not next to Kamion.exe ($PSScriptRoot)") }
$sys.Add('')
$sys.AddRange($notes)
$sys | Set-Content -LiteralPath (Join-Path $stage 'system.txt') -Encoding UTF8

if ($DxDiag) {
    $dx = Join-Path $stage 'dxdiag.txt'
    try { Start-Process -FilePath 'dxdiag.exe' -ArgumentList '/t', $dx -Wait -WindowStyle Hidden } catch { "dxdiag failed: $($_.Exception.Message)" | Set-Content $dx }
}

# ---------------------------------------------------------------- anonymize text files
if (-not $NoAnonymize) {
    $pairs = @(@(@($env:USERNAME, '<user>'), @($env:COMPUTERNAME, '<pc>')) | Where-Object { $_[0] -and $_[0].Length -ge 2 })
    Get-ChildItem -LiteralPath $stage -Recurse -File | Where-Object { $_.Extension -in '.log', '.txt', '.json', '.csv', '.xml' } | ForEach-Object {
        $text = [IO.File]::ReadAllText($_.FullName)
        foreach ($p in $pairs) { $text = [regex]::Replace($text, [regex]::Escape($p[0]), $p[1], 'IgnoreCase') }
        [IO.File]::WriteAllText($_.FullName, $text, (New-Object Text.UTF8Encoding($false)))
    }
}

# ---------------------------------------------------------------- zip
$zip = Join-Path $OutDir "kamion-logi-$ts.zip"
try {
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -Force
} catch {
    Write-Host "Nie udało się zapisać $zip : $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally { Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue }
Write-Host "Gotowe: $zip"
if (-not $NoCrashes) { Write-Host 'Uwaga: zrzuty awarii (*.dmp) w paczce mogą zawierać nazwę użytkownika Windows (nie są anonimizowane).' }
Write-Host 'Wyślij ten plik autorowi gry (możesz go najpierw otworzyć i sprawdzić zawartość).'
exit 0
