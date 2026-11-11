param([Parameter(Mandatory=$true)][string]$RootRelease)
$ErrorActionPreference='Stop'
Set-Location ([IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..')))
. scripts/env.ps1
$invalid='artifacts/car-paint-r1/r4-release-invalidated.json'
if(Test-Path $invalid){$r=Get-Content $invalid -Raw|ConvertFrom-Json;if($r.root_release-eq$RootRelease){throw 'Release invalidated'}}
Copy-Item artifacts/car-paint-r1/R4TextureInventory.cs game/Assets/_Generated/Editor/R4TextureInventory.cs
try {
 foreach($name in @('PHONE_RUN','GPT_UNITY_HOLD')){if(Test-Path "C:/Users/matma/Documents/Claude/kamion/artifacts/locks/$name"){@{root_release=$RootRelease;marker=$name}|ConvertTo-Json|Set-Content $invalid -Encoding utf8;throw "$name active"}}
 $log=[IO.Path]::GetFullPath('artifacts/car-paint-r1/r4-texture-inventory.log')
 $code=Invoke-UnityBatch -LogFile $log -Arguments @('-executeMethod','Game.Editor.VisualQA.R4TextureInventory.RunBatch')
 if($code-ne0 -or -not(Select-String -Path $log -SimpleMatch 'R4_TEXTURE_INVENTORY_RESULT: OK' -Quiet)){throw "Texture inventory failed exit=$code"}
} finally {git restore -- game/ProjectSettings game/Assets/_Project/Rendering/Settings/Lighting}
