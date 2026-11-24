# forest-height-s24: import + control cameras of the r2 worlds (dk65-04 once its build line is in the status file)
param([string]$Round = "r3-after")
$a = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest-height-s24\artifacts\forest-height-s24'
$log = "$a\chain-$Round.log"
foreach ($r in 'dk65-05','dw671-tykocin-03','dk65-04') {
    while ($true) {
        $st = if (Test-Path "$a\build-$Round.status") { Get-Content "$a\build-$Round.status" -Raw } else { '' }
        if ($st -match "build_world $r exit (\d+)") { break }
        Start-Sleep 15
    }
    if ($Matches[1] -eq '0') { pwsh "$a\run-import.ps1" -Region $r -Round $Round -Cams "$a\cams\$r.json" *>> $log }
    else { "SKIP $r (build failed)" | Add-Content $log }
}
"CHAIN DONE $Round" | Add-Content $log
