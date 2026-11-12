param([Parameter(Mandatory)][string]$Phase, [switch]$Focus)
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Split-Path (Split-Path $PSScriptRoot))
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$owner=(& git branch --show-current).Trim()
if($owner -ne 'gpt-landmarks-r4'){throw 'Unexpected analysis branch'}
$reviewParams=@($Phase,'before')
$compareParams=@('before',$Phase)
if($Focus){$reviewParams+='--focus';$compareParams+='--focus'}
& pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 10 -StaleHours 876000
if($LASTEXITCODE -ne 0){throw 'Image analysis acquisition failed'}
try {
    & uv run --project tools/worldgen python artifacts/landmarks-r4/review_all.py @reviewParams *> "$PSScriptRoot/analysis-$Phase-review.log"
    if($LASTEXITCODE -ne 0){throw 'Image comparison failed'}
    & uv run --project tools/worldgen python artifacts/landmarks-r4/compare_stats.py @compareParams *> "$PSScriptRoot/analysis-$Phase-budget.log"
    if($LASTEXITCODE -ne 0){throw 'Budget comparison failed'}
    & uv run --project tools/worldgen python artifacts/landmarks-r4/photo_pair.py $Phase *> "$PSScriptRoot/analysis-$Phase-photo.log"
    if($LASTEXITCODE -ne 0){throw 'Photo evidence composition failed'}
} finally {
    & pwsh $slot -Release -Pool heavy -Owner $owner
}
@{complete=$true;phase=$Phase;diagnostic_subset_only=[bool]$Focus;utc=(Get-Date).ToUniversalTime().ToString('o');
    scope='All image analysis/composition under one heavy slot, released before human review'} |
    ConvertTo-Json | Set-Content "$PSScriptRoot/analysis-$Phase-result.json" -Encoding utf8
exit 0
