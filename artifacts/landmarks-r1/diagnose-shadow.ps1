param([ValidateSet('direct','gi','ssao')][string]$Mode = 'direct')
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path (Split-Path $PSScriptRoot))
$rq = switch ($Mode) { 'direct' { 'rq_shadow=0,rq_worldsun=0' }; 'gi' { 'rq_worldgi=0' }; 'ssao' { 'rq_ssao=0' } }
$out = switch ($Mode) { 'direct' { 'diagnostic-direct-shadow-off' }; 'gi' { 'diagnostic-gi-off' }; 'ssao' { 'diagnostic-ssao-off' } }
& pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-landmarks -PollSeconds 10 -StaleHours 876000
if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
try {
    & pwsh scripts/visual-qa.ps1 -Scene WorldC_High -Tier High -Lighting overcast -Cameras fire-station-ref7197 `
        -Rq $rq -OutputDir "artifacts/landmarks-r1/$out"
    if ($LASTEXITCODE -ne 0) { throw 'Shadow diagnostic failed' }
} finally {
    & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-landmarks
    & git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
}
