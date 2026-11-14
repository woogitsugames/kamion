# dojfix-0202: build_world dojlidy -> cameras -> [A render of the old scene] -> import -> B render. Status: chain.status, end: chain.done
param([string]$Tag = 'r1', [switch]$SkipBuild, [switch]$Baseline, [switch]$High)
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dojfix-0202'
Set-Location $wt
$a = "artifacts/dojfix-0202"
$st = "$a/chain.status"
$cams = 'bollards-photo-13m,bollards-close-4m,photo_P11-063,krywlany_runway,krywlany_runway_paint'
Remove-Item "$a/chain.done" -ErrorAction SilentlyContinue
function Step($name, [scriptblock]$b) {
    "$Tag $name start $(Get-Date -Format s)" | Add-Content $st
    & $b *> "$a/$Tag-$name.log"
    $code = $LASTEXITCODE
    "$Tag $name exit=$code $(Get-Date -Format s)" | Add-Content $st
    return $code -eq 0
}
function Vqa($name, $scene, $tier, $out) {
    Step $name { pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting overcast -Width 1920 -Height 1080 -Gate3 "$a/cameras.json" -Cameras $cams -OutputDir $out }
}
$ok = $true
if (-not $SkipBuild) {
    pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner dojfix-0202 | Out-Null
    $ok = Step 'build_world' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy }
    pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner dojfix-0202 | Out-Null
}
if ($ok) { $ok = Step 'cams' { uv run --project tools/worldgen python "$a/cams.py" } }
if ($ok) {
    while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
    pwsh scripts/unity-slot.ps1 -Acquire -Owner dojfix-0202 | Out-Null
    if ($Baseline) { Vqa 'vqaA' 'World_bialystok-dojlidy' 'Low' "$a/A-Low-overcast" | Out-Null }
    $ok = Step 'import' { pwsh scripts/import-region.ps1 -Region bialystok-dojlidy }
    if ($ok) { $ok = Vqa 'vqa' 'World_bialystok-dojlidy' 'Low' "$a/$Tag-Low-overcast" }
    if ($ok -and $High) { Vqa 'vqaHigh' 'World_bialystok-dojlidy_High' 'High' "$a/$Tag-High-overcast" | Out-Null }
    pwsh scripts/unity-slot.ps1 -Release -Owner dojfix-0202 | Out-Null
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
}
"$Tag ok=$ok $(Get-Date -Format s)" | Set-Content "$a/chain.done"
