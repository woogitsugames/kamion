param([ValidateSet('Low','High')][string]$Tier='High')
$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
. ./scripts/env.ps1
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
pwsh $slot -Acquire -Owner gpt-cab -PollSeconds 5 -StaleHours 1000000
if ($LASTEXITCODE -ne 0) { throw 'Brak slotu Unity.' }
try {
    $code=Invoke-UnityBatch -LogFile "$PWD/artifacts/cab-r2/ao-mip-audit-$Tier.log" -Arguments @('-executeMethod','Game.Editor.VisualQA.CabAoMipAudit.Run','-cabTier',$Tier,'-cabOutput',"$PWD/artifacts/cab-r2/ao-mip-audit-$Tier")
}
finally { pwsh $slot -Release -Owner gpt-cab; git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
exit $code
