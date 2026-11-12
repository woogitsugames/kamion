param([ValidateSet('after2','after3')][string]$Phase='after2')
$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r3/24h'
$metrics=if($Phase -eq 'after3'){'iteration3'}else{'iteration2'}
$policy=Get-Content "$ev/shelter-policy-$Phase.json" -Raw|ConvertFrom-Json
if(!$policy.variant_inherits_generic -or @($policy.changed_prototypes|Where-Object {$_ -ne 'bus_shelter_red_0120'}).Count){throw 'Normal import policy audit has not passed'}
# Import candidate2 already completed. New paths preserve every short-cull iteration1 input,
# including those read by the older queued comparison. Never share its heavy owner concurrently.
foreach($tier in @('Low','High')){
    foreach($light in @('clear','overcast')){
        & pwsh "$ev/unity-step.ps1" -Step render -Phase $Phase -Tier $tier -Lighting $light
        if($LASTEXITCODE -ne 0){throw "Candidate2 capture failed: $tier $light"}
    }
}
& uv run --project tools/worldgen python "$ev/compare_frames.py" --metrics-only --label $Phase --after-phase $Phase --output-subdir $metrics *> "$ev/compare-$Phase-pre-exact.log"
if($LASTEXITCODE -ne 0){throw 'Candidate2 coverage incomplete'}
foreach($light in @('clear','overcast')){
    & pwsh "$ev/exact-stats.ps1" -Phase $Phase -Tier Low -Lighting $light
    if($LASTEXITCODE -ne 0){throw "Candidate2 exact counters failed: $light"}
}
& pwsh "$ev/side-captures.ps1" -Phase "$Phase-side"
if($LASTEXITCODE -ne 0){throw 'Candidate2 second corners failed'}
& uv run --project tools/worldgen python "$ev/compare_frames.py" --metrics-only --label $Phase --after-phase $Phase --output-subdir $metrics *> "$ev/compare-$Phase-exact.log"
if($LASTEXITCODE -ne 0){throw 'Candidate2 exact comparison failed'}
Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): ukończono 236 kadrów $Phase, 118 dokładnych Low i 8 narożników przy odziedziczonej polityce 60/300 m. Wyniki zapisano osobno w $metrics; nie oznacza to jeszcze spełnienia budżetu ani obejrzenia pełnej serii. NASTĘPNY KROK: odczytać wszystkie delty i przeprowadzić recenzję."
Copy-Item "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md
git add -f "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md "$ev/$metrics" "$ev/compare-$Phase-pre-exact.log" "$ev/compare-$Phase-exact.log"
$proof=@(Get-ChildItem "$ev/exact-$Phase" -Recurse -File | Where-Object {$_.Extension -eq '.json' -or $_.Name -eq 'stats.txt'} | ForEach-Object FullName)
git add -f -- $proof
git commit -m 'wip(furniture): preserve complete measurements with inherited shelter visibility' --quiet
