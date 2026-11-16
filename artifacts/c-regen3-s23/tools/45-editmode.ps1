# c-regen3-s23: EditMode alone (after the fence shader fix and the merge of origin/main). Unity slot; verdict from the XML.
. "$PSScriptRoot/_common.ps1"
Init-Status "$Art/unity" 'editmode2.status'
Assert-Branch
Slot-Acquire unity
try {
    $t0 = Get-Date
    Step 'editmode2' { pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode }
    $xml = Get-ChildItem artifacts/tests -Filter 'editmode-*.xml' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -ge $t0 } | Sort-Object LastWriteTime | Select-Object -Last 1
    if ($xml) {
        Copy-Item $xml.FullName $O -Force; [xml]$doc = Get-Content $xml.FullName; $run = $doc.'test-run'
        "editmode2 total=$($run.total) passed=$($run.passed) failed=$($run.failed) skipped=$($run.skipped)" | Add-Content $St
        $doc.SelectNodes('//test-case[@result="Failed"]') | ForEach-Object { "  FAILED $($_.fullname)" | Add-Content $St }
    } else { 'editmode2: NO RESULT XML' | Add-Content $St }
} finally { Slot-Release unity }
Restore-UnitySideEffects
"DONE $(Get-Date -Format s)" | Add-Content $St
