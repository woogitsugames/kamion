# forest-height-s24: import + control cameras of every tile as soon as its r2 world build is done
$a = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest-height-s24\artifacts\forest-height-s24'
foreach ($r in 'dk65-05','dw671-tykocin-03','dk65-04') {
    while (-not (Select-String -Path "$a\build-r2-after.status" -Pattern "build_world $r exit" -ErrorAction SilentlyContinue)) { Start-Sleep 15 }
    if (Select-String -Path "$a\build-r2-after.status" -Pattern "build_world $r exit 0") {
        pwsh "$a\run-import.ps1" -Region $r -Round r2-after -Cams "$a\cams\$r.json" *>> "$a\chain-r2-after.log"
    } else { "SKIP $r (build failed)" >> "$a\chain-r2-after.log" }
}
"CHAIN DONE r2-after" >> "$a\chain-r2-after.log"
