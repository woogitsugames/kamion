param(
    [ValidateSet('Import','Capture','EditMode')] [string]$Step = 'Capture',
    [string]$Phase = 'before',
    [string]$Cameras = 'all',
    [string]$Gate3 = 'artifacts/landmarks-r4/cameras.json'
)
$ErrorActionPreference = 'Stop'
$wt = Split-Path (Split-Path $PSScriptRoot)
$roundRelative = 'artifacts/'+(Split-Path $PSScriptRoot -Leaf)
Set-Location $wt
function Run-Guarded([string]$Script, [hashtable]$Params) {
    # This session's baseline diagnostics use the same project. Finish those
    # before the build pipeline imports or captures the changed hero.
    while (Test-Path "$PSScriptRoot/DIAGNOSTICS_RUNNING") { Start-Sleep -Seconds 5 }
    # Never let this session's acquisition clean up somebody else's aged slot.
    & pwsh C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1 -Acquire -Owner gpt-landmarks -PollSeconds 10 -StaleHours 876000
    if ($LASTEXITCODE -ne 0) { throw 'Unity slot acquisition failed' }
    try {
        & pwsh $Script @Params
        if ($LASTEXITCODE -ne 0) { throw "$Script failed ($LASTEXITCODE)" }
    } finally {
        & pwsh C:/Users/matma/Documents/Claude/kamion/scripts/unity-slot.ps1 -Release -Owner gpt-landmarks
        & git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    }
}
switch ($Step) {
    'Import' { Run-Guarded "$roundRelative/import-prepared.ps1" @{} }
    'EditMode' { Run-Guarded 'scripts/test.ps1' @{Platform='EditMode'} }
    'Capture' {
        foreach ($tier in @('Low','High')) {
            foreach ($light in @('overcast','clear')) {
                $scene = if ($tier -eq 'High') { 'WorldC_High' } else { 'WorldC' }
                $params = @{Scene=$scene; Tier=$tier; Lighting=$light; OutputDir="$roundRelative/$Phase/$tier-$light"}
                if ($Cameras -and $Cameras -ne 'all') { $params.Cameras = $Cameras }
                if ($Gate3) { $params.Gate3 = $Gate3 }
                Run-Guarded 'scripts/visual-qa.ps1' $params
            }
        }
    }
}


