param([string[]]$Tiles)
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\regen-wave-2-s24'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$out = Join-Path $wt 'artifacts\regen-wave-2-s24'
$st = Join-Path $out 'vqa.status'
Set-Location $wt
foreach ($t in $Tiles) {
    while (Test-Path (Join-Path $main 'artifacts\locks\PHONE_RUN')) { Start-Sleep 60 }
    $log = Join-Path $out "logs\vqa-$t.log"
    pwsh -NoProfile -File (Join-Path $main 'scripts\unity-slot.ps1') -Acquire -Owner regen-wave-2-s24-vqa *>> $log
    pwsh -NoProfile -File scripts/import-region.ps1 -Region $t -BuildTarget Win64 *>> $log
    $e1 = $LASTEXITCODE
    pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene "World_${t}_High" -Tier High -Pc -Width 1920 -Height 1080 -Lighting clear -BuildTarget Win64 -OutputDir "artifacts/regen-wave-2-s24/vqa/$t/High-clear" *>> $log
    $e2 = $LASTEXITCODE
    pwsh -NoProfile -File (Join-Path $main 'scripts\unity-slot.ps1') -Release -Owner regen-wave-2-s24-vqa *>> $log
    git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset game/ProjectSettings/EditorBuildSettings.asset 2>$null
    Add-Content $st "$(Get-Date -Format s) tile=$t import_exit=$e1 vqa_exit=$e2"
}
Add-Content $st "$(Get-Date -Format s) DONE"

