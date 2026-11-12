$ErrorActionPreference = 'Stop'
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh $slot -Acquire -Owner gpt-s16
try {
    if (Test-Path 'C:/Users/matma/Documents/Claude/kamion/artifacts/locks/PHONE_RUN') { throw 'PHONE_RUN appeared' }
    . scripts/env.ps1
    $code = Invoke-UnityBatch -LogFile (Join-Path $RepoRoot 'artifacts/gpt-s16-r1/projection-probe.log') -Arguments @('-nographics', '-executeMethod', 'Game.World.Import.VehicleLodAtlasProbe.RunBatch')
    if ($code -ne 0) { throw "Projection probe failed: $code" }
} finally {
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner gpt-s16
}
