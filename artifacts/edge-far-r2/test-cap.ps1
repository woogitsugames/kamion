$ErrorActionPreference = 'Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
. scripts/env.ps1
function Wait-Phone {
    while (Test-Path 'C:\Users\matma\Documents\Claude\kamion\artifacts\locks\PHONE_RUN') { Start-Sleep -Seconds 60 }
}
Wait-Phone
try {
    $code = Invoke-UnityBatch -LogFile "$PSScriptRoot/cap-prototype-rebuild.log" -Arguments @('-executeMethod','Game.World.Import.WorldEdgeBuilder.RebuildEdgeBatch','-region','bialystok-industrial-c')
    if ($code -ne 0) { throw 'Rebuild failed' }
} finally { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
Wait-Phone
try {
    & pwsh -NoProfile -File scripts/visual-qa.ps1 -Scene WorldC -Tier Low -Lighting clear -Cameras edge-pietrasze-skyline -Gate3 "$PSScriptRoot/skyline-cameras.json" -OutputDir "$PSScriptRoot/cap-prototype/Low-clear"
    if ($LASTEXITCODE -ne 0) { throw 'Render failed' }
} finally { git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings }
