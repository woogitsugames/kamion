# Wait for wave 3 chains, then rebuild the tiles started before the road-widen merge (redo-0306.txt), then final.ps1.
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-2-s24'; $o = "$wt\artifacts\regen-wave-2-s24"
Set-Location $wt
while ((Select-String 'DONE' "$o\chain.status" -ErrorAction SilentlyContinue).Count -lt 3) { Start-Sleep 60 }
pwsh -NoProfile -File "$o\commit.ps1" *>> "$o\autocommit.log"
Move-Item "$o\chain.status" "$o\chain-wave3.status"; Move-Item "$o\claims" "$o\claims-wave3"
Copy-Item "$o\queue.txt" "$o\queue-wave3.txt"; Copy-Item "$o\redo-0306.txt" "$o\queue.txt"
Add-Content "$o\wave4.status" "$(Get-Date -Format s) wave3 DONE, wave4 start ($((Get-Content "$o\queue.txt").Count) tiles)"
foreach ($c in 'A','B','C') { Start-Process pwsh -ArgumentList '-NoProfile','-File',"$o\chain.ps1",'-Chain',$c -WindowStyle Hidden; Start-Sleep 3 }
Start-Process pwsh -ArgumentList '-NoProfile','-File',"$o\autocommit.ps1" -WindowStyle Hidden
Start-Process pwsh -ArgumentList '-NoProfile','-File',"$o\final.ps1" -WindowStyle Hidden
