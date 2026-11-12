$ErrorActionPreference='Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
function Run-LandmarksAnalysis([string]$Script,[string[]]$ScriptArgs) {
    & uv run --project tools/worldgen python "$PSScriptRoot/$Script" @ScriptArgs
    if ($LASTEXITCODE -ne 0) {throw "Analysis failed: $Script"}
}
Run-LandmarksAnalysis 'compare_stats.py' @('before','after-budget')
Run-LandmarksAnalysis 'measure_glass.py' @('after-budget')
Run-LandmarksAnalysis 'make_focus_review.py' @('after-budget')
Run-LandmarksAnalysis 'review_all.py' @('after-budget')
Run-LandmarksAnalysis 'review_all.py' @('after-budget','after')
Run-LandmarksAnalysis 'final_proof.py' @('after-budget','budget-fix-world.log')
exit 0
