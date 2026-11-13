$ErrorActionPreference = 'Continue'
$wt = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\truck-regs-0175'
$main = 'C:\Users\matma\Documents\Claude\kamion'
$out = Join-Path $wt 'artifacts\truck-regs-0175'
$st = Join-Path $out 'unity_s18.status'
Set-Location $wt
. (Join-Path $wt 'scripts\env.ps1')
function Step($name, [scriptblock]$body) {
    while (Test-Path (Join-Path $main 'artifacts\locks\PHONE_RUN')) { "WAIT PHONE_RUN $(Get-Date -Format s)" | Out-File $st -Append; Start-Sleep 60 }
    "START $name $(Get-Date -Format s)" | Out-File $st -Append
    pwsh (Join-Path $main 'scripts\unity-slot.ps1') -Acquire -Owner truck-regs-0175 | Out-Null
    try { & $body *>> (Join-Path $out "unity_s18_$name.log"); "END $name exit=$LASTEXITCODE $(Get-Date -Format s)" | Out-File $st -Append }
    finally { pwsh (Join-Path $main 'scripts\unity-slot.ps1') -Release -Owner truck-regs-0175 | Out-Null }
}
foreach ($m in @(@('truck', 'Game.Editor.Setup.TruckAssetBuilder.BuildBatch'), @('trailer', 'Game.Editor.Setup.TrailerAssetBuilder.BuildBatch'))) {
    Step "build_$($m[0])" {
        $log = Join-Path $out "unitylog_s18_build_$($m[0]).log"
        $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod', $m[1])
        Select-String -Path $log -Pattern '_RESULT:.*' | Select-Object -Last 2 | ForEach-Object { $_.Line }
        $global:LASTEXITCODE = $code
    }
}
$cams = 'trailer-34,chase,truck-rear34'
foreach ($cfg in @(@('Low', 'overcast'), @('High', 'overcast'), @('High', 'dusk'))) {
    $dir = Join-Path $out "unity\S18-WorldC-$($cfg[0])-$($cfg[1])"
    Step "world_$($cfg[0])_$($cfg[1])" { pwsh (Join-Path $wt 'scripts\visual-qa.ps1') -Scene WorldC -Tier $cfg[0] -Lighting $cfg[1] -Cameras $cams -OutputDir $dir -TruckLamps $(if ($cfg[1] -eq 'dusk') { 'low' } else { '' }) }
}
Step 'editmode' { pwsh (Join-Path $wt 'scripts\test.ps1') -Platform EditMode }
git -C $wt checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings 2>&1 | Out-File $st -Append
"DONE $(Get-Date -Format s)" | Out-File $st -Append
