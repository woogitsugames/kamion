<#
.SYNOPSIS
  Build region packs (AssetBundles, ADR 0234) in Unity batchmode and optionally push them to phones with adb.
.EXAMPLE
  pwsh scripts/build-region-packs.ps1                                   # all imported regions except C, Low tier
  pwsh scripts/build-region-packs.ps1 -Regions dojlidy,dk65-01,knyszyn  # a subset (ids or ids without "bialystok-")
  pwsh scripts/build-region-packs.ps1 -Tiers Both                       # Low + High packs (+ <region>-data bundles)
  pwsh scripts/build-region-packs.ps1 -Push -Serial RFGL34SJYDZ         # build, then adb push the set into incoming/
  pwsh scripts/build-region-packs.ps1 -SkipBuild -SetDir artifacts/regionpacks/0.1.0-abc -Push -Serial RFGL34SJYDZ -Only dk65-06
  pwsh scripts/build-region-packs.ps1 -Target Win64 -Regions dk65-06,dk65-07 -InstallLocal   # PC (D73): copy into the player's incoming/
.NOTES
  ADR 0273: every pack holds the full region scene AND its tile scene (World_<id>[_High]_Tile, ADR 0235) when imported,
  so the streamer can open a region from a pack like one in the player build. -Target Win64 builds Windows bundles
  (folder <ver>-win64); -InstallLocal copies them into %USERPROFILE%/AppData/LocalLow/<company>/<product>/regionpacks/incoming
  (Application.persistentDataPath of the Windows player), the player installs them at the next start.
  Output: artifacts/regionpacks/<bundleVersion>-<sha>[-dirty]/{common.bundle, <region>.bundle, regionpacks.json,
  SHA256SUMS, regionpacks.plan.txt}. Log: artifacts/logs/regionpacks-<ts>.log. Exit 0 = everything requested succeeded.
  Regions must be imported first (scripts/import-region.ps1 -Region <id>); the scenes are gitignored.
  The set only loads in an APK built from the same commit or later (minAppVersionCode = commit count) with the same
  Unity version. Push target: /sdcard/Android/data/<package>/files/regionpacks/incoming/ (bundles first, manifest last);
  the app installs them at the next start (RegionPackService.InstallIncoming). Access to Android/data over adb on the
  A16 (Android 14) is UNVERIFIED.
