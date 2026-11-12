# ADR 0146: imports the rebuilt region into Unity under a Unity slot (PHONE_RUN honoured by unity-slot.ps1 -Acquire).
param([string]$Log = 'import-1.log')
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh -NoProfile -File $slot -Acquire -Owner claude-putry-andersa -PollSeconds 20
try {
    Push-Location $root
    & pwsh -NoProfile -File scripts/import-region.ps1 -Region bialystok-industrial-c *> (Join-Path $root "artifacts\putry-andersa\logs\$Log")
    "import exit=$LASTEXITCODE" | Tee-Object (Join-Path $root "artifacts\putry-andersa\logs\$Log.done")
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-putry-andersa
    Pop-Location
}
