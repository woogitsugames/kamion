# ADR 0183 r2: build (with the row) -> import -> renders Low/High -> EditMode -> A/B (build without the row, import,
# Low render for stats) -> restore the row -> build + import again. Status lines in artifacts/logs/pipeline-r2.status.
param([string]$From = 'build')
$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bollards-0183'
Set-Location $wt
$st = 'artifacts/logs/pipeline-r2.status'
$ov = 'Data/Regions/bialystok-dojlidy/overrides.yaml'
function S([string]$m) { "$(Get-Date -Format HH:mm:ss) $m" | Tee-Object -FilePath $st -Append | Out-Null }
function Build([string]$tag) {
    pwsh scripts/unity-slot.ps1 -Acquire -Pool heavy -Owner bollards-0183 *>> artifacts/logs/slot-heavy.log
    try { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region bialystok-dojlidy *> "artifacts/logs/bw-$tag.log"; $c = $LASTEXITCODE }
    finally { pwsh scripts/unity-slot.ps1 -Release -Pool heavy -Owner bollards-0183 *>> artifacts/logs/slot-heavy.log }
    S "build $tag exit=$c"
}
$steps = 'build', 'render', 'editmode', 'ab', 'restore'
$go = $false
foreach ($s in $steps) {
    if ($s -eq $From) { $go = $true }
    if (-not $go) { continue }
    switch ($s) {
        'build'    { S 'build r2 start'; Build 'r2' }
        'render'   { S 'unity r2 start'; pwsh artifacts/bollards-0183/tools/run_unity.ps1 -Steps import,low,high -Tag r2; S 'unity r2 done' }
        'editmode' { S 'editmode start'; pwsh artifacts/bollards-0183/tools/run_unity.ps1 -Steps editmode -Tag r2-editmode; S 'editmode done' }
        'ab'       {
            S 'A/B without the row start'
            Move-Item $ov "$ov.ab-off" -Force
            try { Build 'ab-off' } finally { Move-Item "$ov.ab-off" $ov -Force }
            pwsh artifacts/bollards-0183/tools/run_unity.ps1 -Steps import,low,high -Tag ab-off -Cams 'bollards-close-5m,bollards-cab-20m,bollards-along-8m,photo_P11-063'
            S 'A/B without the row done'
        }
        'restore'  { S 'restore start'; Build 'r2-restore'; pwsh artifacts/bollards-0183/tools/run_unity.ps1 -Steps import -Tag r2-restore; S 'restore done' }
    }
}
S 'PIPELINE DONE'
