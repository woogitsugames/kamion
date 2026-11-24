$wt='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest-height-s24'; $a="$wt\artifacts\forest-height-s24"
while (-not (Select-String -Path "$a\chain-r0b.log" -Pattern 'CHAIN DONE' -Quiet)) { Start-Sleep 10 }
foreach ($r in 'dk65-04','dw671-tykocin-03') { pwsh "$a\run-import.ps1" -Region $r -Round r0-before -Cams "$a\cams\$r.json" -SkipImport *>> "$a\chain-r0c.log" }
"CHAIN DONE r0c" >> "$a\chain-r0c.log"
