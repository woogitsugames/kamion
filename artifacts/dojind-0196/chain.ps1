# dojind-0196: build_world dojlidy -> import -> render control cameras (Low overcast). Status: chain.status, end: chain.done
param([string]$Tag = 'r1', [switch]$SkipBuild)
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dojind-0196'
Set-Location $wt
$a = "artifacts/dojind-0196"
$st = "$a/chain.status"
Remove-Item "$a/chain.done" -ErrorAction SilentlyContinue
function Step($name, [scriptblock]$b) {
    "$Tag $name start $(Get-Date -Format s)" | Add-Content $st
    & $b *> "$a/$Tag-$name.log"
    $code = $LASTEXITCODE
    "$Tag $name exit=$code $(Get-Date -Format s)" | Add-Content $st
    return $code -eq 0
}
$ok = $true
if (-not $SkipBuild) {
    pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner dojind-0196 | Out-Null
    $ok = Step 'build_world' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy }
    pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner dojind-0196 | Out-Null
}
if ($ok) {
    while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
    pwsh scripts/unity-slot.ps1 -Acquire -Owner dojind-0196 | Out-Null
    $ok = Step 'import' { pwsh scripts/import-region.ps1 -Region bialystok-dojlidy }
    if ($ok) {
        $ok = Step 'vqa' { pwsh scripts/visual-qa.ps1 -Scene World_bialystok-dojlidy -Tier Low -Lighting overcast -Width 1920 -Height 1080 -Cameras 'photo_P11-001,photo_P11-063,photo_P11-056,photo_P11-094,krywlany_runway,route_s0457,route_s0761' -OutputDir "$a/$Tag-Low-overcast" }
    }
    pwsh scripts/unity-slot.ps1 -Release -Owner dojind-0196 | Out-Null
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
}
"$Tag ok=$ok $(Get-Date -Format s)" | Set-Content "$a/chain.done"
