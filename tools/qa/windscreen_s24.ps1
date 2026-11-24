param(
    [ValidateSet('lab', 'vqa', 'editmode', 'truck')] [string]$Phase = 'vqa',
    [string]$Tag = 'before',
    [string]$Tiers = 'High,Low',
    [string]$Lightings = 'clear,overcast,lowsun',
    [string]$Cameras = 'cab-driver,cab-dash',
    [string]$Extra = ''
)
<#
windscreen-s24 (ADR 0341): windscreen layer in the cab view (dash reflection, dirt mask, wiper streaks).
Run detached from the worktree root; one exit file per step in artifacts/windscreen-s24/run/<phase>-<Tag>.exit.
  pwsh -NoProfile -File tools/qa/windscreen_s24.ps1 -Phase lab
  pwsh -NoProfile -File tools/qa/windscreen_s24.ps1 -Phase vqa -Tag before
  pwsh -NoProfile -File tools/qa/windscreen_s24.ps1 -Phase editmode
#>
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $root
$run = Join-Path $root 'artifacts\windscreen-s24\run'
New-Item -ItemType Directory -Force $run | Out-Null
$owner = "windscreen-s24-$Phase-$Tag"
$log = Join-Path $run "$Phase-$Tag.log"
$exit = Join-Path $run "$Phase-$Tag.exit"
Remove-Item $exit -ErrorAction SilentlyContinue
$code = 1
try {
    pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Pool unity -Owner $owner *> (Join-Path $run "$Phase-$Tag.slot.log")
    "start $(Get-Date -Format s)" | Set-Content $log
    if ($Phase -eq 'lab') {
        pwsh -NoProfile -File scripts/build-lab.ps1 -SkipAudio -BuildTarget Win64 *>> $log
        $code = $LASTEXITCODE
    }
    elseif ($Phase -eq 'truck') {
        . "$root/scripts/env.ps1"
        $tl = Join-Path $run "truck-$Tag.unity.log"
        $code = Invoke-UnityBatch -LogFile $tl -Arguments @('-executeMethod', 'Game.Editor.Setup.TruckAssetBuilder.BuildBatch') -BuildTarget Win64
        "truck exit $code" | Add-Content $log
        if ($code -eq 0) { pwsh -NoProfile -File scripts/build-lab.ps1 -SkipAudio -BuildTarget Win64 *>> $log; $code = $LASTEXITCODE }
    }
    elseif ($Phase -eq 'editmode') {
        pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode -BuildTarget Win64 *>> $log
        $code = $LASTEXITCODE
    }
    else {
        $code = 0
        foreach ($t in $Tiers -split ',') {
            foreach ($l in $Lightings -split ',') {
                $out = Join-Path $root "artifacts\windscreen-s24\$Tag\$t-$l"
                $a = @('-NoProfile', '-File', 'scripts/visual-qa.ps1', '-Scene', 'DrivingLab', '-Tier', $t, '-Lighting', $l,
                       '-Cameras', $Cameras, '-OutputDir', $out, '-BuildTarget', 'Win64', '-Pc')
                if ($Extra) { $a += ($Extra -split ' ') }
                "== $t $l" | Add-Content $log
                pwsh @a *>> $log
                if ($LASTEXITCODE -ne 0) { $code = $LASTEXITCODE }
            }
        }
    }
    "end $(Get-Date -Format s) code=$code" | Add-Content $log
} finally {
    pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Pool unity -Owner $owner *>> (Join-Path $run "$Phase-$Tag.slot.log")
    git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
    "exit=$code" | Set-Content $exit
}
