$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r3/24h'
$policy=Get-Content "$ev/shelter-policy-after2.json" -Raw|ConvertFrom-Json
if(!$policy.variant_inherits_generic -or @($policy.changed_prototypes|Where-Object {$_ -ne 'bus_shelter_red_0120'}).Count){throw 'Normal import policy audit has not passed'}
# Import candidate2 already completed. New paths preserve every short-cull iteration1 input,
# including those read by the older queued comparison. Never share its heavy owner concurrently.
foreach($tier in @('Low','High')){
    foreach($light in @('clear','overcast')){
        & pwsh "$ev/unity-step.ps1" -Step render -Phase after2 -Tier $tier -Lighting $light
        if($LASTEXITCODE -ne 0){throw "Candidate2 capture failed: $tier $light"}
    }
}
& uv run --project tools/worldgen python "$ev/compare_frames.py" --metrics-only --label after2 --after-phase after2 --output-subdir iteration2 *> "$ev/compare-after2-pre-exact.log"
if($LASTEXITCODE -ne 0){throw 'Candidate2 coverage incomplete'}
foreach($light in @('clear','overcast')){
    & pwsh "$ev/exact-stats.ps1" -Phase after2 -Tier Low -Lighting $light
    if($LASTEXITCODE -ne 0){throw "Candidate2 exact counters failed: $light"}
}
& pwsh "$ev/side-captures.ps1" -Phase after2-side
if($LASTEXITCODE -ne 0){throw 'Candidate2 second corners failed'}
& uv run --project tools/worldgen python "$ev/compare_frames.py" --metrics-only --label after2 --after-phase after2 --output-subdir iteration2 *> "$ev/compare-after2-exact.log"
if($LASTEXITCODE -ne 0){throw 'Candidate2 exact comparison failed'}
Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): ukończono 236 kadrów after2, 118 dokładnych Low i 8 after2-side przy odziedziczonej polityce 60/300 m. Wyniki zapisano osobno w iteration2; nie oznacza to jeszcze spełnienia budżetu ani obejrzenia pełnej serii. NASTĘPNY KROK: odczytać wszystkie delty i przeprowadzić recenzję."
Copy-Item "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md
git add -f "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md "$ev/iteration2" "$ev/compare-after2-pre-exact.log" "$ev/compare-after2-exact.log"
$proof=@(Get-ChildItem "$ev/exact-after2" -Recurse -File | Where-Object {$_.Extension -eq '.json' -or $_.Name -eq 'stats.txt'} | ForEach-Object FullName)
git add -f -- $proof
git commit -m 'wip(furniture): preserve complete measurements with inherited shelter visibility' --quiet
