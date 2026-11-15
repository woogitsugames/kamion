# ADR 0208: build_world -> export-route -> import-region -> visual-qa for one region; usage: chain.ps1 -R <region> -Tag r1 [-Tiers Low,High] [-Context] [-From build_world|import|vqa]
param([string]$R, [string]$Tag = 'r1', [string[]]$Tiers = @('Low'), [switch]$Context, [string]$From = 'build_world', [string]$Lighting = 'overcast')
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bialystok-t3-0208'
Set-Location $wt
$n = 'bialystok-t3-0208'; $A = "artifacts/$n/$R-$Tag"
New-Item -ItemType Directory -Force $A | Out-Null
$st = "$A/chain.status"
function Step($name, [scriptblock]$b) {
    "$name start $(Get-Date -Format s)" | Add-Content $st
    & $b *>> "$A/$name.log"
    $c = $LASTEXITCODE
    "$name exit=$c $(Get-Date -Format s)" | Add-Content $st
    return ($c -eq 0)
}
$ok = $true
if ($From -eq 'build_world') {
    pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner "$n-$R" | Out-Null
    $bw = @('--region', $R); if ($Context) { $bw += '--context' }
    $ok = (Step 'build_world' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py @bw }) -and
          (Step 'export_route' { uv run --project tools/worldgen python scripts/export-route.py --region $R })
    pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner "$n-$R" | Out-Null
}
# one Unity process per project directory (CLAUDE.md): the two region chains of this worktree share a lock directory
$ul = "$wt/artifacts/bialystok-t3-0208/unity.lock"
if ($ok) {
    while ($true) { try { New-Item -ItemType Directory $ul -ErrorAction Stop | Out-Null; break } catch { Start-Sleep 20 } }
    "unity lock taken $(Get-Date -Format s)" | Add-Content $st
}
try {
if ($ok -and $From -ne 'vqa') {
    while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
    pwsh scripts/unity-slot.ps1 -Acquire -Owner "$n-$R" | Out-Null
    $ok = Step 'import' { pwsh scripts/import-region.ps1 -Region $R }
    pwsh scripts/unity-slot.ps1 -Release -Owner "$n-$R" | Out-Null
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
}
if ($ok) {
    while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
    pwsh scripts/unity-slot.ps1 -Acquire -Owner "$n-$R" | Out-Null
    foreach ($t in $Tiers) {
        Step "vqa_$t" { pwsh scripts/visual-qa.ps1 -Scene "World_$R" -Tier $t -Lighting $Lighting -Width 1920 -Height 1080 -OutputDir "$A/vqa/$t-$Lighting" } | Out-Null
    }
    pwsh scripts/unity-slot.ps1 -Release -Owner "$n-$R" | Out-Null
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null
}
} finally { if (Test-Path $ul) { Remove-Item $ul -Force -ErrorAction SilentlyContinue } }
if ($ok) { "CHAIN DONE $(Get-Date -Format s)" | Add-Content $st } else { "CHAIN FAILED $(Get-Date -Format s)" | Add-Content $st }
