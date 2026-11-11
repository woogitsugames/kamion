param([Parameter(Mandatory=$true)][string]$RootRelease)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
function Assert-Slot {
 if(Test-Path artifacts/car-paint-r1/r4-release-invalidated.json){$r=Get-Content artifacts/car-paint-r1/r4-release-invalidated.json -Raw|ConvertFrom-Json;if($r.root_release-eq$RootRelease){throw 'Release permanently invalidated; fresh ROOT release required'}}
 foreach($name in @('PHONE_RUN','GPT_UNITY_HOLD')){if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$name"){throw "$name active; no Unity launch"}}
}
Assert-Slot
foreach($name in @('R4CarFilmGpuProbe.cs','R4CarOpacityProbe.cs')){Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination (Join-Path 'game/Assets/_Generated/Editor' $name)}
$runner=@'
namespace Game.Editor.VisualQA { public static class R4ProbeRunner { public static void RunBatch() { R4CarFilmGpuProbe.RunBatch(); R4CarOpacityProbe.RunBatch(); } } }
'@
[IO.File]::WriteAllText([IO.Path]::GetFullPath('game/Assets/_Generated/Editor/R4ProbeRunner.cs'),$runner,[Text.UTF8Encoding]::new($false))
try {
 Assert-Slot
 $log=[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-gpu.log')
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.R4ProbeRunner.RunBatch')
 if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'R4_OPACITY_GPU_RESULT: OK' -Quiet)){throw "R4 GPU proof failed exit=$code; inspect log"}
} finally {git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting}
