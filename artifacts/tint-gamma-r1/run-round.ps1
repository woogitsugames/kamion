param([string]$Round = 'before')
$ErrorActionPreference = 'Stop'
if (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') { throw 'PHONE_RUN present; Unity not started' }
. "$PSScriptRoot/../../scripts/env.ps1"
$tintLog = Join-Path $LogsDir "tint-round-$Round.log"
$tintCode = Invoke-UnityBatch -LogFile $tintLog -Arguments @('-executeMethod','Game.Editor.VisualQA.WorldPbrTintRound.RunBatch','-tintRound',$Round,'-qaGate3',(Join-Path $RepoRoot 'Data/Regions/bialystok-industrial-c/buildings_r10_cameras.json'))
Show-UnityLogErrors $tintLog
Write-Output "TINT_ROUND_EXIT=$tintCode"
if ($tintCode -ne 0) { exit 1 }
if (-not (Select-String -Path $tintLog -Pattern "TINT_ROUND_RESULT: OK $Round" -Quiet)) { throw 'Missing final render evidence' }
