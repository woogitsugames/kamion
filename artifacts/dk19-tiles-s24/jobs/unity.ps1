# dk19-tiles-s24: Unity Win64 import of given tiles (+ optional visual-qa), one slot.
param([string[]]$Tiles, [string]$Vqa = '', [string]$Tag = 'u')
$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\dk19-tiles-s24'
Set-Location $wt
$st = "$wt\artifacts\dk19-tiles-s24\jobs\unity-$Tag.status"; $logd = "$wt\artifacts\logs"
"start $(Get-Date -Format s)" | Set-Content $st
while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep 60 }
pwsh scripts/unity-slot.ps1 -Acquire -MaxSlots 2 -Owner "dk19-s24-$Tag" | Out-Null
foreach ($t in $Tiles) {
  pwsh scripts/import-region.ps1 -Region "bialystok-$t" -BuildTarget Win64 *> "$logd\dk19-s24-import-$t.log"
  "import-$t exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
}
foreach ($t in ($Vqa -split ',' | ? { $_ })) {
  pwsh scripts/visual-qa.ps1 -Scene "World_bialystok-$t" -Tier High -Lighting overcast -BuildTarget Win64 -OutputDir "artifacts/dk19-tiles-s24/vqa/$t" *> "$logd\dk19-s24-vqa-$t.log"
  "vqa-$t exit=$LASTEXITCODE $(Get-Date -Format s)" | Add-Content $st
}
pwsh scripts/unity-slot.ps1 -Release -Owner "dk19-s24-$Tag" | Out-Null
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
"DONE exit=0 $(Get-Date -Format s)" | Add-Content $st
