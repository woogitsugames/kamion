param([string[]]$Tiles = @('knyszyn-w','dw671-tykocin-03','dk65-07','tykocin'))
# Wave 11 visual QA: import tile into this worktree (Library = Android, no platform switch) + render High clear PC tier.
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$env:PYTHONIOENCODING = 'utf-8'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-11-s24'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$v = "$main\artifacts\regen-wave-11-s24\vqa"; New-Item -ItemType Directory -Force $v | Out-Null
$st = "$v\vqa.status"; $L = "$wt\artifacts\regen-wave-11-s24\logs"
$cams = @{
  'knyszyn-w' = 'route_s0142,route_s0426,route_s0710,route_s0994,route_s1278,route_s1562,route_s1846,dk65_koscielna,dk65_goniadzka,tykocka_dw671_out'
  'dw671-tykocin-03' = ''
  'dk65-07' = 'route_s0144,route_s0433,route_s0721,drive_wood,drive_kozince,owner02_seam_n_cab'
  'tykocin' = 'route_s0160,route_s0480,route_s0801,route_s1121,route_s1441,route_s1762,route_s2082,route_s2402,look_tykocin_plaza_cab_0325,sett_eye_kozia'
}
Set-Location $wt
foreach ($t in $Tiles) {
    while (Test-Path "$main\artifacts\locks\PHONE_RUN") { Start-Sleep 60 }
    $log = "$L\vqa-$t.log"
    pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Acquire -Owner regen-wave-11-s24-vqa *>> $log
    $t0 = Get-Date
    pwsh -NoProfile -File scripts/import-region.ps1 -Region $t -BuildTarget Android *>> $log; $e1 = $LASTEXITCODE; $t1 = Get-Date
    $a = @{Scene="World_${t}_High"; Tier='High'; Pc=$true; Width=1920; Height=1080; Lighting='clear'; BuildTarget='Android'; OutputDir="$v\$t\High-clear"}
    if ($cams[$t]) { $a.Cameras = $cams[$t] }
    pwsh -NoProfile -File scripts/visual-qa.ps1 @a *>> $log; $e2 = $LASTEXITCODE
    pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Release -Owner regen-wave-11-s24-vqa *>> $log
    git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings 2>$null
    Add-Content $st ("{0} tile={1} import_exit={2} vqa_exit={3} import_s={4:N0} total_s={5:N0}" -f (Get-Date -Format s), $t, $e1, $e2, ($t1-$t0).TotalSeconds, ((Get-Date)-$t0).TotalSeconds)
}
Add-Content $st "$(Get-Date -Format s) DONE"
