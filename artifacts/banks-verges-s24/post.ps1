param([string]$Round = 'r1')
$a = Split-Path -Parent $MyInvocation.MyCommand.Path
$st = "$a\logs\$Round.status"
while (-not ((Get-Content $st -Raw) -match 'BUILD DONE')) { Start-Sleep 30 }
pwsh -NoProfile -File "$a\run.ps1" -Round $Round -Tiers 'Low,High' -LowStats *> "$a\logs\$Round-post.log"
& 'C:\Program Files\Git\bin\bash.exe' "$a/sbs.sh" $Round *>> "$a\logs\$Round-post.log"
"POST DONE $(Get-Date -f s)" | Add-Content $st
