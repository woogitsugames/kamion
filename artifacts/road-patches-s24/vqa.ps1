param([ValidateSet('before','after')] [string]$Phase = 'before',
      [string[]]$Tiles = @('knyszyn-w','dw671-tykocin-03'),
      [string[]]$Lights = @('clear','overcast'),
      [switch]$SkipImport)
# road-patches-s24: import tile into this worktree (Library = Android) + render High PC tier clear/overcast.
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$env:PYTHONIOENCODING = 'utf-8'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\agent-a4b13d4540b9ae795'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$v = "$wt\artifacts\road-patches-s24\$Phase"; New-Item -ItemType Directory -Force $v | Out-Null
$st = "$wt\artifacts\road-patches-s24\vqa.status"; $L = "$wt\artifacts\road-patches-s24\logs"
$cams = @{
  'knyszyn-w' = 'dk65_goniadzka,dk65_koscielna,route_s0142,route_s0426,route_s0710,tykocka_dw671_out'
  'dw671-tykocin-03' = 'cab_view_b_fov70,cab_view_0_fov55,chase,route_s0157,route_s0470,route_s0783'
}
Set-Location $wt
foreach ($t in $Tiles) {
    while (Test-Path "$main\artifacts\locks\PHONE_RUN") { Start-Sleep 60 }
    $log = "$L\vqa-$Phase-$t.log"
    pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Acquire -Owner road-patches-s24 *>> $log
    $t0 = Get-Date
    $e1 = 0
    if (-not $SkipImport) { pwsh -NoProfile -File scripts/import-region.ps1 -Region $t -BuildTarget Android *>> $log; $e1 = $LASTEXITCODE }
    $t1 = Get-Date
    foreach ($li in $Lights) {
        $a = @{Scene="World_${t}_High"; Tier='High'; Pc=$true; Width=1920; Height=1080; Lighting=$li; BuildTarget='Android'; OutputDir="$v\$t\High-$li"; Cameras=$cams[$t]}
        pwsh -NoProfile -File scripts/visual-qa.ps1 @a *>> $log; $e2 = $LASTEXITCODE
        Add-Content $st ("{0} phase={1} tile={2} light={3} import_exit={4} vqa_exit={5} import_s={6:N0} total_s={7:N0}" -f (Get-Date -Format s), $Phase, $t, $li, $e1, $e2, ($t1-$t0).TotalSeconds, ((Get-Date)-$t0).TotalSeconds)
    }
    pwsh -NoProfile -File "$main\scripts\unity-slot.ps1" -Release -Owner road-patches-s24 *>> $log
    git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings 2>$null
}
Add-Content $st "$(Get-Date -Format s) $Phase DONE"
