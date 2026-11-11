param(
 [Parameter(Mandatory=$true)][ValidateSet('Fixtures','PrepareImport','Import','Capture')][string]$Phase,
 [Parameter(Mandatory=$true)][string]$RootRelease,
 [string]$Cameras='',
 [string]$ContentProof=''
)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Assert-Slot {
 if([string]::IsNullOrWhiteSpace($RootRelease)){throw 'An explicit current ROOT release is required'}
 $invalid='artifacts/car-paint-r1/r4-release-invalidated.json'
 if(Test-Path $invalid) {
  $record=Get-Content $invalid -Raw | ConvertFrom-Json
  if($record.root_release-eq$RootRelease){throw 'This ROOT release was invalidated; marker disappearance is not permission to resume'}
 }
 foreach($name in @('PHONE_RUN','GPT_UNITY_HOLD')) {
  if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$name"){
   @{root_release=$RootRelease;markers=@($name)} | ConvertTo-Json | Set-Content $invalid -Encoding utf8
   throw "$name active; ROOT release invalidated. No wait or automatic queued launch."
  }
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
if($Phase-eq'PrepareImport') {
 # Execute only the canonical CPU preparation prefix. It has NO Unity call,
 # so a long PBR regeneration cannot turn into an unguarded automatic launch.
 $sourcePath=[IO.Path]::GetFullPath('scripts/import-region.ps1')
 $text=[IO.File]::ReadAllText($sourcePath)
 $anchor='$log = Join-Path $LogsDir "import-region-$Region-$(Get-Timestamp).log"'
 $cut=$text.IndexOf($anchor)
 if($cut-lt0){throw 'Canonical import CPU/Unity boundary changed'}
 $cpu=$text.Substring(0,$cut).Replace('. "$PSScriptRoot/env.ps1"',(". '"+[IO.Path]::GetFullPath('scripts/env.ps1')+"'"))
 if($ContentProof) {
  & uv run --project tools/worldgen python artifacts/car-paint-r1/r4-pbr-content-proof.py --check $ContentProof
  if($LASTEXITCODE-ne0){throw 'Private R4 targeted content proof failed'}
  $needle='if ($missing -gt 0 -or $stale -gt 0) {'
  if($cpu.IndexOf($needle)-lt0){throw 'Canonical stale conditional changed'}
  $replacement=@'
if ($missing -ne 0) { throw 'Missing PBR files: private content exception refused' }
Write-Output 'PRIVATE R4 EXCEPTION: all baseline PNGs/other source AST exact; targeted clean variant validated. This is not a full post-R4 PBR regeneration.'
$stale = 0
if ($missing -gt 0 -or $stale -gt 0) {
'@
  $cpu=$cpu.Replace($needle,$replacement)
 }
 $cpu+="`nWrite-Output 'R4_IMPORT_CPU_READY'`nexit 0`n"
 $copy=[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-import-cpu-only.ps1')
 [IO.File]::WriteAllText($copy,$cpu,[Text.UTF8Encoding]::new($false))
 if($cpu-match 'Invoke-UnityBatch'){throw 'CPU copy unexpectedly contains a Unity launcher'}
 $stop=[IO.Path]::GetFullPath("artifacts/car-paint-r1/r4-watch-stop-$PID.txt")
 $watch=Start-Process -FilePath (Get-Command python).Source -ArgumentList @([IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-release-monitor.py'),$stop,$RootRelease) -WindowStyle Hidden -PassThru
 try {
  & pwsh -NoProfile -ExecutionPolicy Bypass -File $copy -Region bialystok-industrial-c
  if($LASTEXITCODE-ne0){throw 'R4 CPU preparation failed'}
 } finally {
  [IO.File]::WriteAllText($stop,'stop')
  $null=$watch.WaitForExit(2000)
 }
 [IO.File]::WriteAllText([IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-import-cpu-ready.txt'),(Get-FileHash $sourcePath).Hash,[Text.UTF8Encoding]::new($false))
 $readyRecord=@{canonicalImportSha=(Get-FileHash $sourcePath).Hash;shaderSha=(Get-FileHash 'game/Assets/_Project/Environment/Shaders/WorldPBR.shader').Hash;specSha=(Get-FileHash 'art-source/world/materials/materials_spec.json').Hash;contentProof=$ContentProof;contentProofSha=''}
 if($ContentProof){$readyRecord.contentProofSha=(Get-FileHash $ContentProof).Hash}
 $readyRecord | ConvertTo-Json | Set-Content artifacts/car-paint-r1/r4-import-cpu-ready.json -Encoding utf8
 Write-Output 'CPU only complete. STOPPED: launch Import separately after a fresh release/guard check.'
}
if($Phase-eq'Import') {
 $ready='artifacts/car-paint-r1/r4-import-cpu-ready.txt'
 if(-not(Test-Path $ready)){throw 'Run PrepareImport first; CPU and Unity are deliberately separate commands'}
 if([IO.File]::ReadAllText([IO.Path]::GetFullPath($ready))-ne(Get-FileHash scripts/import-region.ps1).Hash){throw 'Canonical import source changed after CPU preparation'}
 $record=Get-Content artifacts/car-paint-r1/r4-import-cpu-ready.json -Raw | ConvertFrom-Json
 if($record.shaderSha-ne(Get-FileHash 'game/Assets/_Project/Environment/Shaders/WorldPBR.shader').Hash -or $record.specSha-ne(Get-FileHash 'art-source/world/materials/materials_spec.json').Hash){throw 'Ready shader/spec content drift'}
 if($record.contentProof) {
  if($record.contentProofSha-ne(Get-FileHash $record.contentProof).Hash){throw 'Ready content proof file changed'}
  & uv run --project tools/worldgen python artifacts/car-paint-r1/r4-pbr-content-proof.py --check $record.contentProof
  if($LASTEXITCODE-ne0){throw 'Content drift after CPU ready record'}
 }
 Assert-Slot
 # Install only our artifact observer into ignored editor output; no production QA source edits.
 $observer='game/Assets/_Generated/Editor/R4PosePacket.cs'
 New-Item -ItemType Directory -Force (Split-Path $observer) | Out-Null
 Copy-Item -LiteralPath artifacts/car-paint-r1/R4PosePacket.cs -Destination $observer
 try {
  $log=[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-final-normal-import.log')
  Assert-Slot # Immediately adjacent to the actual launch, after all CPU work.
  $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.World.Import.RegionImporter.ImportBatch','-region','bialystok-industrial-c','-tiers','Low,High','-materialTier','Medium')
  $ok=Select-String -Path $log -Pattern 'IMPORT_RESULT: OK' -Quiet
  if($code-ne0 -or -not$ok){throw "R4 final normal import failed exit=$code; inspect log"}
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
