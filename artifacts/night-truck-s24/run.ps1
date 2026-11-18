# Detached step runner: pwsh run.ps1 -Name <step> -Cmd '<powershell>' ; writes <step>.log and <step>.status (exit=N)
param([string]$Name, [switch]$Unity)
$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$wt = (Resolve-Path "$PSScriptRoot/../..").Path
Set-Location $wt
$st = Join-Path $PSScriptRoot "$Name.status"; $lg = Join-Path $PSScriptRoot "$Name.log"
"running" | Set-Content $st
$code = 1
try {
  if ($Unity) {
    while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
    pwsh scripts/unity-slot.ps1 -Acquire -Owner night-truck-s24 *>> $lg
  }
  $env:KAMION_ARTIFACTS_DIR = Join-Path $wt 'artifacts'
  pwsh -NoProfile -File (Join-Path $PSScriptRoot "$Name.cmd.ps1") *>> $lg
  $code = $LASTEXITCODE
} finally {
  if ($Unity) {
    pwsh scripts/unity-slot.ps1 -Release -Owner night-truck-s24 *>> $lg
    git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings game/Packages 2>> $lg
  }
  "exit=$code" | Set-Content $st
}
