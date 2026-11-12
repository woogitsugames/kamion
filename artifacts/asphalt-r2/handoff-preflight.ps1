# Read-only evidence check. This does not accept known failures or publish artifacts.
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((& git branch --show-current).Trim() -ne 'gpt-asphalt-r2') { throw 'Wrong round' }
$review = Get-Content "$PSScriptRoot/SELF-INSPECTED-CANDIDATE2.json" -Raw | ConvertFrom-Json
if ($review.total -ne 60 -or @($review.files).Count -ne 60) { throw 'Incomplete visual review inventory' }
foreach ($item in $review.files) {
    if ((Get-FileHash -LiteralPath $item.file -Algorithm SHA256).Hash -ne $item.sha256) {
        throw "Reviewed image changed: $($item.file)"
    }
}
$counters = Get-Content "$PSScriptRoot/counter-audit-candidate2.json" -Raw | ConvertFrom-Json
if ($counters.camera_conditions -ne 328 -or $counters.counter_rows -ne 2952 -or $counters.changed_rows -ne 0) { throw 'Counter evidence incomplete or changed' }
$poses = Get-Content "$PSScriptRoot/camera-state-audit-candidate2.json" -Raw | ConvertFrom-Json
if (@($poses.pose_matrix_differences).Count -or @($poses.scope_errors).Count -or ($poses.rows.png | Measure-Object -Sum).Sum -ne 328) { throw 'Pose evidence incomplete or changed' }
$geometry = Get-Content "$PSScriptRoot/geometry-comparison-candidate2.json" -Raw | ConvertFrom-Json
if (-not $geometry.exactly_equal -or $geometry.files -ne 128 -or $geometry.primitives -ne 7315) { throw 'Geometry evidence incomplete or changed' }
$progress = Get-Content "$PSScriptRoot/validation-progress.json" -Raw | ConvertFrom-Json
$pending = @('physics_gate3_exit','fidelity_exit','editmode_exit','finished' | Where-Object { $_ -notin $progress.PSObject.Properties.Name })
[ordered]@{
    checked_at = Get-Date -Format o
    visual_review_hashes_verified = 60
    camera_conditions = 328
    counter_rows = 2952
    geometry_equal = $true
    validation_pending = $pending
    raw_validation = $progress
    note = 'Read-only integrity check, not final acceptance. Read test logs, final XML and fidelity findings before REPORT and end-round-checks.json.'
} | ConvertTo-Json -Depth 5
if ($pending.Count) { exit 2 }
