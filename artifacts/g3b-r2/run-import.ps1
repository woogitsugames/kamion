# Imports the rebuilt region into Unity under a Unity slot (PHONE_RUN is honoured by unity-slot.ps1 -Acquire).
param([string]$Log = 'import-1.log')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh -NoProfile -File $slot -Acquire -Owner claude-g3b-r2
try {
    Push-Location $root
    & pwsh -NoProfile -File scripts/import-region.ps1 -Region bialystok-industrial-c *> (Join-Path $PSScriptRoot $Log)
    "import exit=$LASTEXITCODE"
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-g3b-r2
    Pop-Location
}
