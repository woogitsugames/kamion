Set-Location 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\tower2-0190'
pwsh -NoProfile -File artifacts/tower2-0190/tools/full.ps1 -Tag base -SkipBuild
pwsh -NoProfile -File artifacts/tower2-0190/tools/full.ps1 -Tag r1 -Sbs
"ALL DONE $(Get-Date -Format s)" | Out-File artifacts/tower2-0190/logs/chain.status -Append -Encoding utf8
