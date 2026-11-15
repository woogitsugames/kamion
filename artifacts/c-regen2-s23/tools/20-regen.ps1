# c-regen2-s23 stage 2, step 2: ONE regeneration of C + Dojlidy on the integration branch. Heavy slot.
# Order per region as in c-regen-s22: build_region -> build_world (incl. far_field) -> fidelity -> export-route -> lamp audit.
# Then: region catalogue check, budget report (30-budget.py; exit 1 = a budget or a QA check is red).
. "$PSScriptRoot/_common.ps1"
Init-Status "$Art/regen" 'regen.status'
Remove-Item "$O/regen.done" -ErrorAction SilentlyContinue
# "before" numbers = generated/ as committed (identical to main: no PR of this branch touches generated/)
foreach ($r in $Regions) {
    $b = "$Art/before/data/$r"; New-Item -ItemType Directory -Force $b | Out-Null
    foreach ($f in 'streetscape_qa.json', 'far_field_qa.json', 'world_manifest.json') {
        cmd /c "git show HEAD:Data/Regions/$r/generated/$f > `"$($b -replace '/', '\')\$f`"" ; "snapshot $r/$f exit=$LASTEXITCODE" | Add-Content $St
    }
}
Slot-Acquire heavy
try {
    foreach ($r in $Regions) {
        Step "build_region-$r" { uv run tools/worldgen/build_region.py --region $r }
        Step "build_world-$r" { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r }
        if ($Last -ne 0) { "STOP: build_world $r failed - see $O/build_world-$r.log" | Add-Content $St; break }
        Step "fidelity-$r" { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $r }
        Step "export_route-$r" { uv run --project tools/worldgen python scripts/export-route.py --region $r }
        Step "lamp_audit-$r" { uv run --project tools/worldgen python tools/worldgen/qa/lamp_family_audit.py --region $r }
    }
} finally { Slot-Release heavy }
# c-regen-s22 open item 4: build_region on Windows rewrites manifest_sha256 in region.yaml (CRLF of the checkout). Revert
# the file only when that is the whole diff; anything else stays for a human to read.
foreach ($r in $Regions) {
    $y = "Data/Regions/$r/region.yaml"
    $ch = @(git diff --unified=0 -- $y | Where-Object { $_ -match '^[+-][^+-]' })
    if ($ch.Count -and -not ($ch | Where-Object { $_ -notmatch 'manifest_sha256' })) { git checkout -q -- $y; "reverted $y (manifest_sha256 only, $($ch.Count) lines)" | Add-Content $St }
    elseif ($ch.Count) { "KEPT $y diff ($($ch.Count) lines, not only manifest_sha256) - read it" | Add-Content $St }
}
Step 'region-catalog-check' { uv run --project tools/worldgen python scripts/export-region-catalog.py --check }
Step 'thin-shadow-audit' { uv run --project tools/worldgen python tools/rendering/thin_shadow_audit.py --check }   # #124 changes prototypes
Step 'budget' { uv run --project tools/worldgen python "$Art/tools/30-budget.py" }
git status --porcelain *> "$O/git-status-after-regen.txt"
Finish 'regen.done'
