$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
function Run([string]$Script, [string[]]$Arguments) {
    pwsh -NoProfile -ExecutionPolicy Bypass -File "artifacts/truck-r1/$Script" @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Nieudany krok $Script." }
}
Run 'render-phase.ps1' @('-Stage','final-medium','-Tiers','Medium','-Lighting','overcast,clear','-Cameras','truck-front,truck-34,cab-driver')
Run 'render-phase.ps1' @('-Stage','final-dusk','-Lighting','dusk','-Cameras','truck-front,truck-34,cab-driver')
Run 'paint-controls.ps1' @('-Prefix','final-control','-Cases','no-pane')
Run 'all-cameras.ps1' @('-Stage','after-all')
Run 'validate-editmode.ps1' @('-Label','final')
$env:OPENBLAS_NUM_THREADS = '1'
$env:OMP_NUM_THREADS = '1'
foreach ($script in @('final_metrics.py','compare_counters.py','reference_pairs.py')) {
    uv run --project tools/worldgen python "artifacts/truck-r1/$script"
    if ($LASTEXITCODE -ne 0) { throw "Nieudane zestawienie $script." }
}
uv run --project tools/worldgen python artifacts/truck-r1/make_review_pairs.py final-candidate
if ($LASTEXITCODE -ne 0) { throw 'Nie zapisano arkuszy przed/po.' }
