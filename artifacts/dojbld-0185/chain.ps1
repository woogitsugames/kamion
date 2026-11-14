param([string]$Tag = 'r1', [switch]$SkipBuild)
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot\..\..
$n = 'dojbld-0185'; $a = "artifacts/$n"; $st = "$a/chain-$Tag.status"
Remove-Item "$a/chain-$Tag.done" -ErrorAction SilentlyContinue
function Step($name, [scriptblock]$b) {
    "$name start $(Get-Date -Format s)" | Add-Content $st
    & $b *> "$a/$name-$Tag.log"
    "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
    return $LASTEXITCODE -eq 0
}
$ok = $true
if (-not $SkipBuild) {
    pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $n | Out-Null
    $ok = Step 'build_world' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy }
    pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $n | Out-Null
}
if ($ok) {
    pwsh scripts/unity-slot.ps1 -Acquire -Owner $n | Out-Null
    $ok = Step 'import' { pwsh scripts/import-region.ps1 -Region bialystok-dojlidy }
    if ($ok) {
        $ok = Step 'vqa' { pwsh scripts/visual-qa.ps1 -Scene World_bialystok-dojlidy -Tier Low -Lighting overcast -Width 1920 -Height 1080 -Cameras 'photo_P11-001,photo_P11-063,photo_P11-056,photo_P11-094,photo_P11-129b' -OutputDir "$a/$Tag-Low-overcast-photo" }
    }
    pwsh scripts/unity-slot.ps1 -Release -Owner $n | Out-Null
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
}
"ok=$ok $(Get-Date -Format s)" | Set-Content "$a/chain-$Tag.done"
