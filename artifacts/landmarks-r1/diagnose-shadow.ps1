$ErrorActionPreference = 'Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
& pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-landmarks -PollSeconds 10 -StaleHours 876000
if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
try {
    & pwsh scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Lighting overcast -Cameras fire-station-ref7197 `
        -Rq 'rq_shadow=0,rq_worldsun=0' -OutputDir artifacts/landmarks-r1/diagnostic-direct-shadow-off
    if ($LASTEXITCODE -ne 0) { throw 'Shadow diagnostic failed' }
} finally {
    & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-landmarks
    & git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
