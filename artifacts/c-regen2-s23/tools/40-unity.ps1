param([switch]$SkipEditMode, [switch]$SkipVqa)
# c-regen2-s23 stage 2, step 3: EditMode (compile gate for the C# of #109 #110 #111 #122 #125 - never compiled before)
# -> import C + Dojlidy -> visual-qa "after" matrix. One unity slot. Run after 20-regen.ps1 (regen.done + budget exit=0).
# EditMode exit code alone is not a verdict: c-regen-s22 had exit=1 with 2 known CarPaint failures. This script reads the XML:
#   no XML                      -> compile error / crash -> STOP before the import
#   failures outside the known  -> listed in the status, import still runs (the lead decides)
. "$PSScriptRoot/_common.ps1"
Init-Status "$Art/unity" 'unity.status'
Remove-Item "$O/unity.done" -ErrorAction SilentlyContinue
$known = @('CarPaintMaterialTests.DepositionChannel_RequiresScopedYardOptInOrExistingCar')   # HANDOVER: known on main
if (-not (Test-Path "$Art/regen/regen.done")) { "ABORT: $Art/regen/regen.done missing - run 20-regen.ps1 first" | Add-Content $St; exit 2 }
Slot-Acquire unity
$stop = $false
try {
    if (-not $SkipEditMode) {
        $t0 = Get-Date
        Step 'editmode' { pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode }
        $xml = Get-ChildItem artifacts/tests -Filter 'editmode-*.xml' -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -ge $t0 } | Sort-Object LastWriteTime | Select-Object -Last 1
        if (-not $xml) { "editmode: NO RESULT XML (compile error?) - STOP, see $O/editmode.log" | Add-Content $St; $stop = $true }
        else {
            Copy-Item $xml.FullName $O -Force
            [xml]$doc = Get-Content $xml.FullName; $run = $doc.'test-run'
            $failed = @($doc.SelectNodes('//test-case[@result="Failed"]') | ForEach-Object { $_.fullname })
            $new = @($failed | Where-Object { $f = $_; -not ($known | Where-Object { $f -like "*$_*" }) })
            "editmode total=$($run.total) passed=$($run.passed) failed=$($run.failed) skipped=$($run.skipped) known_failed=$($failed.Count - $new.Count) NEW_FAILED=$($new.Count)" | Add-Content $St
            $new | ForEach-Object { "  NEW FAILED $_" | Add-Content $St }
            foreach ($fx in 'FenceMeshCoverageTests', 'ThinShadowCasterTests', 'GpuAbOverridesTests', 'LightPostPolicyTests', 'WorldPbr') {
                $n = @($doc.SelectNodes("//test-case[contains(@fullname,'$fx')]")); $p = @($n | Where-Object { $_.result -eq 'Passed' })
                "  $fx $($p.Count)/$($n.Count) passed" | Add-Content $St
            }
        }
    }
    if (-not $stop) {
        foreach ($r in $Regions) {
            Step "import-$r" { pwsh -NoProfile -File scripts/import-region.ps1 -Region $r }
            if ($Last -ne 0) { "STOP: import $r failed" | Add-Content $St; $stop = $true; break }
            Get-ChildItem artifacts/logs -Filter "import-region-$r-*.log" | Sort-Object LastWriteTime | Select-Object -Last 1 | ForEach-Object {
                Select-String -Path $_.FullName -Pattern '\[IMPORT\] (fence_mesh|material .*shader|lighting profiles)|IMPORT_RESULT|WORLD_MEMORY' | Select-Object -First 12 | ForEach-Object { "  $($_.Line.Trim())" } | Add-Content $St }
        }
    }
    if (-not $stop -and -not $SkipVqa) { & "$PSScriptRoot/vqa.ps1" -Tag after -NoSlot }
} finally { Slot-Release unity }
Restore-UnitySideEffects
"git status after Unity: $((git status --porcelain | Measure-Object).Count) entries -> $O/git-status-after-unity.txt" | Add-Content $St
git status --porcelain *> "$O/git-status-after-unity.txt"
if ($stop) { "STOPPED $(Get-Date -Format s)" | Add-Content $St; exit 1 }
Finish 'unity.done'
