param([Parameter(Mandatory=$true)][int]$CandidatePid)
$ErrorActionPreference='Continue'
$PSNativeCommandUseErrorActionPreference=$false
Set-Location (Resolve-Path "$PSScriptRoot/../../..")
$ev='artifacts/furniture-r3/24h'
$candidate=Get-CimInstance Win32_Process -Filter "ProcessId=$CandidatePid"
if($candidate){
    if($candidate.CommandLine -notmatch 'furniture-r3/24h/candidate.ps1'){
        throw 'Unexpected process: do not overlap another Unity owner'
    }
    Wait-Process -Id $CandidatePid -ErrorAction SilentlyContinue
}
# JSON/statistics only: rejects missing PNGs, mismatched camera sets and stale frozen counters.
# This is not an image batch, generator or test run.
& uv run --project tools/worldgen python "$ev/compare_frames.py" --metrics-only --label after1 *> "$ev/compare-after1-pre-exact.log"
if($LASTEXITCODE -ne 0){throw 'Candidate capture incomplete; inspect before any additional Unity launch'}
& uv run --project tools/worldgen python "$ev/audit_shelter_instances.py" after *> "$ev/instances-after.log"
if($LASTEXITCODE -ne 0){throw 'Unexpected instance changes; inspect the audit'}
Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): dokonano kontroli kompletności czterech wariantów renderu i audytu instancji po generacji. Logi i JSON zawierają wynik; to nie jest jeszcze przegląd wizualny ani pomiar GPU. NASTĘPNY KROK: dokładne liczniki Low i dodatkowe narożniki szkła."
Copy-Item "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md
git add -f "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md "$ev/instances-after.json" "$ev/instances-after.log" "$ev/compare-after1-pre-exact.log" "$ev/frame-budget.json" "$ev/frame-budget.csv" "$ev/frame-coverage.json"
git commit -m 'wip(furniture): audit complete candidate captures and instance identity'
foreach($light in @('clear','overcast')){
    & pwsh "$ev/exact-stats.ps1" -Phase after -Tier Low -Lighting $light
    if($LASTEXITCODE -ne 0){throw "Exact candidate counters failed: $light"}
}
& pwsh "$ev/side-captures.ps1" -Phase after-side
if($LASTEXITCODE -ne 0){throw 'Candidate side diagnostics failed'}
& uv run --project tools/worldgen python "$ev/compare_frames.py" --metrics-only --label after1 *> "$ev/compare-after1-exact.log"
if($LASTEXITCODE -ne 0){throw 'Exact budget comparison failed'}
Add-Content "$ev/STATUS.md" "`n$(Get-Date -Format o): ukończono dokładne liczniki Low, oddzielne rendery narożników after-side i porównanie metryk. To nie dowodzi zgodności wizualnej ani budżetu; wartości trzeba odczytać i obejrzeć kadry. NASTĘPNY KROK: kontrola szkła, analiza wszystkich 236 par oraz niezależna recenzja. Pełny GIS dopiero na końcu rundy."
Copy-Item "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md
git add -f "$ev/STATUS.md" artifacts/furniture-r3/STATUS.md "$ev/post-candidate.ps1" "$ev/exact-after" "$ev/compare-after1-exact.log" "$ev/frame-budget.json" "$ev/frame-budget.csv" "$ev/frame-coverage.json"
git commit -m 'wip(furniture): preserve exact candidate counters before visual review'
