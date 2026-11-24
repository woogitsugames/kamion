# forest-height-s24: r2 = rebuild of the two tiles generated before the HLOD ribs existed, after the first build chain
$a = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\forest-height-s24\artifacts\forest-height-s24'
while (@(Select-String -Path "$a\build-r1-after.status" -Pattern 'exit' -ErrorAction SilentlyContinue).Count -lt 3) { Start-Sleep 15 }
pwsh "$a\run-build.ps1" -Regions 'dk65-04,dw671-tykocin-03' -Round r2-after
