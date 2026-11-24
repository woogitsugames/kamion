param([string]$Round = 'r2')
# forest2-s24: import + control cameras of each tile as soon as its world build is done (one Unity at a time)
$wt='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest2-s24'; $a="$wt\artifacts\forest2-s24"
foreach ($r in 'dw671-tykocin-03','dk65-05','dk65-04') {
  while (-not ((Test-Path "$a\build-$Round.status") -and (Select-String -Path "$a\build-$Round.status" -Pattern "build_world $r exit" -Quiet))) { Start-Sleep 15 }
  Copy-Item "$wt\Data\Regions\$r\generated\streetscape_qa.json" "$a\$Round\$r\streetscape_qa.json"
  pwsh "$a\run-import.ps1" -Region $r -Round $Round -Cams "$a\cams\$r.json" *>> "$a\chain-$Round.log"
}
"CHAIN DONE $Round" >> "$a\chain-$Round.log"
