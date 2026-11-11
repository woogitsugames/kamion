# ADR0101 render round: Low (WorldC) / High (WorldC_High) x overcast / clear in one Unity process.
# Usage: pwsh artifacts/tint-r2/run-round.ps1 -Round baseline [-Cameras 'a,b,c']
param([string]$Round = 'baseline', [string]$Cameras = '')
$ErrorActionPreference = 'Stop'
while ((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')) { Write-Output 'PHONE_RUN present; waiting 60 s'; Start-Sleep 60 }
. "$PSScriptRoot/../../scripts/env.ps1"
$log = Join-Path $LogsDir "tint-r2-round-$Round.log"
$a = @('-executeMethod','Game.Editor.VisualQA.WorldPbrTintRound.RunBatch','-tintRound',$Round,
       '-tintOutDir',(Join-Path $RepoRoot 'artifacts/tint-r2'),
       '-qaGate3',(Join-Path $RepoRoot 'artifacts/tint-r2/cameras_r2.json'))
if ($Cameras) { $a += @('-tintCameras', $Cameras) }
$code = Invoke-UnityBatch -LogFile $log -Arguments $a
Show-UnityLogErrors $log
# Undo known Unity side effects (AGENT-RULES 2)
Push-Location $RepoRoot
git checkout -- game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat game/ProjectSettings/QualitySettings.asset game/ProjectSettings/ProjectSettings.asset 2>$null
if (Test-Path game/Assets/Resources) { if (-not (Get-ChildItem game/Assets/Resources -Recurse -File)) { Remove-Item game/Assets/Resources -Recurse -Force; Remove-Item game/Assets/Resources.meta -ErrorAction SilentlyContinue } }
Pop-Location
Write-Output "TINT_ROUND_EXIT=$code"
if (-not (Select-String -Path $log -Pattern "TINT_ROUND_RESULT: OK $Round" -Quiet)) { throw "Missing render evidence ($log)" }
