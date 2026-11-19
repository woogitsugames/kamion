$env:Path=[Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')
$wt='C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\seams-p3-s24'; $main='C:\Users\matma\Documents\Claude\kamion'
Set-Location $wt
$out="$wt\artifacts\seams-p3-s24"; $st="$out\vqa.status"
$cams=@{'bialystok-knyszynska'='seam_e_into_tile,seam_e_back_to_edge,seam_w_to_edge,seam_w_back_into_tile'; 'knyszyn-w'='dk65_seam_east_out,dk65_inbound_to_rondo'}
foreach ($phase in 'after','before') {
  foreach ($t in 'bialystok-knyszynska','knyszyn-w') {
    while (Test-Path "$main\artifacts\locks\PHONE_RUN") { Start-Sleep 60 }
    $d="$wt\Data\raw\derived\$t"
    if ($phase -eq 'before') { Move-Item $d "$d.after"; Move-Item "$out\before-derived\$t" $d }
    $log="$out\logs\vqa-$phase-$t.log"
    pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Acquire -Owner seams-p3-s24 *>> $log
    pwsh -NoProfile -File scripts/import-region.ps1 -Region $t -Tiers High -BuildTarget Win64 *>> $log; $e1=$LASTEXITCODE
    pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene "World_${t}_High" -Tier High -Pc -Width 1920 -Height 1080 -Lighting clear -BuildTarget Win64 -Cameras $cams[$t] -OutputDir "artifacts/seams-p3-s24/vqa/$phase/$t" *>> $log; $e2=$LASTEXITCODE
    pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Release -Owner seams-p3-s24 *>> $log
    if ($phase -eq 'before') { Move-Item $d "$out\before-derived\$t"; Move-Item "$d.after" $d }
    git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset game/ProjectSettings/EditorBuildSettings.asset 2>$null
    Add-Content $st "$(Get-Date -Format s) phase=$phase tile=$t import_exit=$e1 vqa_exit=$e2"
  }
}
Add-Content $st "$(Get-Date -Format s) DONE"
