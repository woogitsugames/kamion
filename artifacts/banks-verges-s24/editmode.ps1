$main='C:\Users\matma\Documents\Claude\kamion'; $wt="$main\.claude\worktrees\banks-verges-s24"; Set-Location $wt
pwsh -NoProfile -File $main\scripts\unity-slot.ps1 -Acquire -Owner banks-verges-s24-t | Out-Null
pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode -BuildTarget Win64 *> "$wt\artifacts\banks-verges-s24\logs\editmode-r3.log"
"editmode exit=$LASTEXITCODE $(Get-Date -f s)" | Add-Content "$wt\artifacts\banks-verges-s24\logs\editmode-r3.status"
pwsh -NoProfile -File $main\scripts\unity-slot.ps1 -Release -Owner banks-verges-s24-t | Out-Null
