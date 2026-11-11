$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
foreach($method in @('Game.Rendering.Editor.LookDevAssets.EnsureAll','Game.Editor.Setup.ProjectSetup.ApplyRenderingBatch')) {
 if(Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN'){throw 'Main PHONE_RUN lock'}
 $log="artifacts/light-r12/bake-$($method.Split('.')[-1]).log"
 $code=Invoke-UnityBatch -LogFile ([IO.Path]::GetFullPath($log)) -Arguments @('-executeMethod',$method)
 if($code-ne0){throw "Failed $method exit$code"}
 if(Select-String -Path $log -Pattern 'error CS\d+|Shader error|SETUP_RESULT: FAILED' -Quiet){throw "Error in $log"}
 git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting/M_Sky.mat
}
