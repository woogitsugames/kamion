$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$w='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\build-fix-s24'
Set-Location $w
. ./scripts/env.ps1
$fb="$w\artifacts\build-fix-s24"; $st="$fb\setup-tests.status"
"start $(Get-Date -Format s)" | Set-Content $st
pwsh scripts/unity-slot.ps1 -Acquire -Owner build-fix-s24 | Out-Null
try {
  $t0=Get-Date
  $c = Invoke-UnityBatch -LogFile "$fb\unity-setup.log" -BuildTarget Win64 -NoQuit -Arguments @('-executeMethod','Game.Editor.Setup.ProjectSetup.ApplyRenderingBatch')
  "setup exit=$c secs=$([int]((Get-Date)-$t0).TotalSeconds) $(Get-Date -Format s)" | Add-Content $st
  git diff -- game/ProjectSettings | Set-Content "$fb\projectsettings.diff"
  git status --short | Set-Content "$fb\status-after-setup.txt"
  $t0=Get-Date
  pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 *> "$fb\editmode.log"
  "editmode exit=$LASTEXITCODE secs=$([int]((Get-Date)-$t0).TotalSeconds) $(Get-Date -Format s)" | Add-Content $st
} finally { pwsh scripts/unity-slot.ps1 -Release -Owner build-fix-s24 | Out-Null }
"done $(Get-Date -Format s)" | Add-Content $st
