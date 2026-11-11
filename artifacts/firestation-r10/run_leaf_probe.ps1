$ErrorActionPreference='Stop'
$taskRoot=$PSScriptRoot;$workRoot=[IO.Path]::GetFullPath((Join-Path $taskRoot '../..'));Set-Location $workRoot
. "$workRoot/scripts/env.ps1"
function Assert-LeafGate {
 if(-not(Test-Path "$taskRoot/ROOT_UNITY_RELEASE.txt")){throw 'Fresh explicitROOTrelease missing'}
 foreach($guard in @('PHONE_RUN','GPT_UNITY_HOLD')){if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$guard"){throw "Unity blocked by $guard"}}
 if(Test-UnityProjectLocked){throw 'Own Unity already active'}
 if(-not(Test-Path "$taskRoot/GLASS2_ROOT_ACCEPTED.txt")){throw 'Glass2actual4ROOTgate must finish BEFORE shader experiment'}
}
Assert-LeafGate
$generatedRoot=[IO.Path]::GetFullPath((Join-Path $workRoot 'game/Assets/_Generated'))
$qaDir=[IO.Path]::GetFullPath((Join-Path $generatedRoot 'FireStationR7LeafQA'))
$mat=[IO.Path]::GetFullPath((Join-Path $generatedRoot 'World/bialystok-industrial-c/Materials/M_fire_station_thuja_shell.mat'))
foreach($p in @($qaDir,$mat)){if(-not $p.StartsWith($generatedRoot+[IO.Path]::DirectorySeparatorChar)){throw 'Path escapes owned generated root'}}
if(Test-Path $qaDir){throw 'Inspect existing QA folder before reuse'}
if(Test-Path "$taskRoot/leaf-probe/High-overcast/stats.txt"){throw 'Preserve completed evidence; ONE experiment only'}
$original=[IO.File]::ReadAllBytes($mat);$originalMeta=[IO.File]::ReadAllBytes($mat+'.meta');$hash=(Get-FileHash -LiteralPath $mat -Algorithm SHA256).Hash
[IO.File]::WriteAllBytes("$taskRoot/leaf-probe-original.mat",$original)
try {
 New-Item -ItemType Directory -Path (Join-Path $qaDir 'Editor') -Force | Out-Null
 'E_QA_OWNED' | Set-Content -LiteralPath (Join-Path $qaDir '.e-qa-owned')
 Copy-Item -LiteralPath "$taskRoot/LeafProbe.cs" -Destination (Join-Path $qaDir 'Editor/LeafProbe.cs')
 Assert-LeafGate
 $code=Invoke-UnityBatch -LogFile "$taskRoot/leaf-probe.log" -Arguments @('-executeMethod','FireStationR7LeafProbe.Run')
 if($code -ne 0 -or -not(Select-String -Path "$taskRoot/leaf-probe.log" -SimpleMatch 'E_LEAF_PROBE_RESULT: OK' -Quiet)){throw "LeafQA failed exit$code"}
}
finally {
 # Exact byte restore even after C# exception, process crash or importer reserialization.
 if((Get-Item -LiteralPath $mat).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Refusing material junction restore'}
 [IO.File]::WriteAllBytes($mat,$original);[IO.File]::WriteAllBytes($mat+'.meta',$originalMeta)
 if((Get-FileHash -LiteralPath $mat -Algorithm SHA256).Hash -ne $hash){throw 'Original material exact restore failed'}
 "Restored exact SHA256=$hash; Low/world/source products unchanged by QA" | Set-Content "$taskRoot/leaf-probe-restore.txt"
 if(Test-Path -LiteralPath $qaDir){
  $resolved=(Resolve-Path -LiteralPath $qaDir).Path
  if(-not $resolved.StartsWith($generatedRoot+[IO.Path]::DirectorySeparatorChar)){throw 'Cleanup outside owned root'}
  if((Get-Item -LiteralPath $resolved).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'QA junction cleanup refused'}
  if(-not(Test-Path (Join-Path $resolved '.e-qa-owned'))){throw 'Ownership marker missing'}
  Remove-Item -LiteralPath $resolved -Recurse -Force
  if(Test-Path ($qaDir+'.meta')){Remove-Item -LiteralPath ($qaDir+'.meta') -Force}
 }
}
