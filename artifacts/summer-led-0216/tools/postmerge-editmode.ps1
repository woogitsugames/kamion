# ADR 0216: EditMode after merging origin/main (unity slot, waits for phone runs).
$ErrorActionPreference = 'Continue'
$wt = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)); Set-Location $wt
$o = 'artifacts/summer-led-0216/postmerge'; New-Item -ItemType Directory -Force $o | Out-Null
Remove-Item "$o/editmode.done" -ErrorAction SilentlyContinue
$me = 'summer-led-0216'; $main = 'C:\Users\matma\Documents\Claude\kamion'
while (Test-Path "$main\artifacts\locks\PHONE_RUN") { "waiting PHONE_RUN $(Get-Date -Format s)" | Add-Content "$o/editmode.status"; Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -Pool unity -Owner $me | Out-Null
"editmode start $(Get-Date -Format s)" | Add-Content "$o/editmode.status"
try { pwsh scripts/test.ps1 -Platform EditMode *> "$o/editmode.log"; $c = $LASTEXITCODE } finally { pwsh scripts/unity-slot.ps1 -Release -Pool unity -Owner $me | Out-Null }
"editmode exit=$c $(Get-Date -Format s)" | Add-Content "$o/editmode.status"; "exit=$c" | Set-Content "$o/editmode.done"
