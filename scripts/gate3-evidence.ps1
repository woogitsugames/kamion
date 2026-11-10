<#
.SYNOPSIS
  Reproducible gate 3 evidence for docs/06 section 5 (STAGE-3 E8): editor renders of every gate3 camera for
  Low/Medium/High x overcast/lowsun, side-by-side sheets, and the automatic checks with PASS/FAIL.
.DESCRIPTION
  Steps (each can be skipped; Unity runs are serialised, one process per project):
    1. audit   Unity batchmode Game.Editor.VisualQA.Gate3Audit.Run -> artifacts/gate3/evidence/audit_raw.json
    2. render  Unity batchmode VisualQaRunner (-qaGate3 adds the 30 gate cameras, plus the 7 reused control cameras)
               per tier x lighting -> artifacts/gate3/evidence/renders/<Tier>-<lighting>/<id>.png  (needs a GPU)
    3. report  scripts/gate3_evidence.py: albedo histograms, verdicts, per-camera sheets
               (editor render | phone screencap | CC0 reference), gate3-evidence.json + gate3-evidence.md
  Phone screencaps are NOT taken here (no adb): put them in -PhoneDir (default artifacts/gate3/final/, any layout; a file
  is matched by camera id in its name, tier words in the path/name are shown in the label). Missing = shown as missing.
  Reference photos: Data/Regions/<region>/gate3_reference_map.json; only CC0 / public domain entries are embedded.
.EXAMPLE
  pwsh scripts/gate3-evidence.ps1                       # everything
  pwsh scripts/gate3-evidence.ps1 -SkipRender           # audit + report from existing renders
  pwsh scripts/gate3-evidence.ps1 -SkipAudit -SkipRender  # re-run only the Python report
  pwsh scripts/gate3-evidence.ps1 -Tiers Low -Lightings overcast -Width 1170 -Height 540
.NOTES
  Exit 0 = every check PASS (renders and sheets produced); 1 = at least one check FAIL; 2 = prerequisite/Unity error.
  Editor numbers are not phone numbers (CLAUDE.md rule 2); the verdicts are tooling output, the owner decides the gate.
#>
param(
    [string]$Region = 'bialystok-industrial-c',
    [string[]]$Tiers = @('Low', 'Medium', 'High'),
    [string[]]$Lightings = @('overcast', 'lowsun'),
    [int]$Width = 2340,
    [int]$Height = 1080,
    [string]$OutDir,
    [string]$PhoneDir,
    [string]$PhotosRoot,
    [string]$Apk,   # the installed APK (git sha of the phone frames comes from its name); default: gate3-result*.json under -PhoneDir
    [float]$CorridorM = 30,
    [switch]$SkipAudit,
    [switch]$SkipRender,
    [switch]$SkipReport
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/env.ps1"
if (-not $OutDir) { $OutDir = Join-Path $ArtifactsDir 'gate3/evidence' }
if (-not $PhoneDir) { $PhoneDir = Join-Path $ArtifactsDir 'gate3/final' }
$OutDir = [IO.Path]::GetFullPath($OutDir, (Get-Location).Path)
New-Item -ItemType Directory -Force $OutDir | Out-Null

$camFile = Join-Path $RepoRoot "Data/Regions/$Region/gate3_cameras.json"
$segFile = Join-Path $RepoRoot "Data/Regions/$Region/gate3_segment.json"
foreach ($f in $camFile, $segFile) { if (-not (Test-Path $f)) { Write-Host "missing $f" -ForegroundColor Red; exit 2 } }
$camSpec = Get-Content $camFile -Raw | ConvertFrom-Json
$segSpec = Get-Content $segFile -Raw | ConvertFrom-Json
$ids = @($camSpec.cameras | ForEach-Object { $_.id }) + @($camSpec.reuse_from_control_cameras)
$camList = ($ids -join ',')
$sRanges = (@($segSpec.segments | ForEach-Object { '{0}-{1}' -f [int]$_.s_start_m, [int][Math]::Ceiling($_.s_end_m) }) -join ',')
$gitSha = Get-GitShortSha
Write-Host "== gate3 evidence: region $Region, $($ids.Count) cameras, tiers $($Tiers -join '/'), lightings $($Lightings -join '/'), segments $sRanges, out $OutDir"

function Invoke-Step([string]$name, [string[]]$unityArgs, [string]$okPattern) {
    $log = Join-Path $LogsDir "gate3-evidence-$name-$(Get-Timestamp).log"
    $code = Invoke-UnityBatch -LogFile $log -Arguments $unityArgs
    $res = Select-String -Path $log -Pattern $okPattern | Select-Object -Last 1
    if ($code -ne 0 -or -not $res) {
        Write-Host "step $name FAILED (exit $code), log: $log" -ForegroundColor Red
        Show-UnityLogErrors $log
        exit 2
    }
    Write-Host "step ${name}: $($res.Line.Trim())  (log: $log)"
}

# ---------------------------------------------------------------- 1. audit (corridor data from the world scene)
if (-not $SkipAudit) {
    Invoke-Step 'audit' @('-executeMethod', 'Game.Editor.VisualQA.Gate3Audit.Run', '-auditScene', 'WorldC',
        '-auditOut', (Join-Path $OutDir 'audit_raw.json'), '-auditS', $sRanges, '-auditCorridorM', $CorridorM) 'GATE3_AUDIT_RESULT: OK'
}

# ---------------------------------------------------------------- 2. renders
if (-not $SkipRender) {
    foreach ($tier in $Tiers) {
        # High uses the High world content scene (what the -WorldHigh APK ships); Low/Medium share WorldC.
        $scene = if ($tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
        foreach ($light in $Lightings) {
            $dir = Join-Path $OutDir "renders/$tier-$light"
            New-Item -ItemType Directory -Force $dir | Out-Null
            Invoke-Step "render-$tier-$light" @('-executeMethod', 'Game.Editor.VisualQA.VisualQaRunner.RenderControlCameras',
                '-qaScene', $scene, '-qaWidth', $Width, '-qaHeight', $Height, '-qaTier', $tier, '-qaOutput', $dir,
                '-qaLighting', $light, '-qaCameras', $camList, '-qaGate3', $camFile) 'VISUALQA_RESULT: OK'
        }
    }
}

# ---------------------------------------------------------------- 3. report
if ($SkipReport) { exit 0 }
$pyArgs = @("$PSScriptRoot/gate3_evidence.py", '--region', $Region, '--repo', $RepoRoot, '--out', $OutDir, '--phone-dir', $PhoneDir,
    '--tiers', ($Tiers -join ','), '--lightings', ($Lightings -join ','), '--git-sha', $gitSha)
if ($PhotosRoot) { $pyArgs += @('--photos-root', $PhotosRoot) }
if ($Apk) { $pyArgs += @('--apk', $Apk) }
& python -c "import PIL, numpy" 2>$null
if ($LASTEXITCODE -eq 0) { & python @pyArgs } else { & uv run --no-project --with pillow --with numpy python @pyArgs }
exit $LASTEXITCODE
