param(
 [Parameter(Mandatory=$true)][ValidateSet('Fixtures','Import','Capture')][string]$Phase,
 [Parameter(Mandatory=$true)][string]$RootRelease,
 [string]$Cameras=''
)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Assert-Slot {
 if([string]::IsNullOrWhiteSpace($RootRelease)){throw 'An explicit current ROOT release is required'}
 foreach($name in @('PHONE_RUN','GPT_UNITY_HOLD')) {
  if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$name"){throw "$name active; ROOT release invalidated. No wait or automatic queued launch."}
 }
}
function Restore-OwnedSideEffects {
 git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting
}
if($Phase-eq'Fixtures') {
 foreach($method in @('Game.Editor.Setup.TruckAssetBuilder.BuildBatch','Game.Editor.Setup.TrailerAssetBuilder.BuildBatch','Game.World.Import.WorldTruckInstaller.InstallBatch')) {
  Assert-Slot
  $tag=$method.Split('.')[-2]
  $log=[IO.Path]::GetFullPath("artifacts/car-paint-r1/r4-baseline-$tag.log")
  try {
   $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod',$method)
   $ok=Select-String -Path $log -Pattern '^(TRUCK|TRAILER)_RESULT: OK' -Quiet
   if($code-eq-1073741819 -and $ok -and (Select-String -Path $log -SimpleMatch 'D3D12PipelineCacheLibrary::SaveCache' -Quiet)) {
    Write-Warning "Known post-completion D3D12 shutdown crash after $tag; successful builder result retained"
    $code=0
   }
   if($code-ne0 -or -not$ok){throw "Fixture failed $tag exit=$code"}
  } finally {Restore-OwnedSideEffects}
 }
 Write-Output 'Fixtures complete. NEXT: r4-baseline.ps1 -Phase Import with a still-valid explicit ROOT release.'
}
if($Phase-eq'Import') {
 Assert-Slot
 # Install only our artifact observer into ignored editor output; no production QA source edits.
 $observer='game/Assets/_Generated/Editor/R4PosePacket.cs'
 New-Item -ItemType Directory -Force (Split-Path $observer) | Out-Null
 Copy-Item -LiteralPath artifacts/car-paint-r1/R4PosePacket.cs -Destination $observer
 try {
  & pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/import-region.ps1 -Region bialystok-industrial-c
  if($LASTEXITCODE-ne0){throw 'R4 final normal import failed'}
 } finally {Restore-OwnedSideEffects}
 & python artifacts/car-paint-r1/proof.py r4-before-imported
 if($LASTEXITCODE-ne0){throw 'R4 imported baseline source proof failed'}
 Write-Output 'Final normal import complete. No more install/rebuild before matched BEFORE.'
}
if($Phase-eq'Capture') {
 if(-not(Test-Path 'artifacts/car-paint-r1/r4-before-imported-source-proof.json')){throw 'Missing final-import proof'}
 if(-not(Test-Path 'game/Assets/_Generated/Editor/R4PosePacket.cs')){throw 'Pose observer missing'}
 $env:KAMION_G_SOURCE_HEAD=(& git rev-parse HEAD).Trim()
 $env:KAMION_G_SOURCE_PROOF_SHA=(Get-FileHash artifacts/car-paint-r1/r4-before-imported-source-proof.json).Hash
 try {
  foreach($tier in @('Low','High')) {
   foreach($light in @('clear','overcast')) {
    Assert-Slot
    $scene=if($tier-eq'High'){'WorldC_High'}else{'WorldC'}
    $out="artifacts/car-paint-r1/r4-before/$tier-$light"
    if(Test-Path $out){throw "Do not overwrite historical capture directory: $out"}
    $env:KAMION_G_POSE_OUTPUT=[IO.Path]::GetFullPath("$out/poses")
    try {
     $capture=@('-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/visual-qa.ps1','-Scene',$scene,'-Tier',$tier,'-Lighting',$light,'-Gate3','artifacts/car-paint-r1/r4-baseline-cameras.json','-OutputDir',$out)
     if($Cameras){$capture+=@('-Cameras',$Cameras)}
     & pwsh @capture
     if($LASTEXITCODE-ne0){throw "R4 BEFORE failed $tier $light"}
    } finally {Restore-OwnedSideEffects}
   }
  }
 } finally {
  Remove-Item Env:KAMION_G_POSE_OUTPUT -ErrorAction SilentlyContinue
  Remove-Item Env:KAMION_G_SOURCE_HEAD -ErrorAction SilentlyContinue
  Remove-Item Env:KAMION_G_SOURCE_PROOF_SHA -ErrorAction SilentlyContinue
 }
}
