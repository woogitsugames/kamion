$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$w='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\build-fix-s24'
Set-Location $w
$fb="$w\artifacts\build-fix-s24"; $st="$fb\build.status"
"start $(Get-Date -Format s)" | Set-Content $st
git diff | Set-Content "$fb\diff-before-build.txt"; git status --short | Set-Content "$fb\status-before-build.txt"
$t0=Get-Date
pwsh scripts/build-windows.ps1 -Slot *> "$fb\build-windows.log"
"build exit=$LASTEXITCODE secs=$([int]((Get-Date)-$t0).TotalSeconds) $(Get-Date -Format s)" | Add-Content $st
git diff | Set-Content "$fb\diff-after-build.txt"; git status --short | Set-Content "$fb\status-after-build.txt"
$same = (Get-FileHash "$fb\diff-before-build.txt").Hash -eq (Get-FileHash "$fb\diff-after-build.txt").Hash
"diff-unchanged=$same" | Add-Content $st
"done $(Get-Date -Format s)" | Add-Content $st
