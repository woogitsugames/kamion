$wt='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest-height-s24'; $a="$wt\artifacts\forest-height-s24"
while (-not (Select-String -Path "$a\chain-r0-before.log" -Pattern 'CHAIN DONE' -Quiet)) { Start-Sleep 10 }
pwsh "$a\run-import.ps1" -Region dk65-04 -Round r0-before -Cams "$a\cams\dk65-04.json" -SkipImport *>> "$a\chain-r0b.log"
pwsh "$a\run-import.ps1" -Region dk65-05 -Round r0-before -Cams "$a\cams\dk65-05.json" *>> "$a\chain-r0b.log"
"CHAIN DONE r0b" >> "$a\chain-r0b.log"
