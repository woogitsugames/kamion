$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
if((Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') -or (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/GPT_UNITY_HOLD')){throw 'Shared Unity guard active; explicit new ROOT release also required'}
New-Item -ItemType Directory -Force game/Assets/_Generated/CarFilmGpuProbe/Editor | Out-Null
Copy-Item artifacts/car-paint-r1/CarFilmGpuProbe.cs game/Assets/_Generated/CarFilmGpuProbe/Editor/CarFilmGpuProbe.cs
$log=[IO.Path]::GetFullPath('artifacts/car-paint-r1/instanced-film-gpu.log')
$started=Get-Date
$code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.CarFilmGpuProbe.RunBatch')
git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting
$result=Select-String -Path $log -SimpleMatch 'G_FILM_GPU_RESULT: OK' -Quiet
$proof='artifacts/car-paint-r1/instanced-film-gpu-proof.json'
if($code-ne0 -or -not$result -or -not(Test-Path $proof) -or (Get-Item $proof).LastWriteTime-lt$started){throw "Actual instancing proof failed exit=$code"}
$data=Get-Content $proof -Raw | ConvertFrom-Json
if($data.cases.Count-ne18 -or @($data.cases | Where-Object {-not$_.pass}).Count-ne0){throw 'LOD/rebase proof incomplete'}
if(($data.gpuCounts | Measure-Object -Sum).Sum-ne$data.instanceCount){throw 'Actual coverage count mismatch'}
