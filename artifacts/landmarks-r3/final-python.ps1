$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Split-Path (Split-Path $PSScriptRoot))
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:PYTHONUNBUFFERED='1'
$env:KAMION_BLENDER='C:\Users\matma\AppData\Local\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe'
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$owner=(& git branch --show-current).Trim()
if($owner -ne 'gpt-landmarks-r3'){throw 'Unexpected final validation branch'}
& pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 2 -StaleHours 876000
if($LASTEXITCODE -ne 0){throw 'Final Python acquisition failed'}
try {
    $start=(Get-Date).ToUniversalTime().ToString('o')
    & uv run --project tools/worldgen python artifacts/landmarks-r3/verify_cache.py before-tests *> artifacts/landmarks-r3/cache-before-tests.log
    if($LASTEXITCODE -ne 0){throw 'Pre-test runtime cache verification failed'}
    & uv run --project tools/worldgen python -m pytest tests/gis -q *> artifacts/landmarks-r3/final-gis.log
    $gis=$LASTEXITCODE
    & uv run --project tools/worldgen python -m pytest tests/physics tests/gate3 -q *> artifacts/landmarks-r3/final-physics-gate3.log
    $physics=$LASTEXITCODE
    & uv run --project tools/worldgen python artifacts/landmarks-r3/verify_cache.py after-tests *> artifacts/landmarks-r3/cache-after-tests.log
    $cache=$LASTEXITCODE
    @{complete=$true;start_utc=$start;end_utc=(Get-Date).ToUniversalTime().ToString('o');gis_exit=$gis;physics_gate3_exit=$physics;cache_exit=$cache;
      scope='Full GIS once at end of r3, followed by physics/gate3; no parallel Python in this session'} | ConvertTo-Json | Set-Content -Encoding utf8 "$PSScriptRoot/final-python-result.json"
} finally {
    & pwsh $slot -Release -Pool heavy -Owner $owner
}
if($gis -ne 0 -or $physics -ne 0 -or $cache -ne 0){exit 1}
exit 0
