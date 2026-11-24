# forest-height-s24: import + control cameras of the r2 worlds (dk65-04 once its build line is in the status file)
$a = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest-height-s24\artifacts\forest-height-s24'
$log = "$a\chain-r2-after.log"
foreach ($r in 'dk65-05','dw671-tykocin-03','dk65-04') {
    while ($true) {
        $st = if (Test-Path "$a\build-r2-after.status") { Get-Content "$a\build-r2-after.status" -Raw } else { '' }
        if ($st -match "build_world $r exit (\d+)") { break }
        Start-Sleep 15
    }
    if ($Matches[1] -eq '0') { pwsh "$a\run-import.ps1" -Region $r -Round r2-after -Cams "$a\cams\$r.json" *>> $log }
    else { "SKIP $r (build failed)" | Add-Content $log }
}
"CHAIN DONE r2-after" | Add-Content $log
