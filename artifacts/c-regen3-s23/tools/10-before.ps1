# c-regen3-s23 step 1: "before" renders = artifacts/c-regen2-s23/after (Reuse).
# Why this is the state of main: generated/ of C and Dojlidy in origin/main differs from the c-regen2 merge (e4fad6868) only
# in fidelity_qa.json; main's own _Generated scenes are from 15.11 16:59 (older than c-regen2), so a fresh "before" would
# need build_world + import of both regions (~55 min, c-regen2 measurement).
# Caveat (goes into the report): main got rendering C# after those renders (ADR 0269 tree shadows on PC Low/Medium,
# LED colour hand-back) - Low pairs differ in tree shadows for a reason that is not this branch.
. "$PSScriptRoot/_common.ps1"
Init-Status "$Art/before" 'before.status'
$srcRoot = "$Main\artifacts\c-regen2-s23\after"
foreach ($r in $Regions) {
    foreach ($cell in 'Low-overcast', 'High-clear', 'g3-Low-clear') {
        if (-not (Test-Path "$srcRoot\$r\$cell")) { "no source cell $r/$cell" | Add-Content $St; continue }
        robocopy "$srcRoot\$r\$cell" "$Art\before\$r\$cell" /E /NFL /NDL /NJH /NJS /NP | Out-Null
        "reuse $r/$cell robocopy=$LASTEXITCODE png=$((Get-ChildItem "$Art\before\$r\$cell" -Filter *.png -ErrorAction SilentlyContinue).Count)" | Add-Content $St
    }
}
"source: $srcRoot (renders of the generated/ state that is in main; before ADR 0269 tree shadows)" | Add-Content $St
Finish 'before.done'
