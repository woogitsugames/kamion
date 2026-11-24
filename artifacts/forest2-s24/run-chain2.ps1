param([string]$Round = 'r1')
$wt='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest2-s24'; $a="$wt\artifacts\forest2-s24"
while (-not (Select-String -Path "$a\chain-$Round.log" -Pattern 'DONE dk65-05' -Quiet)) { Start-Sleep 15 }
foreach ($r in 'dk65-04','dw671-tykocin-03') { pwsh "$a\run-import.ps1" -Region $r -Round $Round -Cams "$a\cams\$r.json" *>> "$a\chain-$Round.log" }
"CHAIN DONE $Round" >> "$a\chain-$Round.log"
