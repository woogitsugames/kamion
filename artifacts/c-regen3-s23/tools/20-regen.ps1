# c-regen3-s23 step 2: ONE regeneration of C + Dojlidy on the integration branch (#123 + #119 + #93). Heavy slot.
# Per region: build_region -> build_world -> [copy aside] -> build_world again -> compare_world (determinism, review #119)
#             -> fidelity -> export-route -> lamp audit.
# Then: region.yaml CRLF revert, region catalogue, thin-shadow audit, budget gate (30-budget.py), tests bound to the data.
. "$PSScriptRoot/_common.ps1"
Init-Status "$Art/regen" 'regen.status'
Remove-Item "$O/regen.done" -ErrorAction SilentlyContinue
Assert-Branch
foreach ($r in $Regions) {
    $b = "$Art/before/data/$r"; New-Item -ItemType Directory -Force $b | Out-Null
    foreach ($f in 'streetscape_qa.json', 'far_field_qa.json', 'world_manifest.json') {
        cmd /c "git show origin/main:Data/Regions/$r/generated/$f > `"$($b -replace '/', '\')\$f`"" ; "snapshot $r/$f exit=$LASTEXITCODE" | Add-Content $St
    }
}
function Gen-Hashes([string]$r, [string]$out) {
    Get-ChildItem "Data/Regions/$r/generated" -Recurse -File | Where-Object { $_.Name -ne 'fidelity_qa.json' } | Sort-Object FullName |
        ForEach-Object { "$((Get-FileHash $_.FullName -Algorithm SHA256).Hash)  $($_.FullName.Substring($Wt.Length + 1))" } | Set-Content $out
}
Slot-Acquire heavy
try {
    foreach ($r in $Regions) {
        Step "build_region-$r" { uv run tools/worldgen/build_region.py --region $r }
        Step "build_world-$r" { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r }
        if ($Last -ne 0) { "STOP: build_world $r failed - see $O/build_world-$r.log" | Add-Content $St; break }
        # determinism (PR #119 / review): second run of the same code on the same data must be byte-identical
        $run1 = "Data/raw/derived/_c-regen3-run1/$r"      # Data/raw is ignored by git; removed at the end of the task
        if (Test-Path $run1) { Remove-Item $run1 -Recurse -Force }
        robocopy "Data/raw/derived/$r/world" $run1 /E /NFL /NDL /NJH /NJS /NP | Out-Null
        "run1 copy $r robocopy=$LASTEXITCODE files=$((Get-ChildItem $run1 -Recurse -File).Count)" | Add-Content $St
        Gen-Hashes $r "$O/generated-run1-$r.sha256"
        Step "build_world2-$r" { uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region $r }
        if ($Last -ne 0) { "STOP: second build_world $r failed" | Add-Content $St; break }
        Step "determinism-$r" { uv run --project tools/worldgen python tools/worldgen/qa/compare_world.py $run1 "Data/raw/derived/$r/world" --detail 5 }
        Gen-Hashes $r "$O/generated-run2-$r.sha256"
        $d = @(Compare-Object (Get-Content "$O/generated-run1-$r.sha256") (Get-Content "$O/generated-run2-$r.sha256"))
        "generated-determinism-$r differing_lines=$($d.Count)" | Add-Content $St
        $d | ForEach-Object { "  $($_.SideIndicator) $($_.InputObject)" } | Select-Object -First 20 | Add-Content $St
        Step "fidelity-$r" { uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region $r }
        Step "export_route-$r" { uv run --project tools/worldgen python scripts/export-route.py --region $r }
        Step "lamp_audit-$r" { uv run --project tools/worldgen python tools/worldgen/qa/lamp_family_audit.py --region $r }
    }
} finally { Slot-Release heavy }
foreach ($r in $Regions) {
    $y = "Data/Regions/$r/region.yaml"
    $ch = @(git diff --unified=0 -- $y | Where-Object { $_ -match '^[+-][^+-]' })
    if ($ch.Count -and -not ($ch | Where-Object { $_ -notmatch 'manifest_sha256' })) { git checkout -q -- $y; "reverted $y (manifest_sha256 only, $($ch.Count) lines)" | Add-Content $St }
    elseif ($ch.Count) { "KEPT $y diff ($($ch.Count) lines, not only manifest_sha256) - read it" | Add-Content $St }
}
Step 'region-catalog-check' { uv run --project tools/worldgen python scripts/export-region-catalog.py --check }
Step 'thin-shadow-audit' { uv run --project tools/worldgen python tools/rendering/thin_shadow_audit.py --check }
Step 'budget' { uv run --project tools/worldgen python "$Art/tools/30-budget.py" }
# tests bound to the rebuilt data: #123 baseline / budget (BASE_M acts only after build_region), #93 ring + piers, #119 forest
Step 'pytest-after-regen' { uv run --project tools/worldgen python -m pytest tests/gis/test_typology_0238.py tests/gis/test_putry_ring_0226.py tests/gis/test_piers_vs_roads_0198.py tests/gis/test_forest_0187.py tests/gis/test_road_fidelity.py -q -p no:cacheprovider -rfEs }
git status --porcelain *> "$O/git-status-after-regen.txt"
$ok = (Step-Ok $St 'budget') -and -not ($Regions | Where-Object { -not (Step-Ok $St "build_world-$_") -or -not (Step-Ok $St "build_world2-$_") })
if ($ok) { Finish 'regen.done' } else { "NOT DONE: a build_world or the budget is not exit=0 - no regen.done written $(Get-Date -Format s)" | Add-Content $St; exit 1 }
