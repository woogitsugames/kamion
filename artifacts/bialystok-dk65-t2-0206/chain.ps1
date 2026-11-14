# ADR 0206: build_world -> export-route -> import-region for bialystok-kleeberga (slots: heavy, then unity)
param([string]$From = 'build_world')
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bialystok-dk65-t2-0206'
Set-Location $wt
$n = 'bialystok-dk65-t2-0206'; $R = 'bialystok-kleeberga'
$st = "artifacts/$n/chain.status"
function Step($name, [scriptblock]$b) {
    "$name start $(Get-Date -Format s)" | Add-Content $st
    & $b *>> "artifacts/$n/$name.log"
    $c = $LASTEXITCODE
    "$name exit=$c $(Get-Date -Format s)" | Add-Content $st
    if ($c -ne 0) { "STOP at $name" | Add-Content $st; return $false }
    return $true
}
$ok = $true
if ($From -eq 'build_world') {
    pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $n | Out-Null
    $ok = (Step 'build_world' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R }) -and
          (Step 'export_route' { uv run --project tools/worldgen python scripts/export-route.py --region $R })
    pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $n | Out-Null
}
if ($ok) {
    while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
    pwsh scripts/unity-slot.ps1 -Acquire -Owner $n | Out-Null
    $ok = Step 'import' { pwsh scripts/import-region.ps1 -Region $R }
    pwsh scripts/unity-slot.ps1 -Release -Owner $n | Out-Null
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
if ($ok) { "CHAIN DONE $(Get-Date -Format s)" | Add-Content $st } else { "CHAIN FAILED $(Get-Date -Format s)" | Add-Content $st }
