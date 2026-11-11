param(
    [ValidateSet('Import','Capture','EditMode')] [string]$Step = 'Capture',
    [string]$Phase = 'before',
    [string]$Cameras = 'fire-station-ref7197,fire-station-route,fire-station-abeam,fire-station-above'
)
$ErrorActionPreference = 'Stop'
$wt = Split-Path (Split-Path $PSScriptRoot)
Set-Location $wt
function Run-Guarded([string]$Script, [hashtable]$Params) {
    & pwsh scripts/unity-slot.ps1 -Acquire -Owner gpt-landmarks -PollSeconds 10
    if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
    try {
        & pwsh $Script @Params
        if ($LASTEXITCODE -ne 0) { throw "$Script failed ($LASTEXITCODE)" }
    } finally {
        & pwsh scripts/unity-slot.ps1 -Release -Owner gpt-landmarks
        & git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
}
switch ($Step) {
    'Import' { Run-Guarded 'scripts/import-region.ps1' @{Region='bialystok-industrial-c'} }
    'EditMode' { Run-Guarded 'scripts/test.ps1' @{Platform='EditMode'} }
    'Capture' {
        foreach ($tier in @('Low','High')) {
            foreach ($light in @('overcast','clear')) {
                $scene = if ($tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
                $params = @{Scene=$scene; Tier=$tier; Lighting=$light; OutputDir="artifacts/landmarks-r1/$Phase/$tier-$light"}
                if ($Cameras -and $Cameras -ne 'all') { $params.Cameras = $Cameras }
                Run-Guarded 'scripts/visual-qa.ps1' $params
            }
        }
    }
}
