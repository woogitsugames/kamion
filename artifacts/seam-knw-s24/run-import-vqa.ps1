param([string[]]$Regions = @('knyszyn-w','knyszyn'), [switch]$NoVqa)
$ErrorActionPreference = 'Continue'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$wt = "$main\.claude\worktrees\seam-knw-s24"
$log = "$wt\artifacts\seam-knw-s24\import.log"
Set-Location $wt
$code = 0
while (Test-Path "$main\artifacts\locks\PHONE_RUN") { "PHONE_RUN, waiting" | Add-Content $log; Start-Sleep 60 }
pwsh "$main\scripts\unity-slot.ps1" -Acquire -Owner seam-knw-s24 *>> $log
try {
  foreach ($r in $Regions) {
    "=== import $r $(Get-Date -Format s)" | Add-Content $log
    pwsh scripts/import-region.ps1 -Region $r -BuildTarget Win64 *>> $log
    if ($LASTEXITCODE -ne 0) { $code = $LASTEXITCODE; "import $r exit $code" | Add-Content $log; break }
  }
  if ($code -eq 0 -and -not $NoVqa) {
    "=== vqa knyszyn $(Get-Date -Format s)" | Add-Content $log
    pwsh scripts/visual-qa.ps1 -Scene World_knyszyn_High -Tier High -BuildTarget Win64 -Lighting clear -OutputDir "$wt\artifacts\seam-knw-s24\vqa-knyszyn" -Cameras 'rings_w_arm_top,rondo_dk65_top,seam_w_top,seam_w_above,rondo_owner_09,dk65_outlet_nw,rondo_dk65_above' *>> $log
    "vqa knyszyn exit $LASTEXITCODE" | Add-Content $log
    "=== vqa knyszyn-w $(Get-Date -Format s)" | Add-Content $log
    pwsh scripts/visual-qa.ps1 -Scene World_knyszyn-w_High -Tier High -BuildTarget Win64 -Lighting clear -OutputDir "$wt\artifacts\seam-knw-s24\vqa-knyszyn-w" *>> $log
    "vqa knyszyn-w exit $LASTEXITCODE" | Add-Content $log
  }
} finally {
  pwsh "$main\scripts\unity-slot.ps1" -Release -Owner seam-knw-s24 *>> $log
  git -C $wt checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
  "DONE code $code $(Get-Date -Format s)" | Add-Content $log
  Set-Content ("$wt\artifacts\seam-knw-s24\import-" + ($Regions -join "_") + ".exit") $code
}
