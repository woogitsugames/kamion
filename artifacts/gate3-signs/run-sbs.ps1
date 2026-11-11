# Renders the SBS photo-pose cameras (Low overcast by default) under a Unity slot and moves the result to artifacts/gate3-signs/<Name>.
param([string]$Name = 'baseline', [string[]]$Tiers = @('Low'), [string[]]$Lighting = @('overcast'))
$ErrorActionPreference = 'Stop'
$Tiers = @($Tiers | ForEach-Object { $_ -split ',' }); $Lighting = @($Lighting | ForEach-Object { $_ -split ',' })   # pwsh -File passes 'a,b' as one string
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$slot = 'C:\Users\matma\Documents\Claude\kamion\scripts\unity-slot.ps1'
& pwsh -NoProfile -File $slot -Acquire -Owner claude-gate3-signs
try {
    Push-Location $root
    & pwsh -NoProfile -File scripts/sbs-gate3.ps1 -Tiers $Tiers -Lighting $Lighting
    $code = $LASTEXITCODE
} finally {
    & git -C $root checkout -- game/Assets/_Project/Rendering/Settings game/ProjectSettings
    & pwsh -NoProfile -File $slot -Release -Owner claude-gate3-signs
    Pop-Location
}
$dst = Join-Path $root "artifacts\gate3-signs\$Name"
if (Test-Path (Join-Path $root 'artifacts\sbs-gate3\renders')) {
    New-Item -ItemType Directory -Force $dst | Out-Null
    robocopy (Join-Path $root 'artifacts\sbs-gate3') $dst /E /NFL /NDL /NJH /NJS /NP | Out-Null
}
"sbs exit=$code -> $dst"
