param([ValidateSet('Low','High')][string]$Tier='High',[string]$Phase='round1-runtime')
$ErrorActionPreference='Stop';$taskRoot=$PSScriptRoot;$workRoot=[IO.Path]::GetFullPath((Join-Path $taskRoot '../..'));Set-Location $workRoot
. "$workRoot/scripts/env.ps1"
function Assert-BindingGate {
 if(-not(Test-Path "$taskRoot/ROOT_UNITY_RELEASE.txt")){throw 'Fresh explicitROOTrelease missing'}
 foreach($guard in @('PHONE_RUN','GPT_UNITY_HOLD')){if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$guard"){throw "Unity blocked by $guard"}}
 if(Test-UnityProjectLocked){throw 'OwnUnityalreadyactive'}
}
Assert-BindingGate
$generated=[IO.Path]::GetFullPath((Join-Path $workRoot 'game/Assets/_Generated'));$qa=[IO.Path]::GetFullPath((Join-Path $generated 'FireStationR7BindingQA'))
if(-not $qa.StartsWith($generated+[IO.Path]::DirectorySeparatorChar)){throw 'QApathoutsideownedgeneratedroot'}
if(Test-Path $qa){throw 'InspectexistingQApath'}
if(Test-Path "$taskRoot/$Phase/$Tier-overcast/stats.txt"){throw 'Preservecompletedevidence'}
try {
 New-Item -ItemType Directory -Path (Join-Path $qa 'Editor') -Force | Out-Null
 'E_QA_OWNED' | Set-Content (Join-Path $qa '.e-qa-owned')
 Copy-Item -LiteralPath "$taskRoot/BindingCapture.cs" -Destination (Join-Path $qa 'Editor/BindingCapture.cs')
 Assert-BindingGate
 $code=Invoke-UnityBatch -LogFile "$taskRoot/$Phase-$Tier-binding.log" -Arguments @('-executeMethod','FireStationR7BindingCapture.Run','-eTier',$Tier,'-ePhase',$Phase)
 if($code -ne 0 -or -not(Select-String -Path "$taskRoot/$Phase-$Tier-binding.log" -SimpleMatch 'E_FINAL_BINDING_RESULT: OK' -Quiet)){throw "Finalbindingcapturefailedexit$code"}
}
finally {
 if(Test-Path -LiteralPath $qa){
  $resolved=(Resolve-Path -LiteralPath $qa).Path
  if(-not $resolved.StartsWith($generated+[IO.Path]::DirectorySeparatorChar)){throw 'Cleanupoutsideownedroot'}
  if((Get-Item -LiteralPath $resolved).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Nojunctioncleanup'}
  if(-not(Test-Path (Join-Path $resolved '.e-qa-owned'))){throw 'Ownershipmissing'}
  Remove-Item -LiteralPath $resolved -Recurse -Force
  if(Test-Path ($qa+'.meta')){Remove-Item -LiteralPath ($qa+'.meta') -Force}
 }
}
