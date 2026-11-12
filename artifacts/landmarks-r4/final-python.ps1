$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Split-Path (Split-Path $PSScriptRoot))
$env:OPENBLAS_NUM_THREADS='1';$env:OMP_NUM_THREADS='1';$env:MKL_NUM_THREADS='1';$env:PYTHONUNBUFFERED='1'
$env:KAMION_BLENDER='C:\Users\matma\AppData\Local\Programs\Blender4.2\blender-4.2.9-windows-x64\blender.exe'
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
$owner=(& git branch --show-current).Trim()
if($owner -ne 'gpt-landmarks-r4'){throw 'Unexpected final branch'}
function Check-VisualCheckpoint {
    $record=Get-Content "$PSScriptRoot/FINAL-CANDIDATE.json" -Raw | ConvertFrom-Json
    if(-not $record.visual_review_complete -or $record.camera_conditions -ne 244){throw 'Full visual review not recorded'}
    $required=@('tools/blender/world/landmarks/make_fire_station.py','art-source/world/landmarks/fire_station_jrg2/dims.json',
        'art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2.glb','art-source/world/landmarks/fire_station_jrg2/fire_station_jrg2_meta.json',
        'Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json',
        'Data/Regions/bialystok-industrial-c/generated/world_manifest.json','artifacts/landmarks-r4/cameras.json')
    foreach($name in $required){if(-not $record.renderer_input_sha256.PSObject.Properties[$name]){throw "Missing renderer binding: $name"}}
    foreach($entry in $record.renderer_input_sha256.PSObject.Properties){
        if((Get-FileHash -LiteralPath $entry.Name).Hash -ne $entry.Value){throw "Changed renderer input: $($entry.Name)"}
    }
}
Check-VisualCheckpoint
$start=(Get-Date).ToUniversalTime().ToString('o')
& pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 10 -StaleHours 876000
if($LASTEXITCODE -ne 0){throw 'Final GIS acquisition failed'}
try {
    Check-VisualCheckpoint
    & uv run --project tools/worldgen python artifacts/landmarks-r4/verify_cache.py before-tests *> "$PSScriptRoot/cache-before-tests.log"
    if($LASTEXITCODE -ne 0){throw 'Pre-test cache failed'}
    & uv run --project tools/worldgen python -m pytest tests/gis -q *> "$PSScriptRoot/final-gis.log"
    $gis=$LASTEXITCODE
    & uv run --project tools/worldgen python artifacts/landmarks-r4/verify_cache.py after-gis *> "$PSScriptRoot/cache-after-gis.log"
    $cacheGis=$LASTEXITCODE
} finally { & pwsh $slot -Release -Pool heavy -Owner $owner }
@{complete=$false;gis_exit=$gis;cache_after_gis_exit=$cacheGis;start_utc=$start;scope='GIS done; physics/gate3 pending a separate heavy slot'} |
    ConvertTo-Json | Set-Content "$PSScriptRoot/final-python-result.json" -Encoding utf8
if($cacheGis -ne 0){throw 'Runtime cache changed during GIS; inspect before further work'}
& pwsh $slot -Acquire -Pool heavy -Owner $owner -PollSeconds 10 -StaleHours 876000
if($LASTEXITCODE -ne 0){throw 'Final physics acquisition failed'}
try {
    Check-VisualCheckpoint
    & uv run --project tools/worldgen python -m pytest tests/physics tests/gate3 -q *> "$PSScriptRoot/final-physics-gate3.log"
    $physics=$LASTEXITCODE
    & uv run --project tools/worldgen python artifacts/landmarks-r4/verify_cache.py after-tests *> "$PSScriptRoot/cache-after-tests.log"
    $cache=$LASTEXITCODE
} finally { & pwsh $slot -Release -Pool heavy -Owner $owner }
@{complete=$true;gis_exit=$gis;physics_gate3_exit=$physics;cache_after_gis_exit=$cacheGis;cache_exit=$cache;
    all_test_commands_passed=($gis -eq 0 -and $physics -eq 0);start_utc=$start;end_utc=(Get-Date).ToUniversalTime().ToString('o');
    scope='Full GIS once at end of r4; each test suite holds and releases its own heavy slot'} |
    ConvertTo-Json | Set-Content "$PSScriptRoot/final-python-result.json" -Encoding utf8
if($gis -ne 0 -or $physics -ne 0 -or $cache -ne 0){exit 1}
exit 0
