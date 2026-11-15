$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\bialystok-dk65-t2-0206'
$n = 'bialystok-dk65-t2-0206'
pwsh "artifacts/$n/vqa.ps1" -Tag r2 -Tiers Low *> "artifacts/$n/vqa-r2-low.out"
pwsh "artifacts/$n/vqa.ps1" -Tag r2 -Tiers High *> "artifacts/$n/vqa-r2-high.out"
"VQA2 DONE $(Get-Date -Format s)" | Add-Content "artifacts/$n/vqa-r2.status"
