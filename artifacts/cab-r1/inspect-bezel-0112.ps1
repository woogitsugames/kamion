param([string]$Tier='High',[string]$Lighting='clear')
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
. ./scripts/env.ps1
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slot -Acquire -Owner gpt-cab -PollSeconds 5 -StaleHours 1000000
if ($LASTEXITCODE -ne 0) { throw 'Brak slotu Unity.' }
try {
    $code=Invoke-UnityBatch -LogFile "$PWD/artifacts/cab-r1/bezel-inspection-$Tier-$Lighting.log" -Arguments @('-executeMethod','Game.Editor.VisualQA.CabBezelInspection.Run','-cabTier',$Tier,'-cabLighting',$Lighting,'-cabOutput',"$PWD/artifacts/cab-r1/bezel-inspection/$Tier-$Lighting")
}
finally { pwsh $slot -Release -Owner gpt-cab; git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
exit $code
