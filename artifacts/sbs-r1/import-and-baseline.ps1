$ErrorActionPreference = 'Stop'
pwsh -NoProfile -File scripts/unity-slot.ps1 -Acquire -Owner gpt-sbs
if ($LASTEXITCODE -ne 0) { throw 'Nie uzyskano slotu Unity' }
try {
    pwsh -NoProfile -File scripts/import-region.ps1 -Region bialystok-industrial-c
    if ($LASTEXITCODE -ne 0) { throw 'Import regionu nie powiódł się' }
} finally {
    git restore -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    pwsh -NoProfile -File scripts/unity-slot.ps1 -Release -Owner gpt-sbs
}
pwsh -NoProfile -File scripts/sbs-gate3.ps1 -EditMode -Tiers Low -Lighting overcast -OutputRoot artifacts/sbs-r1/baseline-current
if ($LASTEXITCODE -ne 0) { throw 'Testy lub baseline SBS nie powiodły się' }
