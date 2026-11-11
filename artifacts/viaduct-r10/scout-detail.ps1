$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '../..')
while (!(Select-String artifacts/viaduct-r10/unity-queue.log -Pattern '^after render and EditMode finished$' -Quiet)) { Start-Sleep -Seconds 30 }
while (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') { Start-Sleep -Seconds 30 }
try {
 & pwsh scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting overcast -Gate3 artifacts/viaduct-r10/detail-cameras.json -Cameras 'dk8-east-interior,dk8-east-north,dk8-east-south,dk8-west-interior,dk8-west-north,dk8-west-south' -OutputDir artifacts/viaduct-r10/detail-scout
 if ($LASTEXITCODE -ne 0) { throw 'detail scout failed' }
} finally { git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