#>
param(
    [string[]]$Regions = @('all'),
    [ValidateSet('Low', 'High', 'Both')] [string]$Tiers = 'Low',
    [ValidateSet('Android', 'Win64')] [string]$Target = 'Android',
    [switch]$InstallLocal,          # -Target Win64: copy the set into the local Windows player's incoming/ folder
    [string]$Version = '',          # default: <bundleVersion>-<sha>[-dirty], same as the APK name
    [int]$MinAppVersionCode = -1,   # default: git commit count of HEAD
    [int]$MaxAppVersionCode = 0,
    [switch]$SkipBuild,
    [string]$SetDir = '',           # with -SkipBuild: existing set folder
    [switch]$Push,
    [string[]]$Only = @(),          # with -Push: pack ids to push (dependencies are added); default = whole set
    [string[]]$Serial,
    [switch]$AllDevices,
    [string[]]$ExtraUnityArgs = @()
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
$ts = Get-Timestamp
$packRoot = Join-Path $ArtifactsDir 'regionpacks'
New-Item -ItemType Directory -Force $LogsDir, $packRoot | Out-Null

if (-not $SkipBuild) {
    if (-not $Version) {
        $bundleVersion = (Select-String -Path "$ProjectPath/ProjectSettings/ProjectSettings.asset" -Pattern '^\s*bundleVersion:\s*(.+)$').Matches[0].Groups[1].Value.Trim()
        $sha = Get-GitShortSha
        if (& git -C $RepoRoot status --porcelain --untracked-files=no) { $sha = "$sha-dirty" }
        $Version = "$bundleVersion-$sha"
        if ($Target -eq 'Win64') { $Version = "$Version-win64" }
    }
    $SetDir = Join-Path $packRoot $Version
    $log = Join-Path $LogsDir "regionpacks-$ts.log"
    $unityArgs = @('-executeMethod', 'Game.Editor.Build.RegionPackCommands.BuildRegionPacks',
        '-regions', ($Regions -join ','), '-packTiers', $Tiers, '-packOutput', $packRoot, '-packSetVersion', $Version,
        '-maxAppVersionCode', "$MaxAppVersionCode", '-packTarget', $Target)
    if ($MinAppVersionCode -ge 0) { $unityArgs += @('-minAppVersionCode', "$MinAppVersionCode") }
    if ($ExtraUnityArgs) { $unityArgs += $ExtraUnityArgs }
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $code = Invoke-UnityBatch -LogFile $log -Arguments $unityArgs -BuildTarget $Target
    $result = Select-String -Path $log -Pattern 'REGIONPACKS_RESULT:.*' -ErrorAction SilentlyContinue | Select-Object -Last 1
    if ($code -ne 0 -or -not $result -or $result.Line -notmatch 'REGIONPACKS_RESULT: Succeeded') {
        Write-Host "REGION PACKS FAILED (exit $code) after $([int]$sw.Elapsed.TotalSeconds)s, log: $log" -ForegroundColor Red
        if ($result) { Write-Host "  $($result.Line)" -ForegroundColor Red }
        Show-UnityLogErrors $log
        exit ([Math]::Max(1, $code))
    }
    Write-Host $result.Line
    Write-Host "log    $log"
} elseif (-not $SetDir) {
    $SetDir = Get-ChildItem $packRoot -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
    if (-not $SetDir) { throw 'no set in artifacts/regionpacks (run without -SkipBuild)' }
    Write-Warning "no -SetDir: using the NEWEST set $SetDir"
}

# ---------------------------------------------------------------- verify the set (independent of Unity)
$manifestPath = Join-Path $SetDir 'regionpacks.json'
if (-not (Test-Path $manifestPath)) { throw "manifest missing: $manifestPath" }
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
if ($manifest.schema -ne 'truck-sim-pl/region-packs/1') { throw "unknown manifest schema '$($manifest.schema)'" }
$sums = @()
$bad = 0
$total = 0L
Write-Host ("SET    {0}  unity {1}  minAppVersionCode {2}" -f $manifest.packSetVersion, $manifest.unityVersion, $manifest.minAppVersionCode)
foreach ($p in $manifest.packs) {
    $f = Join-Path $SetDir $p.file
    if (-not (Test-Path $f)) { Write-Host "  MISSING $($p.file)" -ForegroundColor Red; $bad++; continue }
    $len = (Get-Item $f).Length
    $hash = (Get-FileHash -Algorithm SHA256 $f).Hash.ToLower()
    $ok = ($len -eq [long]$p.sizeBytes) -and ($hash -eq $p.sha256)
    if (-not $ok) { $bad++ }
    $total += $len
    $sums += "$hash  $($p.file)"
    Write-Host ("  {0,-28} {1,8:N1} MB  {2}  deps=[{3}]{4}" -f $p.id, ($len / 1MB), $hash.Substring(0, 12), ($p.dependencies -join ','), $(if ($ok) { '' } else { '  MISMATCH' })) -ForegroundColor $(if ($ok) { 'Gray' } else { 'Red' })
}
$sums | Set-Content (Join-Path $SetDir 'SHA256SUMS') -Encoding ascii
Write-Host ("TOTAL  {0:N1} MB in {1} bundles -> {2}" -f ($total / 1MB), @($manifest.packs).Count, $SetDir)
if ($bad -gt 0) { Write-Host "$bad bundle(s) missing or not matching the manifest" -ForegroundColor Red; exit 5 }

if ($InstallLocal) {
    if ($manifest.buildTarget -ne 'Win64') { throw "-InstallLocal needs a Win64 set (this one is '$($manifest.buildTarget)')" }
    $settings = "$ProjectPath/ProjectSettings/ProjectSettings.asset"
    $company = (Select-String -Path $settings -Pattern '^\s*companyName:\s*(.+)$').Matches[0].Groups[1].Value.Trim()
    $product = (Select-String -Path $settings -Pattern '^\s*productName:\s*(.+)$').Matches[0].Groups[1].Value.Trim()
    $incoming = Join-Path $env:USERPROFILE "AppData/LocalLow/$company/$product/regionpacks/incoming"
    New-Item -ItemType Directory -Force $incoming | Out-Null
    foreach ($p in $manifest.packs) { Copy-Item (Join-Path $SetDir $p.file) (Join-Path $incoming $p.file) -Force }
    Copy-Item $manifestPath (Join-Path $incoming 'regionpacks.json') -Force   # manifest last
    Write-Host "installed into $incoming - start Kamion.exe; player log line '[PACKS] install ...' confirms"
}

if (-not $Push) { exit 0 }
if ($manifest.buildTarget -and $manifest.buildTarget -ne 'Android') { throw "-Push needs an Android set (this one is '$($manifest.buildTarget)')" }

# ---------------------------------------------------------------- push into the app's incoming/ folder
$ids = @($manifest.packs | ForEach-Object { $_.id })
$sel = if ($Only) { @($Only) } else { $ids }
foreach ($id in @($sel)) {
    $e = $manifest.packs | Where-Object { $_.id -eq $id }
    if (-not $e) { throw "-Only: '$id' is not in the set ($($ids -join ', '))" }
    foreach ($d in @($e.dependencies)) { if ($d -and $sel -notcontains $d) { $sel += $d } }
}
$devices = @(Resolve-TargetDevices -Serial $Serial -AllDevices:$AllDevices)
if ($devices.Count -eq 0) { Write-Warning 'no target device - push skipped'; exit 0 }
$dest = "/sdcard/Android/data/$PackageName/files/regionpacks/incoming"
$failed = 0
foreach ($d in $devices) {
    Write-Host "== $d -> $dest"
    & $Adb -s $d shell mkdir -p $dest | Out-Null
    foreach ($p in ($manifest.packs | Where-Object { $sel -contains $_.id })) {
        $out = & $Adb -s $d push (Join-Path $SetDir $p.file) "$dest/$($p.file)" 2>&1
        $remote = (& $Adb -s $d shell stat -c %s "$dest/$($p.file)" 2>$null | Out-String).Trim()
        if ($LASTEXITCODE -ne 0 -or $remote -ne "$($p.sizeBytes)") {
            Write-Host "  push FAILED $($p.file): $($out -join ' ') (remote size '$remote')" -ForegroundColor Red; $failed++
        } else { Write-Host "  pushed $($p.file) ($remote B)" }
    }
    # Manifest last: the app only starts installing when regionpacks.json is present.
    & $Adb -s $d push $manifestPath "$dest/regionpacks.json" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Host '  manifest push FAILED' -ForegroundColor Red; $failed++ }
    else { Write-Host "  pushed regionpacks.json - restart the app; logcat line '[PACKS] install ...' confirms" }
}
if ($failed -gt 0) { exit 4 }
exit 0
