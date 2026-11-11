$ErrorActionPreference = 'Stop'
$root = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $root
$mainRoot = 'C:/Users/matma/Documents/Claude/kamion'
$phoneLock = Join-Path $mainRoot 'artifacts/locks/PHONE_RUN'
$ev = 'artifacts/furniture-r1'
function Wait-Phone {
    while (Test-Path $phoneLock) { Write-Host 'PHONE_RUN present; waiting before Unity'; Start-Sleep -Seconds 60 }
    $ours = Get-CimInstance Win32_Process -Filter "name = 'Unity.exe'" |
        Where-Object { $_.CommandLine -like "*$root/game*" -or $_.CommandLine -like "*$root\game*" }
    if ($ours) { throw 'Unity already running in this worktree' }
}
function Save-Status([string]$text) {
    Add-Content "$ev/STATUS.md" "`n$text`nNASTĘPNY KROK: pwsh artifacts/furniture-r1/run-validation.ps1 (resume using completed evidence directories; do not overwrite baseline)"
    git add -f "$ev/STATUS.md"
    git commit -m 'wip(furniture): record validation checkpoint'
}
function Restore-Unity {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
function Import-World([string]$phase) {
    if (Test-Path "$ev/import-$phase.done") { return }
    Wait-Phone
    try {
        & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "$ev/import-$phase.log"
        if ($LASTEXITCODE -ne 0) { throw "Import $phase failed" }
    } finally { Restore-Unity }
    Copy-Item artifacts/world/bialystok-industrial-c-import.json "$ev/import-$phase.json"
    Set-Content "$ev/import-$phase.done" 'OK'
    Save-Status "Import $phase complete."
}
function Render-World([string]$phase) {
    foreach ($tier in @('Low','High')) { foreach ($lighting in @('overcast','clear')) {
        if (Test-Path "$ev/render-$phase-$tier-$lighting.done") { continue }
        Wait-Phone
        $scene = if ($tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
        $dir = "$ev/$phase/$tier-$lighting"
        try {
            & pwsh scripts/visual-qa.ps1 -Scene $scene -Tier $tier -Lighting $lighting -Gate3 Data/Regions/bialystok-industrial-c/furniture_cameras.json -Cameras 'driver-andersa-to-putry,route-putry-entry-signs,dk8-dk19-exit,stretch-05-docks,furniture-footing-slope,furniture-old-steel,furniture-old-concrete,furniture-sign-back,furniture-fence' -OutputDir $dir *> "$ev/render-$phase-$tier-$lighting.log"
            if ($LASTEXITCODE -ne 0) { throw "Render $phase $tier $lighting failed" }
        } finally { Restore-Unity }
        Set-Content "$ev/render-$phase-$tier-$lighting.done" 'OK'
        Save-Status "Render $phase $tier $lighting complete: $dir"
    } }
}
function Audit-World([string]$phase) {
    if (Test-Path "$ev/audit-$phase.done") { return }
    Wait-Phone
    . "$root/scripts/env.ps1"
    $log = "$root/$ev/audit-$phase.log"
    try {
        $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.Gate3Audit.Run',
            '-auditScene','WorldC','-auditOut',"$root/$ev/audit-$phase.json",'-auditCorridorM','40')
        if ($code -ne 0) { throw "Ground audit $phase failed ($code)" }
    } finally { Restore-Unity }
    Set-Content "$ev/audit-$phase.done" 'OK'
    Save-Status "Ground/UV/material audit $phase complete."
}
if (!(Test-Path "$ev/build-before.done")) {
    & uv run --project tools/worldgen python "$ev/source_snapshot.py" baseline
    try {
        & uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$ev/build-before.log"
        if ($LASTEXITCODE -ne 0) { throw 'Baseline generation failed' }
    } finally { & uv run --project tools/worldgen python "$ev/source_snapshot.py" current }
    Copy-Item Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json "$ev/qa-before.json"
    Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json "$ev/manifest-before.json"
    Set-Content "$ev/build-before.done" 'OK'
    Save-Status 'Regenerated baseline from 9e6e9fde; furniture source restored to branch HEAD.'
}
if (!(Test-Path 'Data/raw/derived/bialystok-industrial-c/furniture-r1-before')) {
    & uv run --project tools/worldgen python "$ev/products.py" save before
}
& uv run --project tools/worldgen python "$ev/products.py" load before
Import-World 'before'
Audit-World 'before'
Render-World 'before'
if (Test-Path 'Data/raw/derived/bialystok-industrial-c/furniture-r1-after') {
    & uv run --project tools/worldgen python "$ev/products.py" load after
} else {
    & uv run --project tools/worldgen python -u tools/worldgen/roads/build_world.py --region bialystok-industrial-c *> "$ev/build-after.log"
    if ($LASTEXITCODE -ne 0) { throw 'After generation failed' }
    & uv run --project tools/worldgen python "$ev/products.py" save after
}
Copy-Item Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json "$ev/qa-after.json"
Copy-Item Data/Regions/bialystok-industrial-c/generated/world_manifest.json "$ev/manifest-after.json"
Save-Status 'Regenerated ADR0102 world.'
Import-World 'after'
Audit-World 'after'
Render-World 'after'
if (!(Test-Path "$ev/pytest-after.done")) {
    & uv run --project tools/worldgen python -m pytest tests/gis -q *> "$ev/pytest-after.log"
    if ($LASTEXITCODE -ne 0) { throw 'GIS after failed' }
    Set-Content "$ev/pytest-after.done" 'OK'
}
Save-Status 'GIS after passed (see pytest-after.log).'
Wait-Phone
try {
    & pwsh scripts/test.ps1 -Platform EditMode *> "$ev/editmode.log"
    if ($LASTEXITCODE -ne 0) { throw 'EditMode failed' }
} finally { Restore-Unity }
Save-Status 'EditMode passed. NASTĘPNY KROK: inspect PNG and compare budgets; write ADR/REPORT.'
