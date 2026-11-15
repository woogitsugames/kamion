# ADR 0216 regeneration: EditMode (compile + tests) -> build_world x4 (heavy slot) -> import x4 -> vqa matrix "after".
$ErrorActionPreference = 'Continue'
$wt = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)); Set-Location $wt
$o = 'artifacts/summer-led-0216/regen'; New-Item -ItemType Directory -Force $o | Out-Null
$log = "$o/regen.status"; Remove-Item "$o/regen.done" -ErrorAction SilentlyContinue
$me = 'summer-led-0216'; $main = 'C:\Users\matma\Documents\Claude\kamion'
function Step($name, $pool, [scriptblock]$b) {
    if ($pool -eq 'unity') { while (Test-Path "$main\artifacts\locks\PHONE_RUN") { Start-Sleep 60 } }
    pwsh scripts/unity-slot.ps1 -Acquire -Pool $pool -Owner $me | Out-Null
    "$name start $(Get-Date -Format s)" | Add-Content $log
    try { & $b *> "$o/$name.log"; $c = $LASTEXITCODE } finally { pwsh scripts/unity-slot.ps1 -Release -Pool $pool -Owner $me | Out-Null }
    "$name exit=$c $(Get-Date -Format s)" | Add-Content $log
    if ($pool -eq 'unity') { git checkout -q -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>$null }
    return $c -eq 0
}
$ok = Step 'editmode' 'unity' { pwsh scripts/test.ps1 -Platform EditMode }
"editmode ok=$ok (continuing with build_world either way; import needs a compiling project)" | Add-Content $log
$regions = 'knyszyn-s', 'knyszyn-w', 'knyszyn', 'bialystok-knyszynska'
foreach ($r in $regions) {
    $b = Step "build_world-$r" 'heavy' { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r }
    if ($b) { $null = Step "import-$r" 'unity' { pwsh scripts/import-region.ps1 -Region $r } }
}
"REGEN DONE $(Get-Date -Format s)" | Add-Content $log; 'done' | Set-Content "$o/regen.done"
pwsh -NoProfile -File artifacts/summer-led-0216/tools/vqa-matrix.ps1 -Tag after
