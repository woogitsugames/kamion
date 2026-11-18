# ADR 0211: build_world -> export-route -> import-region for bialystok-kleeberga (slots: heavy, then unity)
param([string]$From = 'build_world', [string]$Tag = 'r1')
$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\tunnel-0211'
$n = 'tunnel-0211'; $R = 'bialystok-kleeberga'
$st = "artifacts/$n/chain-$Tag.status"
function Step($name, [scriptblock]$b) {
    "$name start $(Get-Date -Format s)" | Add-Content $st
    & $b *>> "artifacts/$n/$name-$Tag.log"
    $c = $LASTEXITCODE
    "$name exit=$c $(Get-Date -Format s)" | Add-Content $st
    if ($c -ne 0) { "STOP at $name" | Add-Content $st; return $false }
    return $true
}
$ok = $true
if ($From -eq 'build_world') {
    pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $n | Out-Null
    $ok = (Step 'build_world' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $R --context }) -and
          (Step 'export_route' { uv run --project tools/worldgen python scripts/export-route.py --region $R })
    pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $n | Out-Null
}
if ($ok) {
    while (Test-Path C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN) { Start-Sleep 60 }
    pwsh scripts/unity-slot.ps1 -Acquire -Owner $n | Out-Null
    $ok = Step 'import' { pwsh scripts/import-region.ps1 -Region $R }
    if ($ok) {
        foreach ($t in 'Low', 'High') {
            "vqa $t start $(Get-Date -Format s)" | Add-Content $st
            pwsh scripts/visual-qa.ps1 -Scene World_bialystok-kleeberga -Tier $t -Lighting overcast -Width 1920 -Height 1080 -OutputDir "artifacts/$n/vqa-$Tag/$t-overcast" *>> "artifacts/$n/vqa-$Tag.log"
            "vqa $t exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
        }
    }
    if ($ok -and $Tag -ne 'r1') {
        "editmode start $(Get-Date -Format s)" | Add-Content $st
        pwsh scripts/test.ps1 -Platform EditMode *>> "artifacts/$n/editmode-$Tag.log"
        "editmode exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
    }
    pwsh scripts/unity-slot.ps1 -Release -Owner $n | Out-Null
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
git checkout -- Data/Regions/bialystok-industrial-c Data/SourceManifests/bialystok-industrial-c-far-field.manifest.json 2>$null
if ($ok) {
    tools/worldgen/.venv/Scripts/python.exe "artifacts/$n/tunnel_sweep.py" *> "artifacts/$n/tunnel_sweep-$Tag.txt"
    tools/worldgen/.venv/Scripts/python.exe "artifacts/$n/route_sweep.py" *> "artifacts/$n/route_sweep-$Tag.txt"
    "sweeps done $(Get-Date -Format s)" | Add-Content $st
}
if ($ok) {
    pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner $n | Out-Null
    "pytest start $(Get-Date -Format s)" | Add-Content $st
    uv run --project tools/worldgen python -m pytest tests/gis -q *> "artifacts/$n/pytest-$Tag.log"
    "pytest exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
    pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner $n | Out-Null
}
if ($ok) { "CHAIN DONE $(Get-Date -Format s)" | Add-Content $st } else { "CHAIN FAILED $(Get-Date -Format s)" | Add-Content $st }

