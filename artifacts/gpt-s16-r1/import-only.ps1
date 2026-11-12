param([string]$Label = 'restore-candidate')
$ErrorActionPreference = 'Stop'
$root = 'C:\Users\matma\Documents\Claude\kamion'
$slot = Join-Path $root 'scripts/unity-slot.ps1'
& pwsh $slot -Acquire -Owner gpt-s16
try {
    if (Test-Path "$root/artifacts/locks/PHONE_RUN") { throw 'PHONE_RUN appeared' }
    & pwsh scripts/import-region.ps1 -Region bialystok-industrial-c *> "artifacts/gpt-s16-r1/$Label-import.log"
    if ($LASTEXITCODE -ne 0) { throw "Import failed: $Label" }
} finally {
    git checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh $slot -Release -Owner gpt-s16
}
