# ADR 0141 after merging main: import-region (both tiers), EditMode, then renders "merged" (run-vqa.ps1). One Unity slot per stage.
$ErrorActionPreference = 'Continue'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh -NoProfile -File $slot -Acquire -Owner claude-edge-r6c
try {
    Push-Location $root
    & pwsh -NoProfile -File scripts/import-region.ps1 -Region bialystok-industrial-c *> (Join-Path $PSScriptRoot 'import-merged.log')
    "import exit=$LASTEXITCODE"; $imp = $LASTEXITCODE
    if ($imp -eq 0) {
        & pwsh -NoProfile -File scripts/test.ps1 -Platform EditMode *> (Join-Path $PSScriptRoot 'editmode-merged.log')
        "editmode exit=$LASTEXITCODE"
    }
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-edge-r6c
    Pop-Location
}
if ($imp -ne 0) { exit 1 }
& pwsh -NoProfile -File (Join-Path $PSScriptRoot 'run-vqa.ps1') -Name merged
