# Commit Data/Regions of tiles finished in chain.status that still have changes; update STATUS.md; push.
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-2-s24'
Set-Location $wt
$st = Get-Content artifacts/regen-wave-2-s24/chain.status | Select-String 'tile=(\S+) build_exit=(\d+) route_exit=(\d+) fidelity_exit=(\d+)'
$done = @(); $bad = @()
foreach ($m in $st) {
    $t = $m.Matches[0].Groups[1].Value
    if ($m.Matches[0].Groups[2].Value -eq '0') { $done += $t } else { $bad += $t }
}
$new = @()
foreach ($t in $done) {
    if (git status --porcelain -- "Data/Regions/$t") { git add -- "Data/Regions/$t"; $new += $t }
    git add -- "game/Assets/_Project/UI/Resources/CabDisplay/Nav/${t}_route.bytes" 2>$null
}
$all = Get-Content artifacts/regen-wave-2-s24/queue.txt
$left = $all | Where-Object { $done -notcontains $_ }
$line = "- $(Get-Date -Format 'yyyy-MM-dd HH:mm'): zrobione ($($done.Count)/$($all.Count)): $($done -join ', '). Błędy build: $($bad -join ', '). Pozostałe: $($left -join ', ')."
Add-Content STATUS.md $line
git add STATUS.md
if ($new.Count -gt 0) { git commit -qm "wip(regen-wave-2-s24): przebudowane $($new -join ', ')`n`nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" } else { git commit -qm "wip(regen-wave-2-s24): STATUS`n`nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" }
git push -q 2>&1 | Select-Object -Last 1
"committed: $($new -join ', ')"
