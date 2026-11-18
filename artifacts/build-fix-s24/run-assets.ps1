$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$w='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\build-fix-s24'
Set-Location $w
. ./scripts/env.ps1
$fb="$w\artifacts\build-fix-s24"; $st="$fb\assets.status"
"start $(Get-Date -Format s)" | Set-Content $st
pwsh scripts/unity-slot.ps1 -Acquire -Owner build-fix-s24 | Out-Null
try {
  foreach ($m in 'Game.Editor.Setup.TruckAssetBuilder.BuildBatch','Game.Editor.Setup.TrailerAssetBuilder.BuildBatch') {
    $short = $m.Split('.')[-2]; $t0=Get-Date
    $c = Invoke-UnityBatch -LogFile "$fb\unity-$short.log" -BuildTarget Win64 -NoQuit -Arguments @('-executeMethod', $m)
    "$short exit=$c secs=$([int]((Get-Date)-$t0).TotalSeconds) $(Get-Date -Format s)" | Add-Content $st
    if ($c -ne 0) { break }
  }
} finally { pwsh scripts/unity-slot.ps1 -Release -Owner build-fix-s24 | Out-Null }
"done $(Get-Date -Format s)" | Add-Content $st
