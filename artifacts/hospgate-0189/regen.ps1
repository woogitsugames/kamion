# hospgate-0189: build_world dojlidy -> import -> visual-qa (photo cameras) -> SBS. Usage: pwsh regen.ps1 [-Tag r1] [-SkipBuild]
param([string]$Tag = 'r1', [switch]$SkipBuild, [switch]$SkipImport, [string]$Cameras = 'photo_P11-129c,photo_P11-129b')
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\hospgate-0189'
Set-Location $wt
$a = "artifacts/hospgate-0189"
$st = "$a/regen-$Tag.status"
Remove-Item "$a/regen-$Tag.done" -ErrorAction SilentlyContinue
function Step($name, [scriptblock]$b) {
    "$name start $(Get-Date -Format s)" | Add-Content $st
    & $b *> "$a/$name-$Tag.log"
    "$name exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
    return ($LASTEXITCODE -eq 0)
}
$ok = $true
if (-not $SkipBuild) {
    pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner hospgate-0189 | Out-Null
    $ok = Step 'build_world' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy }
    pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner hospgate-0189 | Out-Null
}
if ($ok) {
    pwsh scripts/unity-slot.ps1 -Acquire -Owner hospgate-0189 | Out-Null
    if (-not $SkipImport) { $ok = Step 'import' { pwsh scripts/import-region.ps1 -Region bialystok-dojlidy } }
    if ($ok) {
        $ok = Step 'render' { pwsh scripts/visual-qa.ps1 -Scene World_bialystok-dojlidy -Tier Low -Lighting overcast -Width 1920 -Height 1080 -Cameras $Cameras -OutputDir "$a/Low-overcast-$Tag" }
    }
    pwsh scripts/unity-slot.ps1 -Release -Owner hospgate-0189 | Out-Null
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
}
"DONE ok=$ok $(Get-Date -Format s)" | Add-Content $st
"done" | Set-Content "$a/regen-$Tag.done"
