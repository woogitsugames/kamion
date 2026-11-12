$ErrorActionPreference='Stop'
Set-Location (Resolve-Path "$PSScriptRoot/../..")
if ((git branch --show-current) -ne 'gpt-cab-r3') { throw 'Tylko runda cab r3.' }
. ./scripts/env.ps1
$slot='C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1'
$log="$PWD/artifacts/cab-r3/occlusion-preflight.log"
pwsh $slot -Acquire -Owner gpt-cab -PollSeconds 5 -StaleHours 1000000
if ($LASTEXITCODE -ne 0) { throw 'Brak slotu Unity.' }
try { $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.CabMirrorOcclusionAudit.Run','-cabOutput',"$PWD/artifacts/cab-r3/occlusion-preflight") }
finally { pwsh $slot -Release -Owner gpt-cab; git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
if ($code -ne 0 -or -not (Select-String -LiteralPath $log -Pattern 'CAB_MIRROR_OCCLUSION_RESULT: OK' -SimpleMatch -Quiet)) { Show-UnityLogErrors $log; throw "Nieudany audyt okluzji, exit $code" }
