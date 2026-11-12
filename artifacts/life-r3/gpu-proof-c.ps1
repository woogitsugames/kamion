$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
if((git branch --show-current).Trim() -ne 'gpt-life-r3'){throw 'Wrong branch'}
$inputs=Get-Content artifacts/life-r3/after-c-inputs.json -Raw|ConvertFrom-Json
foreach($entry in $inputs.source_sha.PSObject.Properties) {
 if((Get-FileHash $entry.Name).Hash -ne $entry.Value){throw "Source drift: $($entry.Name)"}
}
if((Get-FileHash art-source/world/props/street_props.glb).Hash -ne $inputs.library_sha){throw 'Library drift'}
if(Test-Path artifacts/life-r3/gpu-c){throw 'GPU evidence exists'}
if(Test-Path C:/Users/matma/Documents/Claude/kamion/artifacts/locks/unity-slots/gpt-life.slot){throw 'Own Unity already active'}
$plate='game/Assets/_Generated/World/bialystok-industrial-c/Materials/M_car_plate.mat'
$plateHash=(Get-FileHash $plate).Hash
New-Item -ItemType Directory -Force game/Assets/_Generated/Editor | Out-Null
foreach($name in @('Life3CCarFilmGpuProbe.cs','Life3CCarOpacityProbe.cs')) {
 Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path game/Assets/_Generated/Editor $name)
}
@'
namespace Game.Editor.VisualQA {
 public static class Life3CProbeRunner {
  public static void RunBatch() { Life3CCarFilmGpuProbe.RunBatch(); Life3CCarOpacityProbe.RunBatch(); }
 }
}
'@ | Set-Content game/Assets/_Generated/Editor/Life3CProbeRunner.cs
$code=1
& pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner gpt-life -StaleHours 1000000 -PollSeconds 1
if($LASTEXITCODE){throw 'Acquire failed'}
try {
 $log=[IO.Path]::GetFullPath('artifacts/life-r3/gpu-c.log')
 $unityCode=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.Life3CProbeRunner.RunBatch')
 if($unityCode){throw 'GPU probe failed'}
 if(!(Test-Path artifacts/life-r3/gpu-c/opacity-uv-proof.json)){throw 'Opacity evidence missing'}
 $film=Get-Content artifacts/life-r3/gpu-c/instanced-film-gpu-proof.json -Raw|ConvertFrom-Json
 $opacity=Get-Content artifacts/life-r3/gpu-c/opacity-uv-proof.json -Raw|ConvertFrom-Json
 if(@($opacity.cases).Count -ne 81 -or @($film.cases|Where-Object {!$_.pass}).Count){throw 'GPU case coverage failed'}
 if(($film.cpuCounts -join ',') -ne ($film.gpuCounts -join ',')){throw 'GPU distribution mismatch'}
 if((Get-FileHash $plate).Hash -ne $plateHash){throw 'Native plate changed during numeric probe'}
 foreach($entry in $inputs.source_sha.PSObject.Properties) {
  if((Get-FileHash $entry.Name).Hash -ne $entry.Value){throw "Source changed during GPU proof: $($entry.Name)"}
 }
 $code=0
} finally {
 & pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner gpt-life
 git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
 @{exit_code=$code;source_commit=(git rev-parse HEAD);finished=(Get-Date -Format o);plate_sha_before=$plateHash;plate_sha_after=(Get-FileHash $plate).Hash}|ConvertTo-Json|Set-Content artifacts/life-r3/gpu-c-result.json
}
if((Get-FileHash $plate).Hash -ne $plateHash){throw 'Native plate changed during numeric probe'}

