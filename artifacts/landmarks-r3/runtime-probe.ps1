param([string]$Phase='before')
$ErrorActionPreference='Stop'
$wt=Split-Path (Split-Path $PSScriptRoot)
Set-Location $wt
$mine='C:\Users\matma\Documents\Claude\kamion\artifacts\locks\unity-slots\gpt-landmarks.slot'
while(Test-Path $mine){Start-Sleep -Seconds 2}
$slot='C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh $slot -Acquire -Owner gpt-landmarks -PollSeconds 10 -StaleHours 876000
if($LASTEXITCODE -ne 0){throw 'Runtime probe slot failed'}
$temporary=Join-Path $wt 'game/Assets/_Project/Editor/VisualQA/LandmarksRuntimeProbe.cs'
if(Test-Path $temporary){throw 'Probe path already exists; refusing overwrite'}
$copied=$false
try {
    Copy-Item "$PSScriptRoot/LandmarksRuntimeProbe.cs" $temporary
    $copied=$true
    . "$wt/scripts/env.ps1"
    $log="$PSScriptRoot/runtime-probe-$Phase.log"
    $scene='Assets/_Generated/World/bialystok-industrial-c/WorldC.unity'
    if(-not(Test-Path "game/$scene")){throw "Scene missing: $scene"}
    $result=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.LandmarksRuntimeProbe.Run',
        '-landmarksScene',$scene,'-landmarksOutput',"$PSScriptRoot/runtime-probe-$Phase.json")
    if($result -ne 0){throw "Runtime probe failed: $result"}
    if(-not(Test-Path "$PSScriptRoot/runtime-probe-$Phase.json")){throw 'Probe result missing'}
} finally {
    if($copied){
        Remove-Item -LiteralPath $temporary -Force
        if(Test-Path "$temporary.meta"){Remove-Item -LiteralPath "$temporary.meta" -Force}
    }
    & pwsh $slot -Release -Owner gpt-landmarks
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
