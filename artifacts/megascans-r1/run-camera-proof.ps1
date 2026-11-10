param([ValidateSet('before','after')][string]$Stage='after')
$ErrorActionPreference='Stop'
. "$PSScriptRoot/../../scripts/env.ps1"
if (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') {throw 'PHONE_RUN active; wait before Unity'}
$probeUnityArgs=@('-executeMethod','Game.World.Import.MegascansQaProbe.ValidateDetailCameras','-qaGate3',(Join-Path $RepoRoot 'artifacts/megascans-r1/detail-cameras.json'),'-qaProof',(Join-Path $RepoRoot "artifacts/megascans-r1/detail-$Stage/ground-proof.csv"))
$probeExit=Invoke-UnityBatch -LogFile (Join-Path $RepoRoot "artifacts/megascans-r1/detail-$Stage-ground.log") -Arguments $probeUnityArgs -NoGraphics
exit $probeExit
