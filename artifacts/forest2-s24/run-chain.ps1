param([string]$Round, [switch]$Build)
$wt='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest2-s24'; $a="$wt\artifacts\forest2-s24"
foreach ($r in 'dk65-05','dk65-04','dw671-tykocin-03') { pwsh "$a\run-import.ps1" -Region $r -Round $Round -Cams "$a\cams\$r.json" -Build:$Build *>> "$a\chain-$Round.log" }
"CHAIN DONE $Round" >> "$a\chain-$Round.log"
