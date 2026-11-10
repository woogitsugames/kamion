param([string]$Step = 'render', [string]$Out = 'before',
      [string]$Tiers = 'Low,High', [string]$Lights = 'overcast,lowsun',
      [string]$Scene = 'WorldC',
      [string]$Cameras = 'truck-34,truck-front,trailer-34', [string]$Mask = '', [string]$Rq = '', [string]$RenderScale = '', [string]$Sub = '')
# truck-ext-r10 loop in the agent worktree: build (TruckAssetBuilder + WorldTruckInstaller), render (visual-qa), test (EditMode).
# Every Unity start waits for artifacts/locks/PHONE_RUN of the main checkout to disappear.
$ErrorActionPreference = 'Stop'
$W = 'C:\Users\matma\Documents\Claude\kamion\.claude\worktrees\agent-a4049e15e1ab8c681'
$Lock = 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN'
Set-Location $W
. "$W\scripts\env.ps1"
function Wait-Lock {
    $t0 = Get-Date
    while (Test-Path $Lock) { Start-Sleep -Seconds 20 }
    $w = [int]((Get-Date) - $t0).TotalSeconds
    if ($w -gt 0) { Write-Host "waited $w s for PHONE_RUN" }
}
function Run($method, $tag) {
    Wait-Lock
    $log = Join-Path $LogsDir "truck-ext-r10-$tag-$(Get-Timestamp).log"
    $code = Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod', $method)
    $res = Select-String -Path $log -Pattern '(TRUCK_RESULT|TRUCKASSET_RESULT|_RESULT): .*' | Select-Object -Last 1
    Write-Host "$tag exit $code : $($res.Line)  log $log"
    if ($code -ne 0) { Show-UnityLogErrors $log; throw "$tag failed" }
}
if ($Step -in 'all', 'build') {
    Run 'Game.Editor.Setup.TruckAssetBuilder.BuildBatch' 'truck-build'
    Run 'Game.World.Import.WorldTruckInstaller.InstallBatch' 'truck-install'
}
if ($Step -in 'all', 'render') {
    foreach ($tier in $Tiers.Split(',')) {
        foreach ($light in $Lights.Split(',')) {
            Wait-Lock
            $o = Join-Path $W "artifacts\truck-ext-r10\$Out\$tier-$light"
            if ($Sub) { $o = Join-Path $o $Sub }
            $a = @('-NoProfile', '-File', "$W\scripts\visual-qa.ps1", '-Scene', $Scene, '-Tier', $tier, '-Lighting', $light, '-Cameras', $Cameras, '-OutputDir', $o)
            if ($Mask) { $a += @('-Mask', $Mask) }
            if ($Rq) { $a += @('-Rq', $Rq) }
            if ($RenderScale) { $a += @('-RenderScale', $RenderScale) }
            & pwsh @a | Select-Object -Last 3
            Write-Host "render $tier $light exit $LASTEXITCODE"
        }
    }
}
if ($Step -in 'all', 'test') {
    Wait-Lock
    & pwsh -NoProfile -File "$W\scripts\test.ps1" -Platform EditMode | Select-Object -Last 6
    Write-Host "editmode exit $LASTEXITCODE"
}


git -C $W checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
